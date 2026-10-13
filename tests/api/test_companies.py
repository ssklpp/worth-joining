"""회사 API 테스트 (T3-04 · 05 · 06). mart 행을 테스트 트랜잭션에 직접 넣고 롤백한다."""

import pytest

from tests.api.seed import LATEST, add_company, add_location, add_monthly, add_summary


async def test_search_normalizes_query_prefix(client, db):
    await add_company(db, 1, "(주)가나소프트")
    await add_company(db, 2, "다라소프트")
    await add_summary(db, 1)
    await add_summary(db, 2)

    r = await client.get("/companies", params={"q": "주식회사 가나"})

    body = r.json()
    assert r.status_code == 200
    assert body["as_of"] == LATEST
    assert [i["company_id"] for i in body["items"]] == [1]
    assert body["items"][0]["industry"] == {"code": "620100", "name": "컴퓨터 프로그래밍 서비스업"}
    assert body["items"][0]["region"] == {"sido": "서울특별시", "sigungu": "강남구"}
    assert body["next_cursor"] is None


async def test_search_with_no_match_returns_empty(client, db):
    await add_company(db, 1, "가나소프트")
    await add_summary(db, 1)

    for q in ("없는회사", "(주)"):  # (주)만 있으면 정규화 후 빈 문자열
        body = (await client.get("/companies", params={"q": q})).json()
        assert body["items"] == [] and body["next_cursor"] is None


async def test_search_excludes_stale_company(client, db):
    await add_company(db, 1, "가나소프트")  # summary 없음

    body = (await client.get("/companies", params={"q": "가나"})).json()

    assert body["items"] == []


@pytest.mark.parametrize("sort", ["name", "growth"])
async def test_pagination_has_no_duplicates_or_gaps(client, db, sort):
    # growth가 같은 회사와 NULL인 회사를 섞어 동점 처리와 NULL 위치를 확인한다
    growths = [0.5, 0.1, 0.1, 0.1, None, -0.2, 0.1]
    for cid, g in enumerate(growths, start=1):
        await add_company(db, cid, f"회사{cid:02d}")
        await add_summary(db, cid, growth=g)

    seen, cursor = [], None
    while True:
        params = {"sort": sort, "limit": 2} | ({"cursor": cursor} if cursor else {})
        body = (await client.get("/companies", params=params)).json()
        seen += [i["company_id"] for i in body["items"]]
        cursor = body["next_cursor"]
        if cursor is None:
            break

    expected = ([1, 2, 3, 4, 5, 6, 7] if sort == "name" else [1, 2, 3, 4, 7, 6, 5])
    assert seen == expected


async def test_last_page_exactly_full_has_no_cursor(client, db):
    for cid in (1, 2):
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid)

    body = (await client.get("/companies", params={"limit": 2})).json()

    assert len(body["items"]) == 2 and body["next_cursor"] is None


@pytest.mark.parametrize("params", [
    {"limit": 51}, {"limit": 0}, {"cursor": "!!!"}, {"biz_no6": "12345"}, {"sort": "deadline"},
])
async def test_search_invalid_params_return_422(client, params):
    assert (await client.get("/companies", params=params)).status_code == 422


async def test_cursor_from_other_sort_returns_422(client, db):
    for cid in (1, 2):
        await add_company(db, cid, f"회사{cid}")
        await add_summary(db, cid)
    cursor = (await client.get("/companies", params={"limit": 1})).json()["next_cursor"]

    r = await client.get("/companies", params={"sort": "growth", "cursor": cursor})

    assert r.status_code == 422


async def test_detail_ok(client, db):
    await add_company(db, 1, "(주)가나소프트")
    await add_summary(db, 1)

    body = (await client.get("/companies/1")).json()

    assert body["status"] == "ok"
    assert body["name"] == "(주)가나소프트"
    assert body["form_type"] == "corporation"
    assert body["percentiles"] == {"growth": 50, "stability": 60, "salary": 70}
    assert body["flags"] == ["salary_is_lower_bound"]
    assert body["rep_location"] is None


async def test_detail_location(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)
    await add_location(db, 1, lon=126.9, lat=37.5)
    await add_company(db, 2, "다라")
    await add_summary(db, 2)
    await add_location(db, 2, accuracy="dong", basis="dong")

    exact = (await client.get("/companies/1")).json()
    approx = (await client.get("/companies/2")).json()

    assert exact["rep_location"] == {"lon": 126.9, "lat": 37.5,
                                 "accuracy": "building", "basis": "dart_hq"}
    assert "approx_location" not in exact["flags"]
    assert approx["rep_location"]["accuracy"] == "dong"
    assert approx["flags"][-1] == "approx_location"


async def test_detail_small_sample_and_short_history(client, db):
    await add_company(db, 1, "가나", form_type=2)
    await add_summary(db, 1, members=5, small=True, short=True)

    body = (await client.get("/companies/1")).json()

    assert body["form_type"] == "individual"
    assert body["flags"] == ["salary_is_lower_bound", "small_sample", "short_history"]
    assert body["percentiles"] == {"growth": None, "stability": None, "salary": None}


async def test_detail_stale_returns_last_seen_only(client, db):
    await add_company(db, 1, "가나")
    await add_monthly(db, 1, [202604, 202605])
    await add_monthly(db, 1, [202606], members=0)
    await add_company(db, 2, "다라")  # as_of를 위한 최신 회사
    await add_summary(db, 2)

    body = (await client.get("/companies/1")).json()

    assert body == {"company_id": 1, "name": "가나", "as_of": LATEST, "status": "stale",
                    "flags": ["stale"], "last_seen_ym": 202605}


@pytest.mark.parametrize("path, code", [("/companies/999", 404), ("/companies/0", 422),
                                        ("/companies/abc", 422), ("/companies/999/trend", 404)])
async def test_detail_errors(client, path, code):
    assert (await client.get(path)).status_code == code


async def test_trend_filters_period(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1, short=True)
    await add_monthly(db, 1, [202606, 202607, 202608])

    all_points = (await client.get("/companies/1/trend")).json()
    from_only = (await client.get("/companies/1/trend", params={"from_ym": 202607})).json()
    to_only = (await client.get("/companies/1/trend", params={"to_ym": 202607})).json()

    assert [p["ym"] for p in all_points["points"]] == [202606, 202607, 202608]
    assert [p["ym"] for p in from_only["points"]] == [202607, 202608]
    assert [p["ym"] for p in to_only["points"]] == [202606, 202607]
    assert all_points["flags"] == ["salary_is_lower_bound", "short_history"]
    assert all_points["points"][0] == {"ym": 202606, "members": 50, "new": 2, "lost": 1,
                                       "hire_rate": 0.04, "quit_rate": 0.02,
                                       "avg_salary_est": 48000000}


async def test_trend_reversed_period_returns_422(client, db):
    await add_company(db, 1, "가나")

    r = await client.get("/companies/1/trend", params={"from_ym": 202608, "to_ym": 202606})

    assert r.status_code == 422
