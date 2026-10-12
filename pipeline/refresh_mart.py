"""mart 갱신 (SPEC Phase 3-3): sql/q1 → q2를 한 트랜잭션으로 실행한다.

python -m pipeline.refresh_mart

mart는 core에서 언제든 다시 만들 수 있으므로 비우고 다시 넣는다(docs/04 D1 · D4).
한 트랜잭션이라 중간에 실패하면 이전 mart가 그대로 남는다. 실행은 ingestion_log에 남긴다.
"""

import logging
import sys
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import finish_run, start_run

log = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
STEPS = [
    ("mart_company_monthly", "q1_company_monthly.sql"),
    ("mart_company_summary", "q2_company_summary.sql"),
]


def refresh(conn: Connection) -> dict[str, int]:
    """mart 테이블을 순서대로 비우고 다시 채운다. 테이블별 행 수를 돌려준다."""
    counts = {}
    for table, sql_file in STEPS:
        conn.execute(text(f"DELETE FROM {table}"))
        sql = (SQL_DIR / sql_file).read_text(encoding="utf-8")
        counts[table] = conn.execute(text(sql)).rowcount
    return counts


def run(engine: Engine) -> dict[str, int]:
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
