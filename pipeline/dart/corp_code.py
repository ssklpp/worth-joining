"""OpenDART 고유번호(corpCode.xml) → dart_corp (SPEC Phase 5-2).

python -m pipeline.dart.corp_code [--file corpCode.zip]

ZIP 안의 CORPCODE.xml(약 11만 법인)을 읽어 corp_code · corp_name · corp_name_norm · stock_code를
UPSERT한다. bizr_no · corp_cls · adres는 company.json으로 채우므로 덮어쓰지 않는다.
--file이 없으면 OPENDART_API_KEY로 내려받고, 키가 비어 있으면 경고 후 건너뛴다.
같은 ZIP(체크섬)은 다시 적재하지 않는다.
"""

import argparse
import hashlib
import io
import logging
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.http import ApiClient, ApiError
from pipeline.common.ingestion import already_succeeded, finish_run, start_run
from pipeline.common.normalize import normalize_name

log = logging.getLogger(__name__)

SOURCE = "dart_corp"
API_SOURCE = "dart"  # api_call_log: DART 엔드포인트 전체가 하루 20,000건을 나눠 쓴다
DAILY_LIMIT = 20_000
URL = "https://opendart.fss.or.kr/api/corpCode.xml"
BATCH = 5_000


def parse(zip_bytes: bytes) -> list[dict]:
    """ZIP → [{code, name, norm, stock}]. 상장사가 아니면 stock은 None."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xml = zf.read(zf.namelist()[0])
    rows = []
    for item in ET.fromstring(xml).iter("list"):
        name = (item.findtext("corp_name") or "").strip()
        stock = (item.findtext("stock_code") or "").strip()
        rows.append({"code": item.findtext("corp_code").strip(), "name": name,
                     "norm": normalize_name(name), "stock": stock or None})
    return rows


def load(conn: Connection, rows: list[dict]) -> int:
    sql = text(
        "INSERT INTO dart_corp (corp_code, corp_name, corp_name_norm, stock_code)"
        " VALUES (:code, :name, :norm, :stock)"
        " ON DUPLICATE KEY UPDATE corp_name = VALUES(corp_name),"
        " corp_name_norm = VALUES(corp_name_norm), stock_code = VALUES(stock_code)"
    )
    for i in range(0, len(rows), BATCH):
        conn.execute(sql, rows[i:i + BATCH])
    return len(rows)


def download(engine: Engine, api_key: str) -> bytes:
    client = ApiClient(engine, API_SOURCE, DAILY_LIMIT, secret=api_key)
    try:
        body = client.get(URL, {"crtfc_key": api_key}).content
    finally:
        client.close()
    if not body.startswith(b"PK"):  # 키 오류 등은 ZIP 대신 XML 오류 응답이 온다
        raise ApiError(f"corpCode.xml이 ZIP이 아니다: {body[:200].decode('utf-8', 'replace')}")
    return body


def run(engine: Engine, zip_bytes: bytes) -> str:
    checksum = hashlib.sha256(zip_bytes).hexdigest()
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, "corpCode", checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, "corpCode", checksum)
    try:
        with engine.begin() as conn:
            n = load(conn, parse(zip_bytes))
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", n)
        log.info("dart_corp %s행 적재", n)
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="내려받아 둔 corpCode ZIP")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = sync_engine()
    if args.file:
        zip_bytes = args.file.read_bytes()
    elif settings.opendart_api_key:
        zip_bytes = download(engine, settings.opendart_api_key)
    else:
        log.warning("OPENDART_API_KEY가 비어 있어 dart_corp 적재를 건너뛴다")
        return 0
    run(engine, zip_bytes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
