import httpx
from sqlalchemy import text

from app.main import app


async def test_health_returns_ok():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_db_fixture_uses_test_database(db):
    # 개발 DB를 비우는 사고를 막는다
    name = (await db.execute(text("SELECT DATABASE()"))).scalar()

    assert name.endswith("_test")
