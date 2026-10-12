import json
from datetime import date
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from pipeline.common.http import ApiClient, ApiError
from pipeline.dart.financials import default_year, parse, run

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dart" / "fnlttMultiAcnt.json"


def body():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def by_key(rows):
    return {(r["corp_code"], r["bsns_year"]): r for r in rows}


def test_parse_prefers_consolidated_and_spreads_three_years():
    rows = by_key(parse(body(), 2025))

    first = rows[("00000001", 2025)]
    assert (first["revenue"], first["operating_income"], first["net_income"]) == (
        1_200_000_000, 120_000_000, 80_000_000)  # OFS 매출 700,000,000이 아니라 CFS
    assert (first["total_liabilities"], first["total_equity"]) == (600_000_000, 400_000_000)
    assert rows[("00000001", 2024)]["operating_income"] == -50_000_000
    assert rows[("00000001", 2023)]["total_equity"] is None  # "-"는 값 없음


def test_parse_uses_separate_when_no_consolidated_and_bank_revenue():
    rows = by_key(parse(body(), 2025))

    assert rows[("00000002", 2025)]["revenue"] == 50_000_000      # OFS만 있는 회사
    assert ("00000002", 2023) not in rows                          # 전전기 값이 모두 비면 행 없음
    assert rows[("00000003", 2025)]["revenue"] == 3_000_000_000   # 금융업 영업수익


def test_parse_no_data_and_error():
    assert parse({"status": "013", "message": "조회된 데이타가 없습니다."}, 2025) == []
    with pytest.raises(ApiError, match="010"):
        parse({"status": "010", "message": "등록되지 않은 키입니다."}, 2025)


@pytest.mark.parametrize("today, year", [(date(2026, 10, 12), 2025), (date(2026, 3, 31), 2024)])
def test_default_year(today, year):
    assert default_year(today) == year


def test_run_calls_batches_for_two_report_years_and_is_idempotent(clean_tables):
    with clean_tables.begin() as conn:
        conn.execute(text("INSERT INTO company_dart_link VALUES (1, '00000001', 'exact', 1),"
                          " (2, '00000002', 'fuzzy', 0.9), (3, '00000001', 'exact', 1)"))
    calls = []

    def handler(req):
        calls.append((req.url.params["corp_code"], req.url.params["bsns_year"]))
        return httpx.Response(200, json=body() if req.url.params["bsns_year"] == "2025"
                              else {"status": "013", "message": "없음"})

    client = ApiClient(clean_tables, "dart", 100, transport=httpx.MockTransport(handler),
                       backoff=0)
    run(clean_tables, client, "KEY", 2025)
    run(clean_tables, client, "KEY", 2025)

    assert calls[:2] == [("00000001,00000002", "2025"), ("00000001,00000002", "2022")]
    with clean_tables.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM dart_financial")).scalar()
    assert n == 6  # 00000001 3년, 00000002 2년, 00000003 1년(연결 안 됐지만 응답에 있음)
