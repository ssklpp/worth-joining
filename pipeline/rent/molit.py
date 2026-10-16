"""국토교통부 실거래가 공개시스템 전월세 CSV(성남) → raw_rent_contract → rent_contract · building
(decisions/010 2단계).

python -m pipeline.rent.molit [--as-of 2026-10-14] [data/raw/rent/seongnam_rent_*.csv ...]

rt.molit.go.kr에서 받은 연립다세대 · 오피스텔 전월세 파일(CP949, 머리글 1행)이다. 앞쪽 안내문과
번호 열은 받은 뒤 지웠다. 열 이름이 서울시 CSV와 달라 서울 CSV의 23열 순서로 옮겨 담는다.
그러면 raw 이후(rent_contract · building)는 pipeline.rent.seoul과 같은 코드로 처리된다.
- "시군구"("경기도 성남시 분당구 구미동")를 법정동코드 파일에서 찾아 자치구 · 법정동 코드를 만든다
- 번지가 "산"으로 시작하면 지번구분 2(산), 아니면 1
- 연립다세대 파일은 "건물명" · "주택유형", 오피스텔 파일은 "단지명"이고 주택유형 열이 없다
- 접수연도는 없어 비운다. row_hash는 서울과 같이 접수연도를 뺀 22열로 만든다. 기간이 겹치는 두
  파일에 같은 계약이 있어도 한 번만 들어간다
"""

import argparse
import csv
import datetime as dt
import logging
import sys
from collections import Counter
from pathlib import Path

from sqlalchemy import Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run
from pipeline.geocode import rnaddr
from pipeline.rent import seoul

log = logging.getLogger(__name__)

SOURCE = "rent_molit"
DEFAULT_GLOB = "data/raw/rent/seongnam_rent_*.csv"
DONG_FILE = Path("data/raw/region/legal_dong_codes_all.txt")


def dong_codes(path: Path = DONG_FILE) -> dict[str, str]:
    """법정동 전체 이름 → 10자리 코드. 존재하는 행만(폐지된 이름은 새 이름과 겹칠 수 있다)."""
    codes = {}
    for line in path.read_text(encoding="cp949").splitlines()[1:]:
        code, name, status = line.split("\t")
        if status == "존재":
            codes[name] = code
    return codes


def to_seoul_fields(row: dict[str, str], codes: dict[str, str]) -> list[str] | None:
    """국토부 한 행 → 서울 CSV 23열(seoul.RAW_COLUMNS 순서). 법정동을 못 찾으면 None."""
    full = " ".join(row["시군구"].split())
    code = codes.get(full)
    if code is None:
        return None
    _, city, gu, dong = full.split()[:4]
    mountain = row["번지"].strip().startswith("산")
    return [
        "", code[:5], f"{city} {gu}", code[5:], dong,
        "2" if mountain else "1", "산" if mountain else "대지",
        row["본번"], row["부번"], row["층"],
        f"{row['계약년월'].strip()}{int(row['계약일']):02d}", row["전월세구분"],
        row["전용면적(㎡)"], row["보증금(만원)"], row["월세금(만원)"],
        row.get("건물명") or row.get("단지명") or "", row["건축년도"],
        row.get("주택유형") or "오피스텔",
        row["계약기간"], row["계약구분"], row["갱신요구권 사용"],
        row["종전계약 보증금(만원)"], row["종전계약 월세(만원)"],
    ]


def load_raw(engine: Engine, path: Path, codes: dict[str, str]) -> str:
    """CSV → raw_rent_contract. row_hash 키로 INSERT IGNORE. 같은 파일(체크섬)은 건너뛴다."""
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    cols = ", ".join(seoul.RAW_COLUMNS)
    sql = text(f"INSERT IGNORE INTO raw_rent_contract (run_id, row_hash, {cols})"
               f" VALUES (:run_id, :row_hash, {', '.join(':' + c for c in seoul.RAW_COLUMNS)})")
    counts = Counter()
    try:
        values = []
        with path.open(encoding="cp949", newline="") as fh:
            for row in csv.DictReader(fh):
                counts["read"] += 1
                fields = to_seoul_fields(row, codes)
                if fields is None:
                    counts["unknown_dong"] += 1
                    continue
                values.append({"run_id": run_id, "row_hash": seoul.row_hash(fields),
                               **dict(zip(seoul.RAW_COLUMNS, (f.strip() for f in fields),
                                          strict=True))})
        with engine.begin() as conn:
            for start in range(0, len(values), seoul.BATCH):
                batch = values[start:start + seoul.BATCH]
                counts["inserted"] += conn.execute(sql, batch).rowcount
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", counts["inserted"], str(dict(counts)))
        log.info("%s %s", path.name, dict(counts))
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def run(engine: Engine, files: list[Path], as_of: dt.date, juso=None,
        dong_file: Path = DONG_FILE, address_path: Path | None = None) -> Counter:
    """서울과 같은 기준월 · 보관 기간으로 raw → core → building을 적재한다.
    건물 좌표는 서울 · 성남 주소 파일을 함께 쓴다(address_path는 시험용 파일 하나)."""
    end = seoul.period_end(as_of)
    first = seoul.month_add(end, -(seoul.RETENTION - 1))
    codes = dong_codes(dong_file)
    for path in files:
        load_raw(engine, path, codes)
    counts = Counter(rent_contract=seoul.load_core(engine, first))
    buildings = rnaddr.read_files(address_path) if address_path else rnaddr.read_all()
    counts += seoul.load_buildings(engine, seoul.lot_points(buildings), juso)
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--as-of", type=dt.date.fromisoformat, default=dt.date.today(),
                        help="자료를 받은 날(집계 기준월 계산)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    files = args.files or sorted(Path().glob(DEFAULT_GLOB))
    engine = sync_engine()
    juso = None
    if settings.juso_search_key and settings.juso_coord_key:
        from pipeline.geocode.juso import Juso

        juso = Juso(engine, settings.juso_search_key, settings.juso_coord_key)
    else:
        log.warning("juso 키가 없어 주소 파일에 없는 지번은 좌표 없이 둔다")
    try:
        log.info("rent %s", dict(run(engine, files, args.as_of, juso)))
    finally:
        if juso is not None:
            juso.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
