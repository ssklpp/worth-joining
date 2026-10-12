from pydantic import BaseModel, Field


class Industry(BaseModel):
    code: str | None
    name: str | None


class Region(BaseModel):
    sido: str | None
    sigungu: str | None


AS_OF = Field(description="데이터 기준월 YYYYMM. 데이터가 없으면 null")
