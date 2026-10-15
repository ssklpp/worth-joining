"""OpenDART 기업개황(company.json) → dart_corp.bizr_no · corp_cls · adres (SPEC Phase 5-3).

python -m pipeline.dart.company_info [--limit N]

호출 순서: 상장사 → 정규화 이름이 최신 월 회사(mart_company_summary)에 있는 법인(가입자 많은 순)
→ 정규화 이름이 company에 있는 법인. fetched_at이 있는 법인은 건너뛴다. 하루 한도(20,000건,
api_call_log 'dart')에 닿으면 멈추고, 다음 실행에서 이어 받는다. 키가 비어 있으면 건너뛴다.
"""

import argparse
import logging
import sys
import time

from sqlalchemy import Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.http import ApiClient, ApiError, QuotaExceeded
from pipeline.common.ingestion import finish_run, start_run
from pipeline.dart.corp_code import API_SOURCE, DAILY_LIMIT

log = logging.getLogger(__name__)

SOURCE = "dart_company"
URL = "https://opendart.fss.or.kr/api/company.json"
OK, NO_DATA, OVER_LIMIT = "000", "013", "020"
INTERVAL = 0.1  # 초. 짧은 시간에 몰아서 부르면 DART가 차단할 수 있어 간격을 둔다

TARGETS = """
SELECT d.corp_code FROM dart_corp d
  LEFT JOIN (SELECT c.name_norm, MAX(s.members) AS members
               FROM company c JOIN mart_company_summary s ON s.company_id = c.company_id
              GROUP BY c.name_norm) a ON a.name_norm = d.corp_name_norm
 WHERE d.fetched_at IS NULL
   AND (d.stock_code IS NOT NULL OR a.name_norm IS NOT NULL
        OR EXISTS (SELECT 1 FROM company c WHERE c.name_norm = d.corp_name_norm))
 ORDER BY d.stock_code IS NULL, a.members IS NULL, a.members DESC, d.corp_code
"""


def targets(engine: Engine, limit: int | None) -> list[str]:
    """아직 받지 않은 법인(fetched_at NULL) 중 상장사 → 국민연금 회사와 이름이 같은 법인 순, 가입자
    많은 순.
    """
    with engine.connect() as conn:
        sql = TARGETS + (f" LIMIT {int(limit)}" if limit else "")
        return [r[0] for r in conn.execute(text(sql))]


def parse(body: dict) -> dict | None:
    """정상이면 저장할 값, 자료 없음이면 None. 한도 초과 · 키 오류 등은 예외."""
    status = body.get("status")
    if status == NO_DATA:
        return None
    if status == OVER_LIMIT:
        raise QuotaExceeded(f"DART 요청 제한 초과({status}): {body.get('message')}")
    if status != OK:
        raise ApiError(f"DART 오류 {status}: {body.get('message')}")
    bizr = "".join(ch for ch in body.get("bizr_no") or "" if ch.isdigit())
    # 국내 사업자번호는 10자리다. 해외 법인은 현지 번호(16자리 등)가 와서 매칭에 못 쓴다
    return {"bizr_no": bizr if len(bizr) == 10 else None,
            "corp_cls": body.get("corp_cls") or None,
            "adres": (body.get("adres") or "").strip()[:300] or None}


def save(engine: Engine, corp_code: str, info: dict | None) -> None:
    """응답이 없거나 오류면 빈 값으로 저장하고 fetched_at만 찍는다. 다음 실행에서 다시 받지 않기
    위해서다.
    """
    info = info or {"bizr_no": None, "corp_cls": None, "adres": None}
    with engine.begin() as conn:
        conn.execute(text(
            "UPDATE dart_corp SET bizr_no = :bizr_no, corp_cls = :corp_cls, adres = :adres,"
            " fetched_at = NOW() WHERE corp_code = :code"
        ), {**info, "code": corp_code})


def run(engine: Engine, client: ApiClient, api_key: str, limit: int | None = None,
        interval: float = INTERVAL) -> int:
    """하루 한도에 닿으면(QuotaExceeded) 실패로 남기지 않고 멈춘다. 남은 법인은 다음 실행에서 이어
    받는다.
    """
    codes = targets(engine, limit)
    with engine.begin() as conn:
        run_id = start_run(conn, SOURCE, f"{len(codes)}건", None)
    done, status, message = 0, "success", ""
    try:
        for code in codes:
            body = client.get(URL, {"crtfc_key": api_key, "corp_code": code}).json()
            save(engine, code, parse(body))
            done += 1
            if done % 1000 == 0:
                log.info("company.json %s / %s", done, len(codes))
            time.sleep(interval)
    except QuotaExceeded as e:  # 실패가 아니다. 남은 법인은 다음 실행에서
        message = f"한도 도달, 남은 {len(codes) - done}건: {e}"
        log.warning(message)
    except Exception as e:
        status, message = "failed", str(e)
        raise
    finally:
        with engine.begin() as conn:
            finish_run(conn, run_id, status, done, message)
    log.info("company.json %s건 저장", done)
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="이번 실행에서 부를 최대 법인 수")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not settings.opendart_api_key:
        log.warning("OPENDART_API_KEY가 비어 있어 company.json 수집을 건너뛴다")
        return 0
    engine = sync_engine()
    client = ApiClient(engine, API_SOURCE, DAILY_LIMIT, secret=settings.opendart_api_key)
    try:
        run(engine, client, settings.opendart_api_key, args.limit)
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
