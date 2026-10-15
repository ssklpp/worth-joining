"""mart 갱신 (SPEC Phase 3-3 · 9-9 · 11): sql/q1 → q2 → q6 → q5 → q5t를 한 트랜잭션으로
실행한다(q5t는 역세권 시세 24개월 추이).

python -m pipeline.refresh_mart

q6(회사 근처 역)은 q2의 회사와 company_location · station으로, q5(역세권 시세)는 rent_contract로
만든다. q5의 기준월은 신고가 끝난 달이다. 전월세 자료의 마지막 계약일을 자료 받은 날로 보고
pipeline.rent.seoul.period_end로 정한다(decisions/007). 전월세 자료가 없으면 q5는 건너뛴다.

mart는 core에서 언제든 다시 만들 수 있으므로 비우고 다시 넣는다(docs/04 D1 · D4).
한 트랜잭션이라 중간에 실패하면 이전 mart가 그대로 남는다. 실행은 ingestion_log에 남긴다.
"""

import datetime as dt
import logging
import sys
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import finish_run, start_run
from pipeline.rent.seoul import period_end

log = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
STEPS = [
    ("mart_company_monthly", "q1_company_monthly.sql"),
    ("mart_company_summary", "q2_company_summary.sql"),
    ("company_station", "q6_company_station.sql"),
]
WINDOWS = (6, 12, 24)  # docs/04 D7
GRAINS = ("month", "quarter")  # 24개월 추이 단위(FR-HOUS-04)
RADII = (500, 750)  # 역세권 반경(m, decisions/009). 가장 큰 값은 q5a의 거리 조건과 같아야 한다


def refresh(conn: Connection) -> dict[str, int]:
    """mart 테이블을 순서대로 비우고 다시 채운다. 테이블별 행 수를 돌려준다."""
    counts = {}
    for table, sql_file in STEPS:
        conn.execute(text(f"DELETE FROM {table}"))
        sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
        counts[table] = conn.execute(text(sql)).rowcount
    conn.execute(text("DELETE FROM mart_station_rent"))
    conn.execute(text("DELETE FROM mart_station_rent_trend"))
    end_ym = rent_end_ym(conn)
    if end_ym is not None:
        # q5 · q5t의 윈도 함수 + DISTINCT는 임시 테이블을 쓴다. 기본 한도(16MB)를 넘으면 디스크로
        # 내려가 750m 한 번이 10분을 넘긴다(TS-028). 이 연결에서만 256MB로 올린다
        conn.execute(text("SET SESSION tmp_table_size = 268435456,"
                          " max_heap_table_size = 268435456"))
        # 역-건물 쌍을 먼저 만든다(q5a 주석). 임시 테이블은 이 연결에서만 보이고
        # 암묵적 커밋을 일으키지 않는다
        conn.execute(text("CREATE TEMPORARY TABLE IF NOT EXISTS station_building"
                          " (station_id INT NOT NULL, building_id INT NOT NULL,"
                          " dist_m FLOAT NOT NULL,"
                          " PRIMARY KEY (building_id, station_id))"))
        conn.execute(text("DELETE FROM station_building"))
        conn.execute(text((SQL_DIR / "q5a_station_building.sql").read_text(encoding="utf-8")))
        sql = text((SQL_DIR / "q5_station_rent.sql").read_text(encoding="utf-8"))
        trend_sql = text((SQL_DIR / "q5t_station_rent_trend.sql").read_text(encoding="utf-8"))
        for radius in RADII:
            for n in WINDOWS:
                rows = conn.execute(sql, {"end_ym": end_ym, "radius": radius, "n": n}).rowcount
                counts[f"mart_station_rent_{radius}m_{n}"] = rows
            for grain in GRAINS:
                rows = conn.execute(trend_sql, {"end_ym": end_ym, "radius": radius,
                                                "grain": grain}).rowcount
                counts[f"mart_station_rent_trend_{radius}m_{grain}"] = rows
        conn.execute(text("DROP TEMPORARY TABLE station_building"))
    return counts


def rent_end_ym(conn: Connection) -> int | None:
    """전월세 집계 기준월. 마지막 계약일을 자료 받은 날로 본다(그날 - 30일이 속한 달의 전월)."""
    last = conn.execute(text(
        "SELECT MAX(contract_date) FROM raw_rent_contract WHERE contract_date REGEXP '^[0-9]{8}$'"
    )).scalar()
    return period_end(dt.date(int(last[:4]), int(last[4:6]), int(last[6:]))) if last else None


def run(engine: Engine) -> dict[str, int]:
    """ingestion_log 시작 → mart 갱신(한 트랜잭션) → 성공 · 실패 기록. 실패하면 예외를 다시 던진다.
    """
    with engine.begin() as conn:
        latest = conn.execute(text("SELECT MAX(snapshot_ym) FROM workplace_monthly")).scalar()
        run_id = start_run(conn, "mart", str(latest), None)
    try:
        with engine.begin() as conn:
            counts = refresh(conn)
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", counts["mart_company_summary"], message=str(counts))
        log.info("mart 갱신 (최신 %s): %s", latest, counts)
        return counts
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(sync_engine())
    return 0


if __name__ == "__main__":
    sys.exit(main())
