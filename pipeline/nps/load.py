"""국민연금 한 달치 적재 (SPEC Phase 2-3).

python -m pipeline.nps.load --ym 202608 [--file data/raw/nps/202608.csv]
python -m pipeline.nps.load --all            # data/raw/nps/*.csv를 월 오름차순으로

raw(load_raw)와 core(load_core)를 넣고 품질 검사(quality)까지 한 트랜잭션으로 한다.
검사에 실패하면 그 달의 raw · core를 되돌리고 failed로 남긴다. 같은 체크섬이 이미 success면
건너뛰고, 모든 실행을 ingestion_log에 남긴다. 월은 오름차순으로 넣어야 한다(load_core 참고).
"""

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import Engine

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run
from pipeline.nps.load_core import load_core
from pipeline.nps.load_raw import load_raw
from pipeline.nps.quality import QualityError, run_checks

log = logging.getLogger(__name__)

SOURCE = "nps"
RAW_DIR = Path("data/raw/nps")


def run(engine: Engine, csv_path: Path, ym: int) -> str:
    """체크섬 확인 → ingestion_log 기록 → raw · core 적재. 결과 상태를 돌려준다."""
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
            counts = load_core(conn, ym)
            checks = run_checks(conn, ym)
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", rows,
                       message=f"{counts} | " + "; ".join(f"{c.name}: {c.detail}" for c in checks))
        log.info("%s: raw %s행, core %s", ym, f"{rows:,}", counts)
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--ym", type=int, help="자료 월, 예: 202608")
    target.add_argument("--all", action="store_true", help="data/raw/nps/*.csv 전체")
    parser.add_argument("--file", type=Path, help="--ym과 함께. 기본값 data/raw/nps/<ym>.csv")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = sync_engine()
    targets = (
        [(p, int(p.stem)) for p in sorted(RAW_DIR.glob("[0-9]" * 6 + ".csv"))] if args.all
        else [(args.file or RAW_DIR / f"{args.ym}.csv", args.ym)]
    )
    for path, ym in targets:
        try:
            run(engine, path, ym)
        except QualityError as e:
            # 뒤 달은 전월 조건에 기대므로 실패한 달에서 멈춘다
            log.error("%s: 품질 검사 실패, 적재를 되돌림: %s", ym, e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
