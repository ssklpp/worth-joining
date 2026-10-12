"""품질 검사 (docs/decisions/003). 실패하면 그 달의 raw · core가 되돌려지고 failed로 남는다."""

import pytest
from sqlalchemy import text

from pipeline.nps.load import run
from pipeline.nps.quality import QualityError
from tests.nps_csv import Row, write_nps_csv


def rows(n, prefix="가상", **kw):
    return [Row(f"{prefix}{i:02d}", biz_no6=f"{100000 + i}", **kw) for i in range(n)]


def load(engine, tmp_path, ym, data):
    return run(engine, write_nps_csv(tmp_path / f"{ym}.csv", ym, data), ym)


def failed_checks(excinfo):
    return {c.name for c in excinfo.value.failed}


def count(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def test_normal_month_passes_even_with_many_withdrawn_zero_rows(tmp_path, clean_tables):
    # 탈퇴 0명 행은 정상이다(13개월 실제 데이터에서 약 4.6%)
    data = rows(20) + rows(5, prefix="탈퇴", status="2", members=0, billed=0)

    assert load(clean_tables, tmp_path, 202608, data) == "success"


def test_active_zero_over_one_percent_fails_and_rolls_back(tmp_path, clean_tables):
    data = rows(98) + rows(2, prefix="영명", members=0, billed=0)  # 등록 행 중 2%

    with pytest.raises(QualityError) as excinfo:
        load(clean_tables, tmp_path, 202608, data)

    assert failed_checks(excinfo) == {"active_zero"}
    assert count(clean_tables, "SELECT COUNT(*) FROM raw_nps_workplace") == 0
    assert count(clean_tables, "SELECT COUNT(*) FROM company") == 0
    assert count(clean_tables, "SELECT status FROM ingestion_log") == "failed"
    assert "active_zero" in count(clean_tables, "SELECT message FROM ingestion_log")


def test_row_change_over_ten_percent_fails(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202607, rows(20))

    with pytest.raises(QualityError) as excinfo:
        load(clean_tables, tmp_path, 202608, rows(23))  # +15%

    assert failed_checks(excinfo) == {"row_change"}
    sql = "SELECT COUNT(*) FROM workplace_monthly WHERE snapshot_ym = 202608"
    assert count(clean_tables, sql) == 0


def test_row_change_within_ten_percent_passes(tmp_path, clean_tables):
    load(clean_tables, tmp_path, 202607, rows(20))

    assert load(clean_tables, tmp_path, 202608, rows(22)) == "success"  # +10%


def test_billed_over_income_cap_fails(tmp_path, clean_tables):
    # 2026-08 상한: 6,590,000 × 9.5% = 626,050원/인
    data = rows(10) + [Row("상한초과", biz_no6="999999", members=1, billed=700_000)]

    with pytest.raises(QualityError) as excinfo:
        load(clean_tables, tmp_path, 202608, data)

    assert failed_checks(excinfo) == {"billed_cap"}


def test_month_outside_nps_rate_fails(tmp_path, clean_tables):
    with pytest.raises(QualityError) as excinfo:
        load(clean_tables, tmp_path, 202301, rows(10))

    assert "rate_covered" in failed_checks(excinfo)


def test_failed_file_can_be_reloaded_after_fix(tmp_path, clean_tables):
    bad = rows(98) + rows(2, prefix="영명", members=0, billed=0)
    with pytest.raises(QualityError):
        load(clean_tables, tmp_path, 202608, bad)
    (tmp_path / "202608.csv").unlink()

    assert load(clean_tables, tmp_path, 202608, rows(100)) == "success"
