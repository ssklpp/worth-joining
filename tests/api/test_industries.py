"""업종 API 테스트 (T3-05). 분포는 표본 부족 회사를 뺀다(docs/04 D6)."""

import pytest
from sqlalchemy import text

from tests.api.seed import LATEST, add_company, add_summary


async def seed_two_industries(db):
    await db.execute(text("INSERT INTO industry VALUES ('471100', '종합 소매업')"))
    await db.execute(text("INSERT INTO industry VALUES ('000000', '회사 없는 업종')"))
    for cid, ind in [(1, "620100"), (2, "620100"), (3, "471100")]:
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid, industry=ind)


async def test_list_orders_by_company_count_and_hides_empty(client, db):
    await seed_two_industries(db)

    body = (await client.get("/industries")).json()

    assert body["as_of"] == LATEST
    assert body["items"] == [
        {"code": "620100", "name": "컴퓨터 프로그래밍 서비스업", "n_companies": 2},
        {"code": "471100", "name": "종합 소매업", "n_companies": 1},
    ]


async def test_list_filters_by_name_part(client, db):
    await seed_two_industries(db)

    body = (await client.get("/industries", params={"q": "소매"})).json()
    empty = (await client.get("/industries", params={"q": "없는이름"})).json()

    assert [i["code"] for i in body["items"]] == ["471100"]
    assert empty["items"] == []


async def test_distribution_excludes_small_sample(client, db):
    for cid, salary in enumerate([40_000_000, 50_000_000, 60_000_000, 70_000_000, 80_000_000],
                                 start=1):
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid, salary=salary)
    await add_company(db, 9, "작은회사")
    await add_summary(db, 9, members=5, salary=1_000_000_000, small=True)

    body = (await client.get("/industries/620100/distribution")).json()

    assert body == {"as_of": LATEST, "code": "620100", "name": "컴퓨터 프로그래밍 서비스업",
                    "metric": "salary", "p25": 50_000_000, "p50": 60_000_000,
                    "p75": 70_000_000, "n": 5}


async def test_distribution_quit_metric_skips_null(client, db):
    for cid, quit in [(1, 0.1), (2, 0.3), (3, None)]:
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid, quit=quit)

    body = (await client.get("/industries/620100/distribution",
                             params={"metric": "quit"})).json()

    assert (body["p50"], body["n"]) == (pytest.approx(0.2), 2)


async def test_distribution_without_companies_returns_nulls(client):
    body = (await client.get("/industries/620100/distribution")).json()

    assert (body["p25"], body["p50"], body["p75"], body["n"]) == (None, None, None, 0)


@pytest.mark.parametrize("path, code", [
    ("/industries/999999/distribution", 404),
    ("/industries/12345/distribution", 422),
    ("/industries/620100/distribution?metric=members", 422),
])
async def test_distribution_errors(client, path, code):
    assert (await client.get(path)).status_code == code
