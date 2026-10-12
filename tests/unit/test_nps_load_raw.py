import pytest
from sqlalchemy import text

from pipeline.nps.load_raw import RAW_COLUMNS, load_raw, run, write_tsv
from tests.nps_csv import Row, write_nps_csv


def test_write_tsv_adds_ym_run_and_name_norm(tmp_path):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202608, [Row("가상테크(주)")])
    tsv = tmp_path / "a.tsv"

    assert write_tsv(csv_path, tsv, 202608, run_id=7) == 1
    values = tsv.read_text(encoding="utf-8").rstrip("\n").split("\t")
    record = dict(zip(RAW_COLUMNS, values, strict=True))
    assert record["snapshot_ym"] == "202608"
    assert record["run_id"] == "7"
    assert record["name_norm"] == "가상테크"
    assert record["left_on"] == r"\N"


def test_write_tsv_rejects_other_month(tmp_path):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202607, [Row("가상")])

    with pytest.raises(ValueError, match="자료 월"):
        write_tsv(csv_path, tmp_path / "a.tsv", 202608, run_id=1)


def test_load_raw_twice_keeps_same_rows(tmp_path, pipeline_engine):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202608, [Row("가상A"), Row("가상B", status="2")])

    with pipeline_engine.connect() as conn:
        trans = conn.begin()
        try:
            assert load_raw(conn, csv_path, 202608, run_id=1) == 2
            assert load_raw(conn, csv_path, 202608, run_id=2) == 2
            rows = conn.execute(text(
                "SELECT workplace_name, status_code, members, run_id FROM raw_nps_workplace"
                " WHERE snapshot_ym = 202608 ORDER BY workplace_name"
            )).all()
        finally:
            trans.rollback()

    assert [tuple(r) for r in rows] == [("가상A", "1", 10, 2), ("가상B", "2", 10, 2)]


def test_run_skips_file_already_loaded(tmp_path, clean_tables):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202608, [Row("가상A")])

    assert run(clean_tables, csv_path, 202608) == "success"
    assert run(clean_tables, csv_path, 202608) == "skipped"
    with clean_tables.connect() as conn:
        statuses = conn.execute(text(
            "SELECT status, row_count FROM ingestion_log ORDER BY run_id"
        )).all()
    assert [tuple(r) for r in statuses] == [("success", 1), ("skipped", None)]


def test_run_records_failure(tmp_path, clean_tables):
    csv_path = write_nps_csv(tmp_path / "a.csv", 202607, [Row("가상A")])

    with pytest.raises(ValueError):
        run(clean_tables, csv_path, 202608)
    with clean_tables.connect() as conn:
        status = conn.execute(text("SELECT status FROM ingestion_log")).scalar()
    assert status == "failed"
