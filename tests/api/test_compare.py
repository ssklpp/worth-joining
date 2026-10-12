"""비교 API 테스트 (T3-10, FR-CMP-01 · 02). 12개월 전 = 100 지수."""

import pytest
from sqlalchemy import text

from tests.api.seed import LATEST, add_company, add_summary

MONTHS = [202508 + i for i in range(5)] + [202601 + i for i in range(8)]  # 202508 ~ 202608, 13개월


async def add_members(db, company_id, members_by_ym):
    for ym, members in members_by_ym.items():
        await db.execute(text(
            "INSERT INTO mart_company_monthly VALUES (:id, :ym, :m, 1, 1, NULL, NULL, 40000000)"
        ), {"id": company_id, "ym": ym, "m": members})


async def test_index_is_100_at_twelve_months_ago(client, db):
    await add_company(db, 1, "가나소프트")
    await add_summary(db, 1)
    await add_members(db, 1, {ym: 50 + i * 5 for i, ym in enumerate(MONTHS)})  # 50 → 110

    body = (await client.get("/compare", params={"ids": "1"})).json()

    item = body["items"][0]
    assert body["as_of"] == LATEST
    assert item["status"] == "ok"
    assert item["industry"]["code"] == "620100"
    assert [p["ym"] for p in item["index_series"]] == MONTHS
    assert item["index_series"][0] == {"ym": 202508, "members": 50, "idx": 100.0}
    assert item["index_series"][-1] == {"ym": 202608, "members": 110, "idx": 220.0}


async def test_short_history_has_null_index_and_keeps_request_order(client, db):
    await add_company(db, 1, "가나소프트")
    await add_summary(db, 1)
    await add_members(db, 1, {ym: 40 for ym in MONTHS})
    await add_company(db, 2, "다라랩")
    await add_summary(db, 2, short=True)
    await add_members(db, 2, {202606: 10, 202607: 12, 202608: 15})

    body = (await client.get("/compare", params={"ids": "2,1"})).json()

    assert [i["company_id"] for i in body["items"]] == [2, 1]
    short = body["items"][0]
    assert "short_history" in short["flags"]
    assert [p["idx"] for p in short["index_series"]] == [None, None, None]
    assert body["items"][1]["index_series"][-1]["idx"] == 100.0


async def test_stale_company_is_listed_with_flag(client, db):
    await add_company(db, 1, "가나소프트")
    await add_summary(db, 1)
    await add_members(db, 1, {ym: 40 for ym in MONTHS})
    await add_company(db, 9, "옛회사")
    await add_members(db, 9, {202508: 30, 202509: 20})

    body = (await client.get("/compare", params={"ids": "1,9"})).json()

    stale = body["items"][1]
    assert (stale["status"], stale["flags"], stale["members"]) == ("stale", ["stale"], None)
    assert [p["ym"] for p in stale["index_series"]] == [202508, 202509]


async def test_unknown_id_returns_404(client, db):
    await add_company(db, 1, "가나소프트")

    r = await client.get("/compare", params={"ids": "1,999"})

    assert r.status_code == 404
    assert "999" in r.json()["detail"]


@pytest.mark.parametrize("ids", ["", "1,2,3,4", "1,1", "0", "a,b", "1,,2", "1 2"])
async def test_invalid_ids_return_422(client, ids):
    assert (await client.get("/compare", params={"ids": ids})).status_code == 422
