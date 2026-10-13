"""Phase 9 스키마 · rent_contract 월 파티션 (SPEC Phase 9-3 · 14, decisions/007).

파티션 DDL은 바로 커밋되므로 이 파일의 테스트는 롤백 대신 끝날 때 표를 처음 상태로 되돌린다.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from pipeline.rent import partitions

RESET = ("ALTER TABLE rent_contract PARTITION BY RANGE (contract_ym)"
         " (PARTITION pmax VALUES LESS THAN MAXVALUE)")


@pytest.fixture
def conn(pipeline_engine):
    with pipeline_engine.connect() as c:
        yield c
        c.rollback()
        c.execute(text("TRUNCATE TABLE rent_contract"))
        c.execute(text(RESET))


def add(conn, ym, row_hash, addr="11710-10100-1-183-4"):
    conn.execute(text(
        "INSERT INTO rent_contract (contract_ym, row_hash, addr_key, house_type, area_m2,"
        " deposit_man, monthly_man) VALUES (:ym, :h, :a, '오피스텔', 27.07, 1000, 60)"
    ), {"ym": ym, "h": row_hash, "a": addr})
    conn.commit()


def count(conn, where="1=1"):
    return conn.execute(text(f"SELECT COUNT(*) FROM rent_contract WHERE {where}")).scalar()


def test_phase9_tables_exist(conn):
    tables = {r[0] for r in conn.execute(text("SHOW TABLES"))}

    assert {"raw_rent_contract", "station", "building", "rent_contract", "conversion_rate",
            "company_station", "mart_station_rent"} <= tables


def test_ensure_splits_pmax_into_months_and_extends_only_forward(conn):
    assert partitions.ensure(conn, 202411, 202502) == [202411, 202412, 202501, 202502]
    assert partitions.ensure(conn, 202411, 202503) == [202503]  # 있는 달 뒤로만 늘린다
    assert partitions.ensure(conn, 202411, 202502) == []

    assert partitions.months(conn) == [202411, 202412, 202501, 202502, 202503]


def test_drop_partition_keeps_other_months(conn):
    partitions.ensure(conn, 202411, 202501)
    for ym, h in [(202411, "a"), (202412, "b"), (202501, "c"), (202607, "d")]:
        add(conn, ym, h * 32)

    assert partitions.drop_before(conn, 202412) == [202411]

    assert count(conn) == 3
    assert count(conn, "contract_ym = 202411") == 0
    assert count(conn, "contract_ym = 202607") == 1  # pmax에 있던 달도 그대로


def test_same_row_hash_in_same_month_is_rejected(conn):
    add(conn, 202501, "e" * 32)

    with pytest.raises(IntegrityError):
        add(conn, 202501, "e" * 32)
