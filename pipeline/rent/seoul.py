"""서울시 부동산 전월세가 연도별 CSV → raw_rent_contract → rent_contract · building
(SPEC Phase 9-2 · 4 · 6 · 7, decisions/007).

python -m pipeline.rent.seoul [--as-of 2026-10-13] [data/raw/rent/seoul_rent_*.csv ...]

1. raw: CSV(CP949, 23열, 머리글 1행) 행을 글자 그대로 넣는다. 2026 파일은 머리글 이름만 달라서
   이름이 아니라 열 순서로 읽는다. row_hash는 접수연도를 뺀 22열을 정규화(공백, 본번 · 부번 · 층의
   앞자리 0, 금액 쉼표, 면적 소수점)해 만든 MD5다. 연도 파일끼리 겹친 계약은 한 번만 들어간다.
   같은 파일은 체크섬으로 건너뛴다.
2. core: 연립다세대 · 오피스텔, 본번이 있는 행, 보관 기간(집계 기준월 - 23개월 이후)만
   rent_contract로 옮긴다. contract_ym은 계약일에서 만든다. 월 파티션을 먼저 만든다.
3. building: 서로 다른 지번 건물마다 좌표를 붙인다. 지번 → 도로명주소 한글 파일의 건물 →
   출입구 좌표(같은 지번에 건물이 여럿이면 중앙값). 파일에 없는 지번만 juso 검색 API로 찾는다
   (키가 없으면 건너뛴다). 좌표가 없는 건물은 building에 넣지 않는다(공간 인덱스는 NOT NULL).
집계 기준월은 자료 받은 날(--as-of) - 30일이 속한 달의 전월이다(decisions/007).
"""

import argparse
import csv
import datetime as dt
import hashlib
import logging
import statistics
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run
from pipeline.geocode import rnaddr
from pipeline.rent import partitions

log = logging.getLogger(__name__)

SOURCE = "rent_seoul"
DEFAULT_GLOB = "data/raw/rent/seoul_rent_*.csv"
COLUMNS = 23
RETENTION = 24
BATCH = 5000

# raw_rent_contract 열 순서 = CSV 열 순서
RAW_COLUMNS = [
    "receipt_year", "sgg_code", "sgg_name", "bjdong_code", "bjdong_name", "jibun_type",
    "jibun_type_name", "main_no", "sub_no", "floor", "contract_date", "rent_type", "area_m2",
    "deposit_man", "monthly_man", "building_name", "build_year", "house_type", "contract_term",
    "new_or_renew", "renewal_right", "prev_deposit", "prev_monthly",
]
INTEGER_COLS = {7, 8, 9}  # 본번, 부번, 층: "0183" → "183"
MONEY_COLS = {13, 14, 21, 22}


def month_add(ym: int, n: int) -> int:
    y, m = divmod(ym // 100 * 12 + ym % 100 - 1 + n, 12)
    return y * 100 + m + 1


def period_end(as_of: dt.date) -> int:
    """신고가 끝난 달: 자료 받은 날 - 30일이 속한 달의 전월(decisions/007). 2026-10-13 → 202608."""
    d = as_of - dt.timedelta(days=30)
    return month_add(d.year * 100 + d.month, -1)


def normalize(fields: list[str]) -> list[str]:
    g = [f.strip() for f in fields]
    for i in INTEGER_COLS:
        if g[i].lstrip("-").isdigit():
            g[i] = str(int(g[i]))
    for i in MONEY_COLS:
        g[i] = g[i].replace(",", "")
    if g[12]:
        try:
            g[12] = format(Decimal(g[12]).normalize(), "f")
        except InvalidOperation:
            pass
    return g


def row_hash(fields: list[str]) -> str:
    """접수연도(0열)를 뺀 22열. 연도 파일끼리 같은 계약이 겹쳐도 같은 값이 된다."""
    return hashlib.md5("|".join(normalize(fields)[1:]).encode("utf-8")).hexdigest()


def read_csv(path: Path):
    with path.open(encoding="cp949", newline="") as fh:
        reader = csv.reader(fh)
        next(reader)  # 머리글
        for fields in reader:
            if len(fields) == COLUMNS:
                yield fields


def load_raw(engine: Engine, path: Path) -> str:
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    cols = ", ".join(RAW_COLUMNS)
    sql = text(f"INSERT IGNORE INTO raw_rent_contract (run_id, row_hash, {cols})"
               f" VALUES (:run_id, :row_hash, {', '.join(':' + c for c in RAW_COLUMNS)})")
    read = inserted = 0
    try:
        batch = []
        with engine.begin() as conn:
            for fields in read_csv(path):
                read += 1
                batch.append({"run_id": run_id, "row_hash": row_hash(fields),
                              **dict(zip(RAW_COLUMNS, (f.strip() for f in fields), strict=True))})
                if len(batch) == BATCH:
                    inserted += conn.execute(sql, batch).rowcount
                    batch = []
            if batch:
                inserted += conn.execute(sql, batch).rowcount
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", inserted, f"읽음 {read}, 새 행 {inserted}")
        log.info("%s 읽음 %s, 새 행 %s(나머지는 다른 파일과 겹침)", path.name, read, inserted)
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


# 보관 기간 안의 연립다세대 · 오피스텔. 금액 · 면적 · 층은 숫자로 바꿀 수 있는 것만
CORE = """
INSERT IGNORE INTO rent_contract
  (contract_ym, row_hash, addr_key, house_type, area_m2, deposit_man, monthly_man, floor)
SELECT CAST(LEFT(contract_date, 6) AS UNSIGNED), row_hash,
       CONCAT(sgg_code, '-', bjdong_code, '-', jibun_type, '-',
              CAST(main_no AS UNSIGNED), '-', CAST(sub_no AS UNSIGNED)),
       house_type, CAST(area_m2 AS DECIMAL(7,2)),
       CAST(REPLACE(deposit_man, ',', '') AS UNSIGNED),
       CAST(REPLACE(monthly_man, ',', '') AS UNSIGNED),
       IF(floor REGEXP '^-?[0-9]+$', CAST(floor AS SIGNED), NULL)
FROM raw_rent_contract
WHERE house_type IN ('연립다세대', '오피스텔')
  AND contract_date REGEXP '^[0-9]{8}$'
  AND CAST(LEFT(contract_date, 6) AS UNSIGNED) >= :first_ym
  AND main_no REGEXP '^[0-9]+$' AND sub_no REGEXP '^[0-9]+$'
  AND jibun_type IN ('1', '2')
  AND area_m2 REGEXP '^[0-9]+([.][0-9]+)?$'
  AND REPLACE(deposit_man, ',', '') REGEXP '^[0-9]+$'
  AND REPLACE(monthly_man, ',', '') REGEXP '^[0-9]+$'
"""

# rent_contract에 있는 지번 건물(주택유형별)과 이름 · 건축년도
BUILDINGS = """
SELECT r.addr_key, r.house_type, MAX(w.sgg_name) AS sgg_name, MAX(w.bjdong_name) AS bjdong_name,
       MAX(IF(w.build_year REGEXP '^[0-9]{4}$', CAST(w.build_year AS UNSIGNED), NULL)) AS build_year
FROM rent_contract r
JOIN raw_rent_contract w ON w.row_hash = r.row_hash
GROUP BY r.addr_key, r.house_type
"""


def load_core(engine: Engine, first_ym: int) -> int:
    with engine.connect() as conn:
        last = conn.execute(text(
            "SELECT MAX(CAST(LEFT(contract_date, 6) AS UNSIGNED)) FROM raw_rent_contract"
            " WHERE contract_date REGEXP '^[0-9]{8}$'")).scalar()
        partitions.ensure(conn, first_ym, max(last or first_ym, first_ym))
    with engine.begin() as conn:
        n = conn.execute(text(CORE), {"first_ym": first_ym}).rowcount
    log.info("rent_contract 새 행 %s (%s 이후)", n, first_ym)
    return n


def lot_key(addr_key: str) -> tuple[str, bool, int, int]:
    """addr_key(자치구-법정동-지번구분-본번-부번) → 도로명주소 파일의 지번 키."""
    sgg, dong, kind, main, sub = addr_key.split("-")
    return sgg + dong, kind == "2", int(main), int(sub)


def lot_points(buildings) -> dict[tuple[str, bool, int, int], tuple[float, float]]:
    """지번 → 출입구 좌표. 한 지번에 건물이 여럿이면 경도 · 위도 중앙값."""
    found = defaultdict(list)
    for b in buildings:
        found[(b.adm_cd, b.mountain, b.lot_main, b.lot_sub)].append((b.lon, b.lat))
    return {k: (round(statistics.median(p[0] for p in v), 7),
                round(statistics.median(p[1] for p in v), 7)) for k, v in found.items()}


def load_buildings(engine: Engine, lots, juso=None) -> Counter:
    counts = Counter()
    with engine.connect() as conn:
        rows = conn.execute(text(BUILDINGS)).mappings().all()
    values = []
    for r in rows:
        point = lots.get(lot_key(r["addr_key"]))
        if point:
            counts["file"] += 1
        elif juso is not None:
            point = search_lot(juso, r)
            counts["search" if point else "not_found"] += 1
        else:
            counts["not_found"] += 1
        if point:
            values.append({"key": r["addr_key"], "type": r["house_type"], "year": r["build_year"],
                           "lon": point[0], "lat": point[1]})
    with engine.begin() as conn:
        for start in range(0, len(values), BATCH):
            conn.execute(text("""
                INSERT INTO building (addr_key, house_type, build_year, pt)
                VALUES (:key, :type, :year, POINT(:lon, :lat))
                ON DUPLICATE KEY UPDATE build_year = VALUES(build_year), pt = VALUES(pt)
            """), values[start:start + BATCH])
        linked = conn.execute(text("""
            UPDATE rent_contract r
            JOIN building b ON b.addr_key = r.addr_key AND b.house_type = r.house_type
            SET r.building_id = b.building_id
            WHERE r.building_id IS NULL OR r.building_id <> b.building_id
        """)).rowcount
    counts["linked_contracts"] = linked
    log.info("building %s곳 %s", len(values), dict(counts))
    return counts


def one_building(sgg: str, dong: str):
    """같은 자치구 · 법정동의 결과가 모두 한 건물(도로명 + 건물번호)이면 채택한다.
    파일에 없는 지번은 대개 여러 필지에 걸친 건물의 부속 지번이라, 검색하면 대표 지번이 다른
    건물이 나온다(예: 원남동 66-67 → 66-60, 창경궁로18길 20). 그래서 지번 번호는 맞추지 않는다."""
    def pick(results):
        hits = [r for r in results if r.get("sggNm") == sgg and r.get("emdNm") == dong]
        same = {(r.get("rn"), r.get("buldMnnm"), r.get("buldSlno")) for r in hits}
        return hits[0] if hits and len(same) == 1 else None
    return pick


def search_lot(juso, row) -> tuple[float, float] | None:
    """파일에 없는 지번: "자치구 법정동 (산)본번-부번"을 검색해 한 건물이면 그 좌표."""
    _, mountain, main, sub = lot_key(row["addr_key"])
    keyword = (f"서울특별시 {row['sgg_name']} {row['bjdong_name']} "
               f"{'산 ' if mountain else ''}{main}-{sub}")
    g = juso.geocode(f"jibun:{row['addr_key']}", keyword,
                     pick=one_building(row["sgg_name"], row["bjdong_name"]))
    return (g.lon, g.lat) if g.status == "ok" else None


def run(engine: Engine, files: list[Path], as_of: dt.date, juso=None,
        address_path: Path = rnaddr.ADDRESS_PATH) -> Counter:
    end = period_end(as_of)
    first = month_add(end, -(RETENTION - 1))
    log.info("집계 기준월 %s, 보관 %s ~", end, first)
    for path in files:
        load_raw(engine, path)
    counts = Counter(rent_contract=load_core(engine, first))
    counts += load_buildings(engine, lot_points(rnaddr.read_files(address_path)), juso)
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
