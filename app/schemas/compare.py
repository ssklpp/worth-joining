"""비교 응답 스키마 (SPEC 8장 /compare)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF, Industry, Region
from app.schemas.company import Flag


class IndexPoint(BaseModel):
    ym: int
    members: int
    idx: float | None = Field(description="12개월 전 가입자 = 100. 12개월 전 자료가 없으면 null")


class CompareItem(BaseModel):
    company_id: int
    name: str
    status: Literal["ok", "stale"]
    flags: list[Flag]
    industry: Industry | None = None
    region: Region | None = None
    members: int | None = None
    growth_12m: float | None = None
    quit_rate_12m: float | None = None
    avg_salary_est: int | None = Field(None, description="추정 평균 연봉(원, 하한 추정치)")
    index_series: list[IndexPoint] = Field(description="최근 13개월(기준월과 12개월 전 포함)")


class CompareResult(BaseModel):
    as_of: int | None = AS_OF
    items: list[CompareItem] = Field(description="요청한 ids 순서")
