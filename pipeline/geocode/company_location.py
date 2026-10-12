"""회사 지도 좌표 → company_location (SPEC Phase 8-2, decisions/004).

python -m pipeline.geocode.company_location [--steps dart,name] [--name-limit 300]

회사마다 아래 순서로 정하고, 앞 단계에서 얻은 회사는 뒤 단계에서 건너뛴다.
좌표는 모두 juso에서 얻는다.
  1 dart : DART 본사 주소(대표 사업장과 같은 자치구일 때만) → building, basis dart_hq
  2 name : 가입자 많은 순 상위 회사의 "자치구 + 도로명 + 사업장명" 검색 결과가
           같은 도로에 1건 → name_search
  3 · 4  : 도로 · 동 중심(주소정보 출입구 파일)은 따로 만든다
대상은 최신 월에 가입자가 있는 회사(mart_company_summary)다. 다시 실행하면
geocode_cache를 쓰므로 juso 호출은 새 주소만큼만 든다. juso 키가 없으면 경고 후 건너뛴다.
"""

import argparse
import logging
import re
import sys
from collections import Counter

from sqlalchemy import Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.ingestion import finish_run, start_run
from pipeline.geocode.juso import Juso

log = logging.getLogger(__name__)

SOURCE = "company_location"

# 대표 사업장: 최신 월 가입자가 가장 많은 사업장(SPEC 6장). 동률은 workplace_id 작은 쪽
REP = """
WITH latest AS (SELECT latest_ym AS ym FROM mart_company_summary LIMIT 1),
rep AS (
  SELECT w.company_id, w.workplace_name, w.road_address,
         ROW_NUMBER() OVER (PARTITION BY w.company_id ORDER BY m.members DESC, w.workplace_id) AS rn
  FROM workplace w
  JOIN workplace_monthly m ON m.workplace_id = w.workplace_id
  JOIN latest l ON m.snapshot_ym = l.ym
)
"""

DART_TARGETS = REP + """
SELECT s.company_id, r.sigungu_name AS sgg, d.adres
FROM mart_company_summary s
JOIN company_dart_link l ON l.company_id = s.company_id
JOIN dart_corp d ON d.corp_code = l.corp_code
JOIN region r ON r.region_code = s.region_code
WHERE d.adres IS NOT NULL
ORDER BY s.members DESC
LIMIT :limit
"""

NAME_TARGETS = REP + """
SELECT s.company_id, r.sigungu_name AS sgg, rep.road_address, rep.workplace_name
FROM mart_company_summary s
JOIN region r ON r.region_code = s.region_code
JOIN rep ON rep.company_id = s.company_id AND rep.rn = 1
LEFT JOIN company_location cl
  ON cl.company_id = s.company_id AND cl.basis IN ('dart_hq', 'name_search')
WHERE cl.company_id IS NULL AND rep.road_address IS NOT NULL AND rep.road_address <> ''
ORDER BY s.members DESC
LIMIT :limit
"""

# 도로명 주소: 시도 자치구 도로명 건물번호(-부번). 지번 주소: 시도 자치구 동 본번(-부번)
# 도로명과 건물번호 사이에는 공백이 있어야 한다. "남대문로2가"처럼 동 이름의 숫자를 번호로 읽지 않게
ROAD = re.compile(r"^(서울(?:특별시)?)\s+(\S+구)\s+(\S+(?:로|길))\s+(\d+(?:-\d+)?)")
JIBUN = re.compile(r"^(서울(?:특별시)?)\s+(\S+구)\s+(\S+(?:동|가))\s*(?:산\s*)?(\d+(?:-\d+)?)")
CORP_WORDS = re.compile(r"\(주\)|（주）|㈜|주식회사|\(유\)|유한회사|\(사\)|사단법인")


def hq_query(adres: str) -> tuple[str, str, str, str] | None:
    """DART 주소 → (검색어, 자치구, 도로명 또는 동, 번호 "본번-부번").
    층 · 호 · 괄호 설명은 뺀다. 서울 주소가 아니면 None."""
    adres = " ".join(adres.split())
    m = ROAD.match(adres) or JIBUN.match(adres)
    if not m:
        return None
    _, sgg, street, number = m.groups()
    number = number if "-" in number else f"{number}-0"
    return f"서울특별시 {sgg} {street} {m.group(4)}", sgg, street, number


def workplace_query(sgg: str, road_address: str, name: str) -> tuple[str, str] | None:
    """(검색어, 도로명). 국민연금 사업장명의 회사 형태 · 현장 꼬리표는 뺀다."""
    road = road_address.split()[-1]
    if not road.endswith(("로", "길")):
        return None
    clean = CORP_WORDS.sub(" ", name)
    # "회사/일용/현장명", "회사-(상용)…", "회사(본사)"는 앞부분만. "에쓰-오일"의 하이픈은 둔다
    clean = re.split(r"/|-\s*[(（\[]|[(（\[]", clean)[0].strip()
    return (f"{sgg} {road} {clean}", road) if len(clean) >= 2 else None


def same_building(sgg: str, street: str, number: str):
    """같은 자치구 · 같은 도로(지번이면 같은 동)에서 번호가 정확히 같은 건물 하나.
    - "강남대로 382"를 찾으면 "382-2" 가로판매대 같은 부속 시설이 함께 나온다(번호로 거른다)
    - "양천로 13"을 찾으면 "양천로14나길 13"도 나온다(도로명으로 거른다)
    - 같은 건물이 건물명만 다르게 두 줄 나오기도 한다(주소가 모두 같으면 하나로 본다)"""
    def pick(results):
        hits = [r for r in results if r.get("sggNm") == sgg and (
            (r.get("rn") == street and f"{r.get('buldMnnm')}-{r.get('buldSlno')}" == number)
            or (r.get("emdNm") == street
                and f"{r.get('lnbrMnnm')}-{r.get('lnbrSlno')}" == number))]
        same = {(r.get("rn"), r.get("buldMnnm"), r.get("buldSlno")) for r in hits}
        return hits[0] if hits and len(same) == 1 else None
    return pick


def on_road(sgg: str, road: str):
    return lambda results: (lambda hits: hits[0] if len(hits) == 1 else None)(
        [r for r in results if r.get("sggNm") == sgg and r.get("rn") == road])


def save(engine: Engine, company_id: int, g, basis: str, addr_key: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            REPLACE INTO company_location
              (company_id, lon, lat, accuracy, basis, addr_key, refreshed_at)
            VALUES (:id, :lon, :lat, :acc, :basis, :key, NOW())
        """), {"id": company_id, "lon": g.lon, "lat": g.lat, "acc": g.accuracy, "basis": basis,
               "key": addr_key[:200]})


def step_dart(engine: Engine, juso: Juso, limit: int) -> Counter:
    counts = Counter()
    with engine.connect() as conn:
        rows = conn.execute(text(DART_TARGETS), {"limit": limit}).all()
    for i, (company_id, sgg, adres) in enumerate(rows, 1):
        q = hq_query(adres)
        if q is None:
            counts["dart_not_seoul_or_unparsed"] += 1
            continue
        keyword, hq_sgg, street, number = q
        if hq_sgg != sgg:  # 본사와 대표 사업장이 다른 자치구면 쓰지 않는다(decisions/004)
            counts["dart_other_sgg"] += 1
            continue
        key = f"addr:{keyword}"
        g = juso.geocode(key, keyword, pick=same_building(sgg, street, number))
        if g.status == "ok":
            save(engine, company_id, g, "dart_hq", key)
            counts["dart_hq"] += 1
        else:
            counts[f"dart_fail:{(g.fail_reason or '').split(':')[0]}"] += 1
        if i % 500 == 0:
            log.info("dart %s / %s %s", i, len(rows), dict(counts))
    return counts


def step_name(engine: Engine, juso: Juso, limit: int) -> Counter:
    counts = Counter()
    with engine.connect() as conn:
        rows = conn.execute(text(NAME_TARGETS), {"limit": limit}).all()
    for company_id, sgg, road_address, name in rows:
        q = workplace_query(sgg, road_address, name)
        if q is None:
            counts["name_unparsed"] += 1
            continue
        keyword, road = q
        key = f"name:{keyword}"
        g = juso.geocode(key, keyword, pick=on_road(sgg, road))
        if g.status == "ok":
            save(engine, company_id, g, "name_search", key)
            counts["name_search"] += 1
        else:
            counts[f"name_fail:{(g.fail_reason or '').split(':')[0]}"] += 1
    return counts


def run(engine: Engine, juso: Juso, steps: set[str], name_limit: int,
        dart_limit: int = 1_000_000) -> Counter:
    with engine.begin() as conn:
        run_id = start_run(conn, SOURCE, ",".join(sorted(steps)), None)
    counts, status = Counter(), "failed"
    try:
        if "dart" in steps:
            counts += step_dart(engine, juso, dart_limit)
        if "name" in steps:
            counts += step_name(engine, juso, name_limit)
        status = "success"
    finally:
        with engine.begin() as conn:
            finish_run(conn, run_id, status, counts["dart_hq"] + counts["name_search"],
                       str(dict(counts)))
    log.info("company_location %s", dict(counts))
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", default="dart,name")
    parser.add_argument("--dart-limit", type=int, default=1_000_000,
                        help="DART 본사 주소를 볼 상위 회사 수(시험용)")
    parser.add_argument("--name-limit", type=int, default=300,
                        help="상호 검색을 해 볼 상위 회사 수")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not (settings.juso_search_key and settings.juso_coord_key):
        log.warning("JUSO_SEARCH_KEY · JUSO_COORD_KEY가 비어 있어 회사 좌표를 건너뛴다")
        return 0
    engine = sync_engine()
    juso = Juso(engine, settings.juso_search_key, settings.juso_coord_key)
    try:
        run(engine, juso, set(args.steps.split(",")), args.name_limit, args.dart_limit)
    finally:
        juso.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
