"""여러 응답이 함께 쓰는 작은 스키마."""

from pydantic import BaseModel, Field


class Industry(BaseModel):
    """업종(국민연금 업종 코드 6자리). 999999는 분류 없음("BIZ_NO미존재사업장")."""
    code: str | None
    name: str | None


class Region(BaseModel):
    """대표 사업장의 시도 · 시군구 이름."""
    sido: str | None
    sigungu: str | None


AS_OF = Field(description="데이터 기준월 YYYYMM. 데이터가 없으면 null")
