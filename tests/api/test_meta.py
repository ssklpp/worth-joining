"""메타 API 테스트 (T3-07)."""

from sqlalchemy import text

from tests.api.seed import LATEST, add_company, add_dart, add_location, add_monthly, add_summary


async def test_db_fixture_uses_test_database(db):
    # 개발 DB를 비우는 사고를 막는다
    name = (await db.execute(text("SELECT DATABASE()"))).scalar()

    assert name.endswith("_test")


async def test_health_reports_latest_month(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)

    r = await client.get("/health")

    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "latest_nps_ym": LATEST, "latest_rent_ym": None,
                        "match_rate": None, "geocode_success_rate": 0.0}
    assert "cache-control" not in r.headers  # 배포 상태 확인은 캐시하지 않는다


async def test_health_quality_rates(client, db):
    for i in (1, 2, 3, 4):
        await add_company(db, i, f"회사{i}")
        await add_summary(db, i, members=1500 if i <= 2 else 20)
    await add_dart(db, 1)
    await add_location(db, 1)
    await add_location(db, 3, accuracy="dong", basis="dong")

    body = (await client.get("/health")).json()

    assert body["match_rate"] == 0.5  # 1,000명 이상 2곳 중 1곳
    assert body["geocode_success_rate"] == 0.5  # 4곳 중 2곳


async def test_health_with_empty_mart(client):
    body = (await client.get("/health")).json()
    assert body["latest_nps_ym"] is None and body["match_rate"] is None


async def test_get_responses_have_cache_headers_and_etag(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)

    first = await client.get("/companies/1")
    again = await client.get("/companies/1", headers={"If-None-Match": first.headers["etag"]})
    missing = await client.get("/companies/999")

    assert first.headers["cache-control"] == "public, max-age=3600"
    assert first.headers["etag"].startswith('W/"')
    assert again.status_code == 304 and again.content == b""
    assert "etag" not in missing.headers  # 오류 응답은 캐시하지 않는다


async def test_methodology(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)
    await add_monthly(db, 1, [202508, 202608])

    body = (await client.get("/meta/methodology")).json()

    assert (body["as_of"], body["period_from"]) == (LATEST, 202508)
    assert "추정 연봉" in [f["metric"] for f in body["formulas"]]
    assert body["limitations"] and body["sources"]
