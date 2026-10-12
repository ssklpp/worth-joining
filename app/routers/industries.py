from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import companies as company_repo
from app.repositories import industries as repo
from app.schemas.industry import Distribution, IndustryItem, IndustryList, Metric

router = APIRouter(prefix="/industries", tags=["industries"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]


@router.get("", response_model=IndustryList, summary="업종 목록")
async def list_industries(
    conn: Conn, q: str | None = Query(None, max_length=50, description="업종 이름 일부"),
) -> IndustryList:
    """회사가 있는 업종만, 회사 수가 많은 순."""
    rows = await repo.list_industries(conn, q.strip() if q and q.strip() else None)
    return IndustryList(as_of=await company_repo.latest_ym(conn),
                        items=[IndustryItem(**r) for r in rows])


@router.get("/{code}/distribution", response_model=Distribution, summary="업종 내 분포")
async def industry_distribution(
    conn: Conn, code: Annotated[str, Path(pattern=r"^\d{6}$")], metric: Metric = "salary",
) -> Distribution:
    """표본 부족(가입자 10명 미만) 회사를 뺀 p25 · p50 · p75. 비율은 소수, 연봉은 원."""
    industry = await repo.get_industry(conn, code)
    if industry is None:
        raise HTTPException(404, "업종을 찾을 수 없다")
    d = await repo.distribution(conn, code, metric)
    return Distribution(as_of=await company_repo.latest_ym(conn), code=code,
                        name=industry["name"], metric=metric, n=d["n"],
                        **{k: None if d[k] is None else float(d[k]) for k in ("p25", "p50", "p75")})
