"""ingestion_log 기록 (SPEC 4장 공통 수집기 요구사항)."""

import hashlib
from pathlib import Path

from sqlalchemy import Connection, text


def file_checksum(path: Path) -> str:
    """파일 SHA-256. 같은 파일을 두 번 적재하지 않는 기준이다(already_succeeded)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def already_succeeded(conn: Connection, source: str, checksum: str) -> bool:
    """같은 출처 · 체크섬이 이미 success면 True. 적재기는 이때 skipped로 남기고 건너뛴다."""
    row = conn.execute(
        text("SELECT 1 FROM ingestion_log"
             " WHERE source = :s AND checksum = :c AND status = 'success' LIMIT 1"),
        {"s": source, "c": checksum},
    ).first()
    return row is not None


def start_run(conn: Connection, source: str, target: str, checksum: str | None) -> int:
    """running 행을 넣고 run_id를 돌려준다.
    호출하는 쪽은 적재 트랜잭션과 따로 커밋해, 적재가 실패해도 기록이 남게 한다.
    """
    result = conn.execute(
        text("INSERT INTO ingestion_log (source, target, checksum, status, started_at)"
             " VALUES (:s, :t, :c, 'running', NOW())"),
        {"s": source, "t": target, "c": checksum},
    )
    return result.lastrowid


def finish_run(
    conn: Connection, run_id: int, status: str, row_count: int | None = None, message: str = ""
) -> None:
    """status는 success · failed · skipped. message는 500자에서 자른다."""
    conn.execute(
        text("UPDATE ingestion_log SET status = :st, row_count = :n, message = :m,"
             " finished_at = NOW() WHERE run_id = :r"),
        {"st": status, "n": row_count, "m": message[:500], "r": run_id},
    )
