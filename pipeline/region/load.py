"""법정동코드 전체자료 → region (시군구 코드 5자리 → 시도 · 시군구 이름, SPEC Phase 2-2).

python -m pipeline.region.load [--file data/raw/region/legal_dong_codes_seoul.txt]

원본은 행정표준코드관리시스템(code.go.kr)의 "법정동코드 전체자료"(CP949, 탭 구분:
법정동코드, 법정동명, 폐지여부)다. 서울 범위(decisions/002)라 서울 행만 남긴 파일을 쓴다.
같은 시군구 코드가 존재 · 폐지 둘 다 있으면 존재 쪽 이름을 쓴다. 다시 넣어도 결과가 같다.
"""

import argparse
import logging
import sys
from pathlib import Path

from sqlalchemy import Connection, Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run

log = logging.getLogger(__name__)

SOURCE = "region"
ENCODING = "cp949"
HEADER = ["법정동코드", "법정동명", "폐지여부"]
DEFAULT_FILE = Path("data/raw/region/legal_dong_codes_seoul.txt")


def parse_sigungu(path: Path) -> dict[str, tuple[str, str]]:
    """시군구 행(코드 뒤 5자리가 00000, 시도 행 제외)만 골라 {코드5: (시도, 시군구)}."""
    lines = path.read_text(encoding=ENCODING).splitlines()
    if lines[0].split("\t") != HEADER:
        raise ValueError(f"법정동코드 파일 헤더가 다르다: {lines[0]!r}")
    result: dict[str, tuple[str, str, bool]] = {}
    for line in lines[1:]:
        code, name, status = line.split("\t")
        if code[5:] != "00000" or code[2:5] == "000":
            continue
        sido, sigungu = name.split(" ", 1)
        alive = status == "존재"
        if code[:5] not in result or (alive and not result[code[:5]][2]):
            result[code[:5]] = (sido, sigungu, alive)
    return {k: (s, g) for k, (s, g, _) in result.items()}


def load_region(conn: Connection, regions: dict[str, tuple[str, str]]) -> int:
    """시군구 코드 5자리 → 시도 · 시군구 이름 upsert."""
    for code, (sido, sigungu) in regions.items():
        conn.execute(
            text("INSERT INTO region (region_code, sido_name, sigungu_name) VALUES (:c, :s, :g)"
                 " ON DUPLICATE KEY UPDATE sido_name = VALUES(sido_name),"
                 " sigungu_name = VALUES(sigungu_name)"),
            {"c": code, "s": sido, "g": sigungu},
        )
    return len(regions)


def run(engine: Engine, path: Path) -> str:
    """같은 파일(체크섬)은 건너뛴다."""
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    try:
        with engine.begin() as conn:
            rows = load_region(conn, parse_sigungu(path))
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", rows)
        log.info("region %s행 적재", rows)
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(sync_engine(), args.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
