"""OpenDART 다중회사 주요계정(fnlttMultiAcnt.json) → dart_financial (SPEC Phase 5-5, DR-05).

python -m pipeline.dart.financials [--year 2025]

company_dart_link에 연결된 법인만, 한 번에 100개씩 부른다. 사업보고서(11011) 한 건에 당기 ·
전기 · 전전기 3개년이 들어 있으므로 --year와 그 3년 전을 불러 6개년을 채운다(API는 최대 5년).
연결재무제표(CFS)가 있으면 쓰고 없으면 별도(OFS). 다시 실행하면 같은 키를 덮어쓴다.
단일회사 API(fnlttSinglAcnt)로 부르면 법인 수 × 2건(약 2.6만)이라 하루 한도를 넘는다.
"""

import argparse
import logging
import sys
from collections import defaultdict
from datetime import date

from sqlalchemy import Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.http import ApiClient, ApiError, QuotaExceeded
from pipeline.common.ingestion import finish_run, start_run
from pipeline.dart.corp_code import API_SOURCE, DAILY_LIMIT

log = logging.getLogger(__name__)

SOURCE = "dart_financial"
URL = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
REPORT = "11011"  # 사업보고서
BATCH = 100
OK, NO_DATA, OVER_LIMIT = "000", "013", "020"
# 계정명 → 컬럼. 금융업은 매출액 대신 영업수익을 쓰기도 한다
ACCOUNTS = {"매출액": "revenue", "영업수익": "revenue", "영업이익": "operating_income",
            "당기순이익": "net_income", "부채총계": "total_liabilities", "자본총계": "total_equity"}
PERIODS = (("thstrm_amount", 0), ("frmtrm_amount", 1), ("bfefrmtrm_amount", 2))


def default_year(today: date | None = None) -> int:
    """사업보고서는 다음 해 3월 말까지 낸다. 4월부터 전년도 보고서를 쓴다."""
    today = today or date.today()
    return today.year - 1 if today.month >= 4 else today.year - 2


def amount(value: str | None) -> int | None:
    value = (value or "").replace(",", "").strip()
    return int(value) if value.lstrip("-").isdigit() else None


def parse(body: dict, year: int) -> list[dict]:
    """응답 → dart_financial 행. 회사마다 CFS가 있으면 CFS만, 없으면 OFS."""
    status = body.get("status")
    if status == NO_DATA:
        return []
    if status == OVER_LIMIT:
        raise QuotaExceeded(f"DART 요청 제한 초과({status}): {body.get('message')}")
    if status != OK:
        raise ApiError(f"DART 오류 {status}: {body.get('message')}")
    items = body.get("list", [])
    has_cfs = {i["corp_code"] for i in items if i.get("fs_div") == "CFS"}
    rows: dict[tuple[str, int], dict] = defaultdict(dict)
    for item in items:
        code, column = item["corp_code"], ACCOUNTS.get(item.get("account_nm", "").strip())
        if column is None or item.get("fs_div") != ("CFS" if code in has_cfs else "OFS"):
            continue
        for field, back in PERIODS:
            value = amount(item.get(field))
            row = rows[(code, year - back)]
            if value is not None and row.get(column) is None:  # 매출액이 영업수익보다 먼저
                row[column] = value
    return [{"corp_code": code, "bsns_year": y, "reprt_code": REPORT,
             **{c: values.get(c) for c in set(ACCOUNTS.values())}}
            for (code, y), values in rows.items() if values]


def save(engine: Engine, rows: list[dict]) -> None:
    if not rows:
        return
    columns = ["revenue", "operating_income", "net_income", "total_liabilities", "total_equity"]
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO dart_financial (corp_code, bsns_year, reprt_code, " + ", ".join(columns)
            + ") VALUES (:corp_code, :bsns_year, :reprt_code, "
            + ", ".join(f":{c}" for c in columns) + ") ON DUPLICATE KEY UPDATE "
            + ", ".join(f"{c} = VALUES({c})" for c in columns)
        ), rows)


def run(engine: Engine, client: ApiClient, api_key: str, year: int) -> int:
    with engine.connect() as conn:
        codes = [r[0] for r in conn.execute(text(
            "SELECT DISTINCT corp_code FROM company_dart_link ORDER BY corp_code"))]
    with engine.begin() as conn:
        run_id = start_run(conn, SOURCE, str(year), None)
    saved, status, message = 0, "success", ""
    try:
        for y in (year, year - 3):
            for i in range(0, len(codes), BATCH):
                body = client.get(URL, {"crtfc_key": api_key, "corp_code": ",".join(
                    codes[i:i + BATCH]), "bsns_year": str(y), "reprt_code": REPORT}).json()
                rows = parse(body, y)
                save(engine, rows)
                saved += len(rows)
    except QuotaExceeded as e:  # 같은 키를 덮어쓰므로 다음 실행에서 처음부터 다시 돌면 된다
        message = f"한도 도달: {e}"
        log.warning(message)
    except Exception as e:
        status, message = "failed", str(e)
        raise
    finally:
        with engine.begin() as conn:
            finish_run(conn, run_id, status, saved, message)
    log.info("dart_financial %s행 (법인 %s개, %s · %s년 보고서)", saved, len(codes), year, year - 3)
    return saved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=default_year(), help="최근 사업보고서 연도")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not settings.opendart_api_key:
        log.warning("OPENDART_API_KEY가 비어 있어 재무 수집을 건너뛴다")
        return 0
    engine = sync_engine()
    client = ApiClient(engine, API_SOURCE, DAILY_LIMIT, secret=settings.opendart_api_key)
    try:
        run(engine, client, settings.opendart_api_key, args.year)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
