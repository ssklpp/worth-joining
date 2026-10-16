"""회사 응답 스키마 (SPEC 8장, docs/05 2장). 비율은 소수(0.183 = 18.3%), 연봉은 원."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF, Industry, Region

Flag = Literal[
    "salary_is_lower_bound", "small_sample", "short_history", "stale",
    "approx_location", "name_matched", "period_extended_to_24m",
]


class CompanyListItem(BaseModel):
    company_id: int
    name: str
    industry: Industry
    region: Region
    members: int
    growth_12m: float | None = Field(description="12개월 증감률. 12개월 전 자료가 없으면 null")
    quit_rate_12m: float | None
    avg_salary_est: int | None = Field(description="추정 평균 연봉(원, 하한 추정치)")
    open_jobs: int | None = Field(
        None, description="진행 중 공고 수. 사람인 연동(Phase 10) 전에는 null"
    )


class CompanyList(BaseModel):
    as_of: int | None = AS_OF
    items: list[CompanyListItem]
    next_cursor: str | None = Field(description="다음 페이지 커서. 마지막 페이지면 null")


class Percentiles(BaseModel):
    growth: int | None
    stability: int | None = Field(description="100 - 퇴사율 백분위")
    salary: int | None


class DartLink(BaseModel):
    corp_code: str
    corp_name: str
    match_type: Literal["exact", "fuzzy", "manual"] = Field(
        description="exact: 사업자번호 6자리 + 이름 일치, fuzzy: 이름 유사도(docs/matching.md)"
    )


class Location(BaseModel):
    lon: float
    lat: float
    accuracy: Literal["building", "road", "dong"] = Field(description="building이 아니면 대략 위치")
    basis: Literal["dart_hq", "name_search", "road", "dong"] = Field(
        description="dart_hq: DART 본사 주소 기준(decisions/004)"
    )


class CompanyDetail(BaseModel):
    company_id: int
    name: str
    as_of: int | None = AS_OF
    status: Literal["ok", "stale"] = "ok"
    flags: list[Flag]
    # status="stale"이면 아래는 null이고 last_seen_ym만 있다
    last_seen_ym: int | None = Field(None, description="stale일 때 가입자가 있던 마지막 달")
    industry: Industry | None = None
    region: Region | None = None
    form_type: Literal["corporation", "individual"] | None = None
    workplace_count: int | None = None
    members: int | None = None
    growth_12m: float | None = None
    quit_rate_12m: float | None = None
    avg_salary_est: int | None = None
    percentiles: Percentiles | None = Field(
        None, description="서울 · 성남 사업장 중 대표 업종 안 백분위. 표본 부족이면 모두 null"
    )
    dart: DartLink | None = Field(None, description="DART 연결. 연결되지 않았으면 null")
    rep_location: Location | None = Field(
        None, description="지도 위치(company_location). 좌표가 없으면 null"
    )


class TrendPoint(BaseModel):
    ym: int
    members: int
    new: int
    lost: int
    hire_rate: float | None = Field(description="직전 달이 없으면 null")
    quit_rate: float | None
    avg_salary_est: int | None


class CompanyTrend(BaseModel):
    company_id: int
    as_of: int | None = AS_OF
    flags: list[Flag]
    points: list[TrendPoint]


class FinancialRow(BaseModel):
    year: int
    revenue: int | None = Field(description="매출액(금융업은 영업수익), 원")
    operating_income: int | None
    net_income: int | None
    debt_ratio: float | None = Field(description="부채총계 ÷ 자본총계. 자본이 0 이하이면 null")


class CompanyFinancials(BaseModel):
    company_id: int
    as_of: int | None = AS_OF
    flags: list[Flag] = Field(description="이름 유사도(1.0 미만)로 연결했으면 name_matched")
    dart: DartLink | None
    rows: list[FinancialRow] = Field(
        description="사업보고서 기준, 연결 우선 · 없으면 별도. 최근 연도부터"
    )
