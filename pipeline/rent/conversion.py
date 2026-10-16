"""한국부동산원 전월세전환율(시도, 연립다세대, 월) → conversion_rate
(SPEC Phase 9-8, decisions/007 · 010).

python -m pipeline.rent.conversion [--file data/raw/rent/conversion_rate_seoul.csv --sido 11]

R-ONE에서 내려받은 CSV(CP949). 1행은 "No, 지역, (지역,) 2024년 9월, ...", 2행은 항목 이름,
3행부터 지역별 값(%)이다. 서울 파일은 "지역" 열이 두 개(시도, 권역), 경기 파일은 하나다.
시도 전체 행("지역" 열이 모두 시도 이름)만 쓰고 %를 소수로 바꾼다(4.6 → 0.046).
권역별 값과 오피스텔 전환율은 쓰지 않는다(docs/profiling.md 13장). 값이 없는 최근 달은 q5가
가장 가까운 이전 달 값을 쓴다. (sido, ym)으로 upsert하므로 다시 넣어도 같다.
--file을 주지 않으면 FILES의 파일 중 있는 것을 모두 넣는다(서울 11, 경기 41).
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
# 시도 코드 → (파일, 파일 안의 시도 이름)
FILES = {"11": (Path("data/raw/rent/conversion_rate_seoul.csv"), "서울"),
         "41": (Path("data/raw/rent/conversion_rate_gyeonggi.csv"), "경기")}
MONTH = re.compile(r"^(\d{4})년\s*(\d{1,2})월$")


def parse(lines, region: str = "서울") -> dict[int, Decimal]:
    """CSV 줄 → {YYYYMM: 연 이율(소수)}. region은 파일 안의 시도 이름("서울", "경기")."""
    rows = list(csv.reader(lines))
    months = [MONTH.match(c.strip()) for c in rows[0]]
    names = [i for i, c in enumerate(rows[0]) if c.strip() == "지역"]
    total = next((r for r in rows[2:] if len(r) > max(names)
                  and all(r[i].strip() == region for i in names)), None)
    if total is None:
        raise ValueError(f"전환율 파일에 {region} 전체 행이 없다")
    rates = {}
    for m, value in zip(months, total, strict=False):
        if m and value.strip():
            rates[int(m.group(1)) * 100 + int(m.group(2))] = Decimal(value.strip()) / 100
    if not rates:
        raise ValueError("전환율 파일에서 월 열을 찾지 못했다")
    return rates


def run(engine: Engine, path: Path, sido: str = "11") -> str:
    """같은 파일(체크섬)은 건너뛴다. 그 시도의 월별 전환율(% → 소수)을 upsert."""
    checksum = file_checksum(path)
    with engine.begin() as conn:
        if already_succeeded(conn, SOURCE, checksum):
            finish_run(conn, start_run(conn, SOURCE, path.name, checksum), "skipped",
                       message="같은 체크섬이 이미 success")
            return "skipped"
        run_id = start_run(conn, SOURCE, path.name, checksum)
    try:
        with path.open(encoding="cp949", newline="") as fh:
            rates = parse(fh, dict(FILES)[sido][1])
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO conversion_rate (sido, ym, rate_year) VALUES (:sido, :ym, :rate)"
                " ON DUPLICATE KEY UPDATE rate_year = VALUES(rate_year)"
            ), [{"sido": sido, "ym": ym, "rate": rate} for ym, rate in sorted(rates.items())])
        with engine.begin() as conn:
            finish_run(conn, run_id, "success", len(rates), f"{min(rates)} ~ {max(rates)}")
        log.info("conversion_rate %s %s개월 (%s ~ %s)", sido, len(rates), min(rates), max(rates))
        return "success"
    except Exception as e:
        with engine.begin() as conn:
            finish_run(conn, run_id, "failed", message=str(e))
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="한 파일만 넣을 때. --sido와 함께")
    parser.add_argument("--sido", choices=sorted(FILES), default="11")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = sync_engine()
    targets = ([(args.file, args.sido)] if args.file
               else [(path, sido) for sido, (path, _) in FILES.items() if path.exists()])
    for path, sido in targets:
        run(engine, path, sido)
    return 0


if __name__ == "__main__":
    sys.exit(main())
