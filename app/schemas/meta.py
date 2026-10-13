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
    latest_rent_ym: int | None = Field(None, description="역세권 시세 기준월(신고가 끝난 달)")
    match_rate: float | None = Field(
        None, description="가입자 1,000명 이상 회사 중 DART 법인과 연결된 비율(docs/matching.md)")
    geocode_success_rate: float | None = Field(
        None, description="회사 중 지도 좌표(건물 · 도로 · 동 중심)가 있는 비율(decisions/004)")
