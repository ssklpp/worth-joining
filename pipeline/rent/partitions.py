"""rent_contract 월 파티션 만들기 · 지우기 (SPEC 7장 파티션 순환, decisions/007).

python -m pipeline.rent.partitions --upto 202612          # pmax를 나눠 202612까지 월 파티션
python -m pipeline.rent.partitions --drop-before 202409   # 202409보다 앞선 월 파티션 삭제

자동 순환(cron)은 하지 않는다(decisions/007). 적재기가 적재 전에 ensure()를 부르고,
월 갱신 때 runbook대로 --drop-before를 손으로 실행한다. 파티션 DDL은 바로 커밋된다.
"""

import argparse
import logging
import re
import sys

from sqlalchemy import Connection, text

from pipeline.common.db import sync_engine

log = logging.getLogger(__name__)

TABLE = "rent_contract"
NAME = re.compile(r"^p(\d{6})$")


def next_ym(ym: int) -> int:
    return ym + 1 if ym % 100 < 12 else (ym // 100 + 1) * 100 + 1


def months(conn: Connection) -> list[int]:
    """지금 있는 월 파티션(pYYYYMM)의 월, 오름차순. pmax는 빼고 센다."""
    rows = conn.execute(text(
        "SELECT PARTITION_NAME FROM information_schema.PARTITIONS"
        " WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t ORDER BY PARTITION_ORDINAL_POSITION"
    ), {"t": TABLE}).scalars()
    return [int(m.group(1)) for name in rows if (m := NAME.match(name or ""))]


def ensure(conn: Connection, first: int, last: int) -> list[int]:
    """first ~ last의 월 파티션이 있게 pmax를 나눈다. 이미 있는 마지막 달 뒤로만 늘린다.
    파티션은 월 하나가 p{YYYYMM} VALUES LESS THAN (다음 달)이다. 새로 만든 월을 돌려준다."""
    have = months(conn)
    start = next_ym(have[-1]) if have else first
    new, ym = [], start
    while ym <= last:
        new.append(ym)
        ym = next_ym(ym)
    if new:
        parts = ", ".join(f"PARTITION p{m} VALUES LESS THAN ({next_ym(m)})" for m in new)
        conn.execute(text(f"ALTER TABLE {TABLE} REORGANIZE PARTITION pmax INTO"
                          f" ({parts}, PARTITION pmax VALUES LESS THAN MAXVALUE)"))
        log.info("%s 파티션 추가: p%s ~ p%s", TABLE, new[0], new[-1])
    return new


def drop_before(conn: Connection, ym: int) -> list[int]:
    """ym보다 앞선 월 파티션을 지운다(24개월 보관, FR-DATA-07). 지운 월을 돌려준다."""
    old = [m for m in months(conn) if m < ym]
    if old:
        conn.execute(text(f"ALTER TABLE {TABLE} DROP PARTITION " + ", ".join(f"p{m}" for m in old)))
        log.info("%s 파티션 삭제: p%s ~ p%s", TABLE, old[0], old[-1])
    return old


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=int, help="처음 만들 때의 첫 달(파티션이 없을 때만 쓴다)")
    parser.add_argument("--upto", type=int, help="이 달까지 월 파티션을 만든다")
    parser.add_argument("--drop-before", type=int, help="이 달보다 앞선 월 파티션을 지운다")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with sync_engine().connect() as conn:
        if args.upto:
            ensure(conn, args.first or args.upto, args.upto)
        if args.drop_before:
            drop_before(conn, args.drop_before)
    return 0


if __name__ == "__main__":
    sys.exit(main())
