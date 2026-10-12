from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import companies, industries, meta

app = FastAPI(
    title="다닐만한가 API",
    description="서울특별시 사업장의 국민연금 공개 자료로 만든 회사 지표. 읽기 전용. "
    "비율은 소수(0.183 = 18.3%), 연봉은 원(하한 추정치).",
    version="0.1.0",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"])
app.include_router(companies.router)
app.include_router(industries.router)
app.include_router(meta.router)
