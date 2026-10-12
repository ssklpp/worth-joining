"""국민연금 CSV → raw_nps_workplace (SPEC Phase 2-3, T1-03).

python -m pipeline.nps.load_raw --ym 202608 [--file data/raw/nps/202608.csv]

CP949 CSV를 UTF-8 TSV로 바꾸면서 name_norm을 붙이고 LOAD DATA LOCAL INFILE로 넣는다.
같은 월은 지우고 다시 넣어 멱등이다. 같은 체크섬이 이미 success면 건너뛴다.
"""

import argparse
import csv
import logging
import os
import sys
import tempfile
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run
from pipeline.common.normalize import normalize_name
from pipeline.nps.columns import ENCODING, FIELDS, check_header, to_snapshot_ym

log = logging.getLogger(__name__)

SOURCE = "nps"
RAW_COLUMNS = ["snapshot_ym", "run_id", *FIELDS, "name_norm"]
NAME = FIELDS.index("workplace_name")


def _tsv_value(value: str) -> str:
    if value == "":
        return r"\N"
    return (value.replace("\\", "\\\\").replace("\t", "\\t")
            .replace("\n", "\\n").replace("\r", "\\r"))


def write_tsv(csv_path: Path, tsv_path: Path, ym: int, run_id: int) -> int:
    """CP949 CSV를 RAW_COLUMNS 순서의 UTF-8 TSV로 쓴다. 파일의 자료 월이 ym과 다르면 ValueError."""
    rows = 0
    with csv_path.open(encoding=ENCODING, newline="") as src, \
            tsv_path.open("w", encoding="utf-8", newline="") as dst:
        reader = csv.reader(src)
        check_header(next(reader))
        for row in reader:
            row = [v.strip() for v in row]
            if to_snapshot_ym(row[0]) != ym:
                raise ValueError(f"{csv_path.name}: 자료 월 {row[0]}이 --ym {ym}과 다르다")
            values = [str(ym), str(run_id), *row, normalize_name(row[NAME])]
            dst.write("\t".join(_tsv_value(v) for v in values) + "\n")
            rows += 1
    return rows


def load_raw(conn: Connection, csv_path: Path, ym: int, run_id: int) -> int:
    """해당 월 raw를 지우고 다시 넣는다. 넣은 행 수를 돌려준다."""
    fd, tmp = tempfile.mkstemp(suffix=".tsv")
    os.close(fd)
    tsv_path = Path(tmp)
    try:
        expected = write_tsv(csv_path, tsv_path, ym, run_id)
        conn.execute(text("DELETE FROM raw_nps_workplace WHERE snapshot_ym = :ym"), {"ym": ym})
        result = conn.execute(
            text(
                rf"LOAD DATA LOCAL INFILE :path INTO TABLE raw_nps_workplace"
                rf" CHARACTER SET utf8mb4"
                rf" FIELDS TERMINATED BY '\t' ESCAPED BY '\\'"
                rf" LINES TERMINATED BY '\n'"
                rf" ({', '.join(RAW_COLUMNS)})"
            ),
            {"path": tsv_path.as_posix()},
        )
        if result.rowcount != expected:
            raise RuntimeError(f"적재 행 수 {result.rowcount} != 파일 행 수 {expected}")
        return expected
    finally:
        tsv_path.unlink(missing_ok=True)


def run(engine: Engine, csv_path: Path, ym: int) -> str:
    """체크섬 확인 → ingestion_log 기록 → 적재. 결과 상태를 돌려준다."""
    checksum = file_checksum(csv_path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, str(ym), checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            log.info("%s: 이미 적재됨, 건너뜀", ym)
            return "skipped"
        run_id = start_run(conn, SOURCE, str(ym), checksum)
    try:
        with engine.begin() as conn:
            rows = load_raw(conn, csv_path, ym, run_id)
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", rows)
        log.info("%s: raw %s행 적재", ym, f"{rows:,}")
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ym", type=int, required=True, help="자료 월, 예: 202608")
    parser.add_argument("--file", type=Path, help="기본값 data/raw/nps/<ym>.csv")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(sync_engine(), args.file or Path(f"data/raw/nps/{args.ym}.csv"), args.ym)
    return 0


if __name__ == "__main__":
    sys.exit(main())
