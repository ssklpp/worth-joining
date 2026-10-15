"""FastAPI 앱 진입점(`uvicorn app.main:app`). 미들웨어(CORS · 캐시 헤더)와 라우터를 묶는다.

읽기 전용 API라 GET만 연다(SPEC 8장).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.cache import cache_headers
from app.core.config import settings
from app.routers import companies, compare, industries, map_pins, meta, stations

app = FastAPI(
    title="다닐만한가 API",
    description="서울특별시 사업장의 국민연금 공개 자료로 만든 회사 지표. 읽기 전용. "
    "비율은 소수(0.183 = 18.3%), 연봉은 원(하한 추정치).",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET"],
                   expose_headers=["ETag"])
app.middleware("http")(cache_headers)  # CORS 바깥에서 감싸 304에도 CORS 헤더가 남는다
app.include_router(companies.router)
app.include_router(compare.router)
app.include_router(industries.router)
app.include_router(map_pins.router)
app.include_router(meta.router)
app.include_router(stations.router)
