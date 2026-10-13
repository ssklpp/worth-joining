"""전월세전환율 적재 (SPEC Phase 9-8). 가상 값."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from pipeline.rent import conversion

CSV = """No,지역,지역,2024년 12월,2025년 1월,2025년 2월
No,지역,지역,전월세 전환율,전월세 전환율,전월세 전환율
1,서울,서울,4.6,4.7,
2,서울,강북지역,4.9,5.0,5.1
"""


def test_parse_takes_seoul_row_as_fraction_and_skips_blank_month():
    assert conversion.parse(CSV.splitlines()) == {202412: Decimal("0.046"),
                                                  202501: Decimal("0.047")}


def test_parse_without_seoul_row_fails():
    with pytest.raises(ValueError, match="서울 전체"):
        conversion.parse(CSV.splitlines()[:2] + ["2,서울,강북지역,4.9,5.0,5.1"])


@pytest.fixture
def engine(pipeline_engine):
    yield pipeline_engine
    with pipeline_engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE conversion_rate"))
        conn.execute(text("DELETE FROM ingestion_log WHERE source = 'conversion_rate'"))


def test_run_upserts_and_skips_same_file(engine, tmp_path):
    path = tmp_path / "rate.csv"
    path.write_text(CSV, encoding="cp949")

    assert conversion.run(engine, path) == "success"
    assert conversion.run(engine, path) == "skipped"

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT ym, rate_year FROM conversion_rate ORDER BY ym")).all()
    assert rows == [(202412, Decimal("0.0460")), (202501, Decimal("0.0470"))]
