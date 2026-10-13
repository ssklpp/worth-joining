"""주거비 · 역 API (SPEC 8장, Phase 9-10 · 12, decisions/007). mart 행을 직접 넣는다."""

import pytest
from sqlalchemy import text

from tests.api.seed import add_company, add_location, add_summary

END = 202608


async def add_station(db, station_id, name, lines="2호선"):
    await db.execute(text(
        "INSERT INTO station (station_id, station_key, station_name, line_names, pt)"
        " VALUES (:id, :n, :n, :l, POINT(127.0, 37.5))"), {"id": station_id, "n": name, "l": lines})


async def add_rent(db, station_id, months, n, median=700_000, jeonse=20_000):
    await db.execute(text("""
        INSERT INTO mart_station_rent
          (station_id, period_end_ym, window_months, n_monthly, n_jeonse, monthly_p25,
           monthly_median, monthly_p75, deposit_median_man, rent_median_man, jeonse_p25_man,
           jeonse_median_man, jeonse_p75_man)
        VALUES (:s, :end, :m, :n, 5, :p25, :p50, :p75, 1000, 60, 15000, :j, 25000)
    """), {"s": station_id, "end": END, "m": months, "n": n, "p25": median - 100_000,
           "p50": median, "p75": median + 100_000, "j": jeonse})


async def link(db, company_id, station_id, distance, rnk):
    await db.execute(text("INSERT INTO company_station VALUES (:c, :s, :d, :r)"),
                     {"c": company_id, "s": station_id, "d": distance, "r": rnk})


async def test_housing_lists_near_stations_with_burden(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1, salary=48_000_000)  # 월 400만 원
    await add_location(db, 1, accuracy="road", basis="road")
    await add_station(db, 10, "가상역", "2호선,9호선")
    await add_station(db, 11, "작은역")
    await add_rent(db, 10, 12, n=50, median=800_000)
    await add_rent(db, 11, 12, n=8)
    await add_rent(db, 11, 24, n=25, median=600_000)
    await link(db, 1, 10, 320, 1)
    await link(db, 1, 11, 900, 2)

    body = (await client.get("/companies/1/housing")).json()

    assert body["rent_as_of"] == END
    assert body["flags"] == ["approx_location", "salary_is_lower_bound"]
    assert body["monthly_pay_est"] == 4_000_000
    first, second = body["stations"]
    assert (first["name"], first["lines"]) == ("가상역", ["2호선", "9호선"])
    assert first["distance_m"] == 320
    assert first["rent"]["months"] == 12 and first["flags"] == []
    assert first["burden"] == {"low": 0.175, "mid": 0.2, "high": 0.225}
    assert second["rent"]["months"] == 24  # 12개월 8건 → 24개월로 넓힘
    assert second["flags"] == ["period_extended_to_24m"]


async def test_housing_small_sample_even_at_24_months_and_missing_rent(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1, salary=None)
    await add_station(db, 10, "한산역")
    await add_station(db, 11, "아파트역")
    await add_rent(db, 10, 12, n=3)
    await add_rent(db, 10, 24, n=7)
    await link(db, 1, 10, 200, 1)
    await link(db, 1, 11, 400, 2)

    body = (await client.get("/companies/1/housing", params={"months": 6})).json()

    assert body["monthly_pay_est"] is None and "salary_is_lower_bound" not in body["flags"]
    first, second = body["stations"]
    assert first["flags"] == ["period_extended_to_24m", "small_sample"]
    assert first["burden"] is None  # 추정 연봉 없음
    assert second["rent"] is None and second["burden"] is None


@pytest.mark.parametrize("path, code", [
    ("/companies/999/housing", 404), ("/companies/1/housing?months=3", 422),
    ("/stations/999/rent", 404), ("/stations/1/rent?months=18", 422),
])
async def test_housing_errors(client, db, path, code):
    await add_company(db, 1, "가나")
    assert (await client.get(path)).status_code == code


async def test_station_list_filters_and_sorts(client, db):
    await add_station(db, 10, "신림", "2호선,신림선")
    await add_station(db, 11, "신촌", "2호선")
    await add_station(db, 12, "강남", "2호선,신분당선")
    await add_rent(db, 10, 12, n=100, median=750_000)
    await add_rent(db, 12, 12, n=400, median=1_060_000)

    by_rent = (await client.get("/stations", params={"sort": "monthly_median"})).json()
    q = (await client.get("/stations", params={"q": "신"})).json()
    line = (await client.get("/stations", params={"line": "신림선"})).json()

    assert by_rent["as_of"] == END
    assert [(i["name"], i["monthly_median"], i["n"]) for i in by_rent["items"]] == [
        ("신림", 750_000, 100), ("강남", 1_060_000, 400), ("신촌", None, 0)]
    assert [i["name"] for i in q["items"]] == ["신림", "신촌"]
    assert [i["name"] for i in line["items"]] == ["신림"]


async def test_station_rent_detail(client, db):
    await add_station(db, 10, "신림")
    await add_rent(db, 10, 6, n=60)
    await add_rent(db, 10, 12, n=100)

    six = (await client.get("/stations/10/rent", params={"months": 6})).json()
    default = (await client.get("/stations/10/rent")).json()

    assert six["rent"]["months"] == 6 and six["flags"] == []
    assert default["rent"]["n_monthly"] == 100
    assert default["jeonse_share"] == pytest.approx(5 / 105, abs=1e-4)
