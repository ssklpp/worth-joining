"""역세권 시세 q5 · 회사 근처 역 q6 (SPEC 7장, Phase 9-9 · 11 · 14, decisions/007).
가상 역 · 건물."""

import math

import pytest
from sqlalchemy import text

from pipeline.refresh_mart import SQL_DIR, refresh

STATION = (127.0, 37.5)
EARTH_M = 6_370_986  # ST_Distance_Sphere 기본 반지름


def north(meters):
    """역에서 북쪽으로 meters 떨어진 점."""
    return STATION[0], STATION[1] + math.degrees(meters / EARTH_M)


@pytest.fixture
def conn(pipeline_engine):
    with pipeline_engine.connect() as c:
        trans = c.begin()
        yield c
        trans.rollback()


def add_station(conn, key="가상역", point=STATION):
    return conn.execute(text(
        "INSERT INTO station (station_key, station_name, line_names, pt)"
        " VALUES (:k, :k, '9호선', POINT(:x, :y))"
    ), {"k": key, "x": point[0], "y": point[1]}).lastrowid


def add_building(conn, key, point, house_type="오피스텔"):
    return conn.execute(text(
        "INSERT INTO building (addr_key, house_type, pt) VALUES (:k, :t, POINT(:x, :y))"
    ), {"k": key, "t": house_type, "x": point[0], "y": point[1]}).lastrowid


def add_contract(conn, building_id, ym, deposit=1000, monthly=60, area=25):
    conn.execute(text(
        "INSERT INTO rent_contract (contract_ym, row_hash, addr_key, building_id, house_type,"
        " area_m2, deposit_man, monthly_man) VALUES (:ym, MD5(UUID()), 'x', :b, '오피스텔',"
        " :area, :dep, :mon)"), {"ym": ym, "b": building_id, "area": area, "dep": deposit,
                                 "mon": monthly})


def report_date(conn, yyyymmdd):
    """기준월은 raw의 마지막 계약일로 정한다(자료 받은 날 - 30일이 속한 달의 전월)."""
    conn.execute(text("INSERT INTO raw_rent_contract (run_id, row_hash, contract_date)"
                      " VALUES (0, MD5(UUID()), :d)"), {"d": yyyymmdd})


def mart(conn, window):
    return conn.execute(text(
        "SELECT period_end_ym, n_monthly, n_jeonse, monthly_median, deposit_median_man,"
        " rent_median_man, jeonse_median_man FROM mart_station_rent WHERE window_months = :n"
    ), {"n": window}).all()


def test_499m_building_counts_and_501m_does_not(conn):
    add_station(conn)
    near = add_building(conn, "near", north(499))
    far = add_building(conn, "far", north(501))
    add_contract(conn, near, 202608)
    add_contract(conn, far, 202608)
    conn.execute(text("INSERT INTO conversion_rate VALUES (202608, 0.0600)"))
    report_date(conn, "20261010")

    refresh(conn)

    assert [r[1] for r in mart(conn, 12)] == [1]


def test_window_boundary_is_greater_than_and_end_is_report_complete_month(conn):
    add_station(conn)
    b = add_building(conn, "b", north(100))
    for ym in (202508, 202509, 202608, 202609):  # 202508은 12개월 밖(>), 202609는 기준월 뒤
        add_contract(conn, b, ym)
    conn.execute(text("INSERT INTO conversion_rate VALUES (202501, 0.0600)"))
    report_date(conn, "20261010")  # 9/10이 속한 9월의 전월 → 202608

    refresh(conn)

    assert [(r[0], r[1]) for r in mart(conn, 12)] == [(202608, 2)]
    assert [r[1] for r in mart(conn, 6)] == [1]
    assert [r[1] for r in mart(conn, 24)] == [3]


def test_converted_rent_uses_latest_rate_and_splits_jeonse(conn):
    add_station(conn)
    b = add_building(conn, "b", north(100))
    add_contract(conn, b, 202608, deposit=1200, monthly=50)  # 8월 전환율이 없어 7월 값 6%
    add_contract(conn, b, 202608, deposit=20000, monthly=0)  # 전세
    add_contract(conn, b, 202608, deposit=500, monthly=40, area=40)  # 33㎡ 초과는 원룸 아님
    conn.execute(text("INSERT INTO conversion_rate VALUES (202607, 0.0600)"))
    report_date(conn, "20261010")

    refresh(conn)

    # (50 + 1200 × 0.06 ÷ 12) × 10000 = 560,000원
    assert mart(conn, 12) == [(202608, 1, 1, 560000, 1200, 50, 20000)]


def test_no_rent_data_skips_station_rent(conn):
    add_station(conn)

    counts = refresh(conn)

    assert "mart_station_rent_12" not in counts and mart(conn, 12) == []


def seed_company(conn, company_id, point):
    conn.execute(text("INSERT INTO company VALUES (:id, '123456', :n, :n)"),
                 {"id": company_id, "n": f"가상{company_id}"})
    conn.execute(text(
        "INSERT INTO mart_company_summary (company_id, industry_code, region_code, workplace_count,"
        " latest_ym, members, small_sample, short_history) VALUES (:id, '620100', '11680', 1,"
        " 202608, 20, 0, 0)"), {"id": company_id})
    conn.execute(text(
        "INSERT INTO company_location VALUES (:id, :x, :y, 'road', 'road', 'road:x', NOW())"
    ), {"id": company_id, "x": point[0], "y": point[1]})


def test_company_gets_nearest_three_stations_within_1km(conn):
    ids = [add_station(conn, f"역{m}", north(m)) for m in (100, 300, 500, 700, 1001)]
    seed_company(conn, 1, STATION)

    conn.execute(text("DELETE FROM company_station"))
    conn.execute(text((SQL_DIR / "q6_company_station.sql").read_text(encoding="utf-8")))

    rows = conn.execute(text(
        "SELECT station_id, distance_m, rnk FROM company_station ORDER BY rnk")).all()
    assert [(r[0], r[2]) for r in rows] == [(ids[0], 1), (ids[1], 2), (ids[2], 3)]
    assert rows[0][1] == 100


def test_station_building_join_uses_spatial_index(conn):
    sql = (SQL_DIR / "q5a_station_building.sql").read_text(encoding="utf-8")
    select = sql[sql.index("SELECT"):]

    plan = conn.execute(text("EXPLAIN " + select)).mappings().all()

    building = next(p for p in plan if p["table"] == "b")
    assert "Range checked for each record" in (building["Extra"] or "")
