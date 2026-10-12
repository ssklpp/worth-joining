"""업종 응답 스키마 (SPEC 8장)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF

Metric = Literal["salary", "quit", "growth"]


class IndustryItem(BaseModel):
    code: str
    name: str
    n_companies: int = Field(description="최신 월에 가입자가 있는 회사 수(표본 부족 포함)")


class IndustryList(BaseModel):
    as_of: int | None = AS_OF
    items: list[IndustryItem]


class Distribution(BaseModel):
    as_of: int | None = AS_OF
    code: str
    name: str
    metric: Metric
    p25: float | None
    p50: float | None
    p75: float | None
    n: int = Field(description="분포에 쓴 회사 수. 가입자 10명 미만 회사는 뺀다")
