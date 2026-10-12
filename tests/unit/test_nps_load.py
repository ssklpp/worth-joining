"""적재 전체 흐름과 docs/decisions/003 규칙 (raw → core)."""

import pytest
from sqlalchemy import text

from pipeline.nps.load import run
from tests.nps_csv import Row, write_nps_csv


def load(engine, tmp_path, ym, rows):
    return run(engine, write_nps_csv(tmp_path / f"{ym}.csv", ym, rows), ym)


def monthly(engine, ym):
    with engine.connect() as conn:
        return {
            r[0]: tuple(r[1:]) for r in conn.execute(text(
                "SELECT w.workplace_name, m.members, m.billed_amount, m.new_members, m.lost_members"
                " FROM workplace_monthly m JOIN workplace w USING (workplace_id)"
                " WHERE m.snapshot_ym = :ym"
            ), {"ym": ym})
        }


def scalar(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def test_run_skips_file_already_loaded(tmp_path, clean_tables):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202608, [Row("가상A")])

    assert run(clean_tables, csv_path, 202608) == "success"
    assert run(clean_tables, csv_path, 202608) == "skipped"
    with clean_tables.connect() as conn:
        statuses = conn.execute(text("SELECT status, row_count FROM ingestion_log ORDER BY run_id"))
        assert [tuple(r) for r in statuses] == [("success", 1), ("skipped", None)]


def test_run_records_failure_and_keeps_nothing(tmp_path, clean_tables):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202607, [Row("가상A")])

    with pytest.raises(ValueError):
        run(clean_tables, csv_path, 202608)
    assert scalar(clean_tables, "SELECT status FROM ingestion_log") == "failed"
    assert scalar(clean_tables, "SELECT COUNT(*) FROM company") == 0


def test_same_month_twice_gives_same_rows(tmp_path, clean_tables):
    rows = [Row("가상A", members=10), Row("가상B", biz_no6="654321", members=5)]
    load(clean_tables, tmp_path, 202608, rows)
    first = monthly(clean_tables, 202608)
    (tmp_path / "202608.csv").unlink()
    # 체크섬이 다르도록 같은 내용을 다른 줄 순서로 다시 넣는다
    load(clean_tables, tmp_path, 202608, list(reversed(rows)))

    assert monthly(clean_tables, 202608) == first
    assert scalar(clean_tables, "SELECT COUNT(*) FROM company") == 2
    assert scalar(clean_tables, "SELECT COUNT(*) FROM workplace") == 2


def test_withdrawn_only_workplace_creates_no_company(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202608,
         [Row("가상A"), Row("탈퇴만", biz_no6="999999", status="2", members=0, lost=3)])

    assert scalar(clean_tables, "SELECT COUNT(*) FROM company") == 1
    assert set(monthly(clean_tables, 202608)) == {"가상A"}


def test_withdrawal_month_keeps_lost_members(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202607, [Row("가상A", members=8)])
    load(clean_tables, tmp_path, 202608,
         [Row("가상A", status="2", members=0, billed=0, lost=8, left_on="2026-08-10")])
    load(clean_tables, tmp_path, 202609, [Row("가상A", status="2", members=0, billed=0)])

    assert monthly(clean_tables, 202608) == {"가상A": (0, 0, 0, 8)}
    assert monthly(clean_tables, 202609) == {}  # 이미 탈퇴한 사업장의 남은 행은 넣지 않는다
    assert str(scalar(clean_tables, "SELECT left_on FROM workplace")) == "2026-08-10"


def test_duplicate_natural_key_is_summed(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202608, [
        Row("가상A", members=10, billed=3_000_000, new=1, joined_on="2020-01-01"),
        Row("가상A", members=4, billed=1_000_000, lost=2, joined_on="2015-05-01"),
    ])

    assert monthly(clean_tables, 202608) == {"가상A": (14, 4_000_000, 1, 2)}
    assert str(scalar(clean_tables, "SELECT joined_on FROM workplace")) == "2015-05-01"


def test_reregistered_workplace_clears_left_on(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202607, [Row("가상A")])
    withdrawn = Row("가상A", status="2", members=0, billed=0, left_on="2026-08-01")
    load(clean_tables, tmp_path, 202608, [withdrawn])
    load(clean_tables, tmp_path, 202609, [Row("가상A")])

    assert scalar(clean_tables, "SELECT left_on FROM workplace") is None
