"""메타 API 테스트 (T3-07)."""

from sqlalchemy import text

from tests.api.seed import LATEST, add_company, add_monthly, add_summary


async def test_db_fixture_uses_test_database(db):
    # 개발 DB를 비우는 사고를 막는다
    name = (await db.execute(text("SELECT DATABASE()"))).scalar()

    assert name.endswith("_test")


async def test_health_reports_latest_month(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)

    r = await client.get("/health")

    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "latest_nps_ym": LATEST}


async def test_health_with_empty_mart(client):
    assert (await client.get("/health")).json()["latest_nps_ym"] is None


async def test_methodology(client, db):
    await add_company(db, 1, "가나")
    await add_summary(db, 1)
    await add_monthly(db, 1, [202508, 202608])

    body = (await client.get("/meta/methodology")).json()

    assert (body["as_of"], body["period_from"]) == (LATEST, 202508)
    assert "추정 연봉" in [f["metric"] for f in body["formulas"]]
    assert body["limitations"] and body["sources"]
