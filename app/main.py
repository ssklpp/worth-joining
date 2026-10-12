from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine
from app.routers import companies

app = FastAPI(
    title="다닐만한가 API",
    description="서울특별시 사업장의 국민연금 공개 자료로 만든 회사 지표. 읽기 전용. "
    "비율은 소수(0.183 = 18.3%), 연봉은 원(하한 추정치).",
    version="0.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"])
app.include_router(companies.router)


@app.get("/health")
async def health() -> dict[str, str]:
    # Phase 0 접속 확인용. as_of 등은 T3-07에서 추가한다.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
