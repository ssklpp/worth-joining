"""ingestion_log 기록 (SPEC 4장 공통 수집기 요구사항)."""

import hashlib
from pathlib import Path

from sqlalchemy import Connection, text


def file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def already_succeeded(conn: Connection, source: str, checksum: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM ingestion_log"
             " WHERE source = :s AND checksum = :c AND status = 'success' LIMIT 1"),
        {"s": source, "c": checksum},
    ).first()
    return row is not None


def start_run(conn: Connection, source: str, target: str, checksum: str | None) -> int:
    result = conn.execute(
        text("INSERT INTO ingestion_log (source, target, checksum, status, started_at)"
             " VALUES (:s, :t, :c, 'running', NOW())"),
        {"s": source, "t": target, "c": checksum},
    )
    return result.lastrowid


def finish_run(
    conn: Connection, run_id: int, status: str, row_count: int | None = None, message: str = ""
) -> None:
    conn.execute(
        text("UPDATE ingestion_log SET status = :st, row_count = :n, message = :m,"
             " finished_at = NOW() WHERE run_id = :r"),
        {"st": status, "n": row_count, "m": message[:500], "r": run_id},
    )
