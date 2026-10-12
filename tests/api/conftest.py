import httpx
import pytest
from sqlalchemy import text

from app.core.db import get_conn
from app.main import app


@pytest.fixture
async def client(db):
    """테스트 DB 트랜잭션(db)을 라우터 연결로 주입한 클라이언트. 업종 · 시군구 한 개씩 넣어 둔다."""
    async def override():
        yield db

    app.dependency_overrides[get_conn] = override
    await db.execute(text("INSERT INTO industry VALUES ('620100', '컴퓨터 프로그래밍 서비스업')"))
    await db.execute(text("INSERT INTO region VALUES ('11680', '서울특별시', '강남구')"))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
