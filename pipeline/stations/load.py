"""전국도시철도역사정보 표준데이터(XLSX) → station (SPEC Phase 9-1, decisions/007).

python -m pipeline.stations.load [--file data/raw/station/railway_stations_20260630.xlsx]

- 역사 도로명주소가 서울인 행만 쓴다.
- 환승역은 노선마다 행이 따로 있다. 이름이 같고(끝의 "역"과 괄호를 뺀 이름, 괄호 안 이름 포함)
  400m 안에 있는 행을 물리적 역 하나로 묶는다. 좌표는 묶인 행의 평균, 노선은 이름순으로 잇는다.
- 서울 범위 밖 좌표(예: 양원역이 다른 지역 같은 이름 역의 좌표)는 역 주소를 juso로 바꿔 쓴다.
  juso 키가 없거나 찾지 못하면 그 행을 빼고 경고한다.
- station_key(정규화한 이름)로 upsert하므로 다시 넣어도 station_id가 바뀌지 않는다.
"""

import argparse
import logging
import math
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from sqlalchemy import Connection, Engine, text

from app.core.config import settings
from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run

log = logging.getLogger(__name__)

SOURCE = "station"
DEFAULT_FILE = Path("data/raw/station/railway_stations_20260630.xlsx")
COLUMNS = {"역사명": "name", "노선명": "line", "역위도": "lat", "역경도": "lon",
           "역사도로명주소": "address"}
SEOUL = {"lat": (37.41, 37.72), "lon": (126.73, 127.27)}
SAME_STATION_M = 400

Locate = Callable[[str], tuple[float, float] | None]  # 주소 → (경도, 위도)


@dataclass
class Row:
    name: str
    line: str
    lon: float
    lat: float
    names: set[str] = field(default_factory=set)


def base_name(name: str) -> str:
    """괄호를 빼고 끝의 "역"을 뗀다. "용산역" → "용산", "총신대입구(이수)" → "총신대입구"."""
    plain = re.sub(r"\(.*?\)", "", name).strip()
    return plain[:-1] if plain.endswith("역") and len(plain) > 2 else plain


def aliases(name: str) -> set[str]:
    """비교에 쓰는 이름들: 기본 이름과 괄호 안 이름. "총신대입구(이수)" → {총신대입구, 이수}."""
    inner = {base_name(x) for x in re.findall(r"\((.*?)\)", name)}
    return {base_name(name)} | {x for x in inner if len(x) >= 2}


def line_label(line: str) -> str:
    """"서울 도시철도 9호선" · "수도권  도시철도 9호선" → "9호선"."""
    return line.split()[-1]


def in_seoul(lon: float, lat: float) -> bool:
    return SEOUL["lon"][0] <= lon <= SEOUL["lon"][1] and SEOUL["lat"][0] <= lat <= SEOUL["lat"][1]


def address_keyword(address: str) -> str:
    """"서울시 중랑구 송림길 147(망우동)" → "서울특별시 중랑구 송림길 147"."""
    plain = re.sub(r"\(.*?\)", "", address).strip()
    return re.sub(r"^서울(시|특별시)?\s", "서울특별시 ", plain)


def read_rows(frame: pd.DataFrame, locate: Locate | None) -> tuple[list[Row], int]:
    """서울 행 → Row 목록과 뺀 행 수."""
    df = frame.rename(columns=COLUMNS)
    df = df[df["address"].fillna("").str.match(r"^서울")]
    rows, dropped = [], 0
    for r in df.itertuples():
        lon, lat = float(r.lon), float(r.lat)
        if not in_seoul(lon, lat):
            point = locate(address_keyword(r.address)) if locate else None
            if point is None or not in_seoul(*point):
                log.warning("역 좌표가 서울 밖이고 주소로도 찾지 못해 뺀다: %s %s", r.name, r.line)
                dropped += 1
                continue
            log.info("역 좌표를 주소로 고쳤다: %s %s (%.5f, %.5f)", r.name, r.line, *point)
            lon, lat = point
        rows.append(Row(r.name, line_label(r.line), lon, lat, aliases(r.name)))
    return rows, dropped


def distance_m(a: Row, b: Row) -> float:
    dy = (a.lat - b.lat) * 111_320
    dx = (a.lon - b.lon) * 111_320 * math.cos(math.radians((a.lat + b.lat) / 2))
    return math.hypot(dx, dy)


def cluster(rows: list[Row]) -> list[list[Row]]:
    """이름(별칭 포함)이 겹치고 400m 안이면 같은 역. 연결된 행끼리 묶는다(union-find)."""
    parent = list(range(len(rows)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows[i].names & rows[j].names and distance_m(rows[i], rows[j]) <= SAME_STATION_M:
                parent[find(i)] = find(j)
    groups: dict[int, list[Row]] = {}
    for i, row in enumerate(rows):
        groups.setdefault(find(i), []).append(row)
    return list(groups.values())


def station_of(group: list[Row]) -> dict:
    """묶음 → station 행. 이름은 가장 많이 쓰인 기본 이름(같으면 짧은 것), 키는 기본 이름."""
    # 코레일 표기("용산역")와 서울교통공사 표기("용산")를 맞춘다. 서울역만 "역"을 붙여 부른다
    names = [base_name(r.name) for r in group]
    display = min(set(names), key=lambda n: (-names.count(n), len(n), n))
    display = "서울역" if display == "서울" else display
    return {
        "key": base_name(display),
        "name": display,
        "lines": ",".join(sorted({r.line for r in group})),
        "lon": round(sum(r.lon for r in group) / len(group), 7),
        "lat": round(sum(r.lat for r in group) / len(group), 7),
    }


def distinguish(stations: list[dict]) -> list[dict]:
    """같은 이름의 역이 400m 밖에 따로 있으면 노선을 붙여 구분한다.
    예: 2호선 신촌 · 경의중앙선 신촌 → "신촌(2호선)", "신촌(경의중앙선)"."""
    keys = [s["key"] for s in stations]
    for s in stations:
        if keys.count(s["key"]) > 1:
            s["key"], s["name"] = f"{s['key']}({s['lines']})", f"{s['name']}({s['lines']})"
    return stations


def load(conn: Connection, stations: list[dict]) -> int:
    for s in stations:
        conn.execute(text("""
            INSERT INTO station (station_key, station_name, line_names, pt)
            VALUES (:key, :name, :lines, POINT(:lon, :lat))
            ON DUPLICATE KEY UPDATE station_name = VALUES(station_name),
              line_names = VALUES(line_names), pt = VALUES(pt)
        """), s)
    return len(stations)


def run(engine: Engine, path: Path, locate: Locate | None) -> str:
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    try:
        rows, dropped = read_rows(pd.read_excel(path, dtype=str), locate)
        stations = distinguish([station_of(g) for g in cluster(rows)])
        with engine.begin() as conn:
            n = load(conn, stations)
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", n,
                       f"서울 {len(rows)}행 → 역 {n}곳, 뺀 행 {dropped}")
        log.info("station 서울 %s행 → 역 %s곳 (뺀 행 %s)", len(rows), n, dropped)
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def juso_locator(engine: Engine) -> tuple[Locate | None, Callable[[], None]]:
    if not (settings.juso_search_key and settings.juso_coord_key):
        log.warning("juso 키가 없어 서울 밖 좌표의 역은 고치지 않고 뺀다")
        return None, lambda: None
    from pipeline.geocode.juso import Juso

    juso = Juso(engine, settings.juso_search_key, settings.juso_coord_key)

    def locate(keyword: str):
        g = juso.geocode(f"addr:{keyword}", keyword)
        return (g.lon, g.lat) if g.status == "ok" else None
    return locate, juso.close


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = sync_engine()
    locate, close = juso_locator(engine)
    try:
        run(engine, args.file, locate)
    finally:
        close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
