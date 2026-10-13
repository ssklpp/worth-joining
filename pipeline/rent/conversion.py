"""한국부동산원 전월세전환율(서울, 연립다세대, 월) → conversion_rate
(SPEC Phase 9-8, decisions/007).

python -m pipeline.rent.conversion [--file data/raw/rent/conversion_rate_seoul.csv]

R-ONE에서 내려받은 CSV(CP949). 1행은 "No, 지역, 지역, 2024년 9월, ...", 2행은 항목 이름,
3행부터 지역별 값(%)이다. 서울 전체 행(2 · 3열이 모두 "서울")만 쓰고 %를 소수로 바꾼다(4.6 → 0.046).
권역별 값과 오피스텔 전환율은 쓰지 않는다(docs/profiling.md 13장). 값이 없는 최근 달은 q5가
가장 가까운 이전 달 값을 쓴다. ym으로 upsert하므로 다시 넣어도 같다.
"""

import argparse
import csv
import logging
import re
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import Engine, text

from pipeline.common.db import sync_engine
from pipeline.common.ingestion import already_succeeded, file_checksum, finish_run, start_run

log = logging.getLogger(__name__)

SOURCE = "conversion_rate"
DEFAULT_FILE = Path("data/raw/rent/conversion_rate_seoul.csv")
MONTH = re.compile(r"^(\d{4})년\s*(\d{1,2})월$")


def parse(lines) -> dict[int, Decimal]:
    """CSV 줄 → {YYYYMM: 연 이율(소수)}."""
    rows = list(csv.reader(lines))
    months = [MONTH.match(c.strip()) for c in rows[0]]
    seoul = next((r for r in rows[2:] if len(r) > 2 and r[1].strip() == r[2].strip() == "서울"),
                 None)
    if seoul is None:
        raise ValueError("전환율 파일에 서울 전체 행이 없다")
    rates = {}
    for m, value in zip(months, seoul, strict=False):
        if m and value.strip():
            rates[int(m.group(1)) * 100 + int(m.group(2))] = Decimal(value.strip()) / 100
    if not rates:
        raise ValueError("전환율 파일에서 월 열을 찾지 못했다")
    return rates


def run(engine: Engine, path: Path) -> str:
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    try:
        with path.open(encoding="cp949", newline="") as fh:
            rates = parse(fh)
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO conversion_rate (ym, rate_year) VALUES (:ym, :rate)"
                " ON DUPLICATE KEY UPDATE rate_year = VALUES(rate_year)"
            ), [{"ym": ym, "rate": rate} for ym, rate in sorted(rates.items())])
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", len(rates), f"{min(rates)} ~ {max(rates)}")
        log.info("conversion_rate %s개월 (%s ~ %s)", len(rates), min(rates), max(rates))
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
