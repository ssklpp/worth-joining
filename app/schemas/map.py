"""지도 응답 스키마 (SPEC 8장 /map/companies, docs/05 3장)."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF

MapMetric = Literal["growth", "quit", "salary"]


class MapCompany(BaseModel):
    company_id: int
    name: str
    lon: float
    lat: float
    accuracy: Literal["building", "road", "dong"] = Field(description="building이 아니면 대략 위치")
    basis: Literal["dart_hq", "name_search", "road", "dong"] = Field(
        description="dart_hq: DART 본사 주소 기준(decisions/004)"
    )
    value: float | None = Field(description="metric으로 고른 값. 비율은 소수, 연봉은 원")
    members: int
    growth_12m: float | None
    quit_rate_12m: float | None
    avg_salary_est: int | None = Field(description="추정 평균 연봉(원, 하한 추정치)")


class MapCompanies(BaseModel):
    as_of: int | None = AS_OF
    metric: MapMetric
    items: list[MapCompany] = Field(description="가입자 많은 순 최대 200곳")
    truncated: bool = Field(description="조건에 맞는 회사가 200곳보다 많다. 범위를 좁히라고 안내")
    ungeocoded_count: int = Field(description="업종 · 지역 조건에 맞지만 좌표가 없어 빠진 회사 수")
