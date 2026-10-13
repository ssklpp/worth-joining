"""지도 핀 API 테스트 (T3-10, FR-MAP-01 · 06 · 07)."""

import pytest
from sqlalchemy import text

from tests.api.seed import LATEST, add_company, add_location, add_summary


async def seed_three(db):
    """1 · 2는 좌표 있음(가입자 30 · 80), 3은 좌표 없음."""
    for cid, members in [(1, 30), (2, 80), (3, 50)]:
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid, members=members, growth=0.01 * cid, salary=40_000_000 + cid)
    await add_location(db, 1, lon=126.90, lat=37.50, accuracy="dong", basis="dong")
    await add_location(db, 2, lon=127.05, lat=37.60)


async def test_orders_by_members_and_counts_ungeocoded(client, db):
    await seed_three(db)

    body = (await client.get("/map/companies")).json()

    assert body["as_of"] == LATEST
    assert [i["company_id"] for i in body["items"]] == [2, 1]
    assert (body["items"][1]["accuracy"], body["items"][1]["basis"]) == ("dong", "dong")
    assert body["items"][0]["value"] == pytest.approx(0.02)
    assert (body["truncated"], body["ungeocoded_count"]) == (False, 1)


async def test_metric_selects_value(client, db):
    await seed_three(db)

    salary = (await client.get("/map/companies", params={"metric": "salary"})).json()
    quit = (await client.get("/map/companies", params={"metric": "quit"})).json()

    assert salary["items"][0]["value"] == 40_000_002
    assert quit["items"][0]["value"] == pytest.approx(0.12)


async def test_filters(client, db):
    await seed_three(db)
    await db.execute(text("INSERT INTO region VALUES ('11110', '서울특별시', '종로구')"))
    await db.execute(text("UPDATE mart_company_summary SET region_code = '11110'"
                          " WHERE company_id = 1"))

    by_region = (await client.get("/map/companies", params={"region": "11110"})).json()
    by_sido = (await client.get("/map/companies", params={"region": "11"})).json()
    by_industry = (await client.get("/map/companies", params={"industry": "999999"})).json()
    by_bbox = (await client.get("/map/companies", params={"bbox": "126.8,37.4,127.0,37.55"})).json()

    assert [i["company_id"] for i in by_region["items"]] == [1]
    assert by_region["ungeocoded_count"] == 0  # 회사 3은 강남구
    assert [i["company_id"] for i in by_sido["items"]] == [2, 1]
    assert by_industry["items"] == [] and by_industry["ungeocoded_count"] == 0
    assert [i["company_id"] for i in by_bbox["items"]] == [1]


async def test_more_than_200_is_truncated(client, db):
    for cid in range(1, 202):
        await add_company(db, cid, f"회사{cid:03d}")
        await add_summary(db, cid, members=cid)
        await add_location(db, cid)

    body = (await client.get("/map/companies")).json()

    assert body["truncated"] is True
    assert len(body["items"]) == 200
    assert body["items"][0]["company_id"] == 201  # 가입자 많은 순


@pytest.mark.parametrize("params", [
    {"region": "116"}, {"industry": "62"}, {"metric": "members"},
    {"bbox": "126.8,37.4,127.0"}, {"bbox": "127.0,37.4,126.8,37.6"}, {"bbox": "a,b,c,d"},
])
async def test_invalid_params_return_422(client, params):
    assert (await client.get("/map/companies", params=params)).status_code == 422


async def test_ungeocoded_count_is_cached_per_filter(client, db):
    await add_company(db, 1, "가")
    await add_summary(db, 1)
    first = (await client.get("/map/companies")).json()["ungeocoded_count"]
    await add_location(db, 1)

    cached = (await client.get("/map/companies")).json()["ungeocoded_count"]
    other_filter = (await client.get("/map/companies", params={"region": "11680"})).json()

    assert (first, cached) == (1, 1)  # 다시 적재하기 전에는 바뀌지 않는다고 보고 기억한 값을 쓴다
    assert other_filter["ungeocoded_count"] == 0
