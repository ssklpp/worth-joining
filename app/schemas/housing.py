"""역세권 주거비 응답 스키마 (SPEC 8장 /companies/{id}/housing · /stations, decisions/007).
금액: 환산 월세 · 월 급여는 원, 보증금 · 월세 · 전세는 만원. 부담률은 소수(0.32 = 32%)."""

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import AS_OF
from app.schemas.company import Flag

Months = Literal[6, 12, 24]


class MonthsParam(IntEnum):
    """쿼리 파라미터 months. 문자열 "6"을 받으려고 Literal 대신 IntEnum을 쓴다."""
    m6 = 6
    m12 = 12
    m24 = 24


class Burden(BaseModel):
    low: float | None = Field(description="환산 월세 p25 ÷ 추정 월급")
    mid: float | None = Field(description="중앙값 ÷ 추정 월급")
    high: float | None = Field(description="p75 ÷ 추정 월급")


class StationRent(BaseModel):
    months: Months = Field(description="실제로 쓴 기간. 계약이 20건 미만이면 24개월로 넓힌다")
    n_monthly: int = Field(description="원룸 월세 계약 수")
    n_jeonse: int
    monthly_p25: int | None = Field(description="환산 월세(원)")
    monthly_median: int | None
    monthly_p75: int | None
    deposit_median_man: int | None = Field(description="월세 계약의 보증금 중앙값(만원)")
    rent_median_man: int | None = Field(description="월세 계약의 월세 중앙값(만원)")
    jeonse_p25_man: int | None
    jeonse_median_man: int | None
    jeonse_p75_man: int | None


class NearStation(BaseModel):
    station_id: int
    name: str
    lines: list[str]
    distance_m: int = Field(description="회사 좌표에서 역까지(대략 위치면 참고용)")
    rent: StationRent | None = Field(description="역 500m 안 원룸 계약이 없으면 null")
    burden: Burden | None = Field(description="추정 연봉이나 시세가 없으면 null")
    flags: list[Flag] = Field(
        description="period_extended_to_24m, small_sample(24개월에도 20건 미만)")


class CompanyHousing(BaseModel):
    company_id: int
    as_of: int | None = AS_OF
    rent_as_of: int | None = Field(description="전월세 집계 기준월(신고가 끝난 달) YYYYMM")
    flags: list[Flag] = Field(description="approx_location, salary_is_lower_bound, stale")
    monthly_pay_est: int | None = Field(description="추정 월급(원) = 추정 연봉 ÷ 12, 하한 추정")
    stations: list[NearStation] = Field(description="회사에서 1km 안의 역, 가까운 순 최대 3곳")


class StationListItem(BaseModel):
    station_id: int
    name: str
    lines: list[str]
    monthly_median: int | None = Field(description="12개월 원룸 환산 월세 중앙값(원)")
    n: int = Field(description="12개월 원룸 월세 계약 수")


class StationList(BaseModel):
    as_of: int | None = Field(description="전월세 집계 기준월 YYYYMM")
    items: list[StationListItem]


class StationTrendPoint(BaseModel):
    ym: int = Field(description="구간의 마지막 달 YYYYMM(분기면 3개월 구간의 끝 달)")
    n_monthly: int
    monthly_p25: int | None = Field(description="환산 월세(원)")
    monthly_median: int | None
    monthly_p75: int | None
    n_jeonse: int
    jeonse_median_man: int | None


class StationDetail(BaseModel):
    station_id: int
    name: str
    lines: list[str]
    lat: float
    lon: float
    as_of: int | None = Field(description="전월세 집계 기준월 YYYYMM")
    rent: StationRent | None
    jeonse_share: float | None = Field(description="원룸 계약 중 전세 비율")
    flags: list[Flag]
    trend_grain: Literal["month", "quarter"] | None = Field(
        description="24개월 모두 월세 5건 이상이면 month, 아니면 quarter. 계약이 없으면 null")
    trend: list[StationTrendPoint] = Field(
        description="기준월까지 최근 24개월(months와 무관), 오래된 순")
