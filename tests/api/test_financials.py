"""재무 API · 상세 dart 필드 테스트 (Phase 5-5, FR-COMP-08)."""

from tests.api.seed import LATEST, add_company, add_dart, add_summary

YEARS = {year: (1000 + year, 100, 50, 300, 200) for year in range(2020, 2026)}


async def test_financials_latest_five_years_with_debt_ratio(client, db):
    await add_company(db, 1, "가상소프트")
    await add_dart(db, 1, years=YEARS | {2025: (5000, -10, -20, 300, 0)})

    body = (await client.get("/companies/1/financials")).json()

    assert body["as_of"] is None  # mart가 비어 있다
    assert body["flags"] == []
    assert body["dart"] == {"corp_code": "00000001", "corp_name": "가상소프트",
                            "match_type": "exact"}
    assert [r["year"] for r in body["rows"]] == [2025, 2024, 2023, 2022, 2021]
    assert body["rows"][0] == {"year": 2025, "revenue": 5000, "operating_income": -10,
                               "net_income": -20, "debt_ratio": None}  # 자본 0
    assert body["rows"][1]["debt_ratio"] == 1.5


async def test_financials_years_param_and_fuzzy_flag(client, db):
    await add_company(db, 1, "가상소프트")
    await add_summary(db, 1)
    await add_dart(db, 1, match_type="fuzzy", score=0.9, years=YEARS)

    body = (await client.get("/companies/1/financials", params={"years": 2})).json()

    assert body["as_of"] == LATEST
    assert body["flags"] == ["name_matched"]
    assert [r["year"] for r in body["rows"]] == [2025, 2024]


async def test_fuzzy_full_score_has_no_name_matched_flag(client, db):
    await add_company(db, 1, "엘지디스플레이")
    await add_dart(db, 1, match_type="fuzzy", score=1)

    assert (await client.get("/companies/1/financials")).json()["flags"] == []


async def test_financials_without_link(client, db):
    await add_company(db, 1, "가상소프트")

    body = (await client.get("/companies/1/financials")).json()

    assert (body["dart"], body["rows"], body["flags"]) == (None, [], [])


async def test_financials_errors(client):
    assert (await client.get("/companies/999/financials")).status_code == 404
    assert (await client.get("/companies/1/financials", params={"years": 6})).status_code == 422


async def test_detail_includes_dart_link(client, db):
    await add_company(db, 1, "가상소프트")
    await add_summary(db, 1)
    await add_company(db, 2, "다른회사")
    await add_summary(db, 2)
    await add_dart(db, 1)

    linked = (await client.get("/companies/1")).json()
    unlinked = (await client.get("/companies/2")).json()

    assert linked["dart"]["match_type"] == "exact"
    assert unlinked["dart"] is None
