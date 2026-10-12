"""메타 응답 스키마 (SPEC 8장)."""

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF


class Formula(BaseModel):
    metric: str
    formula: str
    note: str


class Source(BaseModel):
    name: str
    provider: str
    url: str


class Methodology(BaseModel):
    as_of: int | None = AS_OF
    period_from: int | None = Field(description="국민연금 자료 첫 달 YYYYMM")
    formulas: list[Formula]
    limitations: list[str]
    sources: list[Source]


class Health(BaseModel):
    status: str = "ok"
    db: str = "ok"
    latest_nps_ym: int | None = Field(description="mart에 반영된 국민연금 최신 월")
