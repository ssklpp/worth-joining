from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import companies as repo
from app.schemas.common import Industry, Region
from app.schemas.compare import CompareItem, CompareResult, IndexPoint
from app.services.flags import company_flags

router = APIRouter(tags=["compare"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]


def _num(value):
    return None if value is None else float(value)


@router.get("/compare", response_model=CompareResult, summary="회사 비교")
async def compare(
    conn: Conn,
    ids: str = Query(pattern=r"^[1-9]\d{0,9}(,[1-9]\d{0,9}){0,2}$",
                     description="회사 ID를 쉼표로 1 ~ 3개. 예: 12,34,56"),
) -> CompareResult:
    """회사별 12개월 전 = 100 가입자 지수와 요약 지표. 없는 ID가 있으면 404."""
    id_list = [int(i) for i in ids.split(",")]
    if len(set(id_list)) != len(id_list):
        raise HTTPException(422, "같은 회사가 두 번 들어 있다")
    summaries = await repo.summaries(conn, id_list)
    missing = [i for i in id_list if i not in summaries]
    if missing:
        raise HTTPException(404, f"회사를 찾을 수 없다: {', '.join(map(str, missing))}")

    series = defaultdict(list)
    for r in await repo.compare_series(conn, id_list):
        series[r["company_id"]].append(
            IndexPoint(ym=r["ym"], members=r["members"], idx=_num(r["idx"])))

    items = []
    for i in id_list:
        s = summaries[i]
        if not s["fresh"]:
            items.append(CompareItem(company_id=i, name=s["name"], status="stale",
                                     flags=company_flags(None), index_series=series[i]))
            continue
        items.append(CompareItem(
            company_id=i, name=s["name"], status="ok", flags=company_flags(s),
            industry=Industry(code=s["industry_code"], name=s["industry_name"]),
            region=Region(sido=s["sido_name"], sigungu=s["sigungu_name"]),
            members=s["members"], growth_12m=_num(s["growth_12m"]),
            quit_rate_12m=_num(s["quit_rate_12m"]), avg_salary_est=s["avg_salary_est"],
            index_series=series[i],
        ))
    return CompareResult(as_of=await repo.latest_ym(conn), items=items)
