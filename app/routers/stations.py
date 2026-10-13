from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import housing as repo
from app.schemas.housing import MonthsParam, StationDetail, StationList, StationListItem
from app.services.housing import pick_rent, pick_trend

router = APIRouter(prefix="/stations", tags=["stations"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]


def _lines(value: str) -> list[str]:
    return value.split(",") if value else []


@router.get("", response_model=StationList, summary="서울 역과 원룸 시세")
async def list_stations(
    conn: Conn,
    q: str | None = Query(None, max_length=50, description="역 이름 앞부분"),
    line: str | None = Query(None, max_length=30, description="노선 이름(예: 2호선)"),
    sort: Literal["name", "monthly_median"] = "name",
) -> StationList:
    """12개월 원룸 환산 월세 중앙값. 원룸 계약이 없는 역은 monthly_median null, n 0."""
    rows = await repo.stations(conn, q or None, line or None, sort)
    return StationList(as_of=await repo.rent_as_of(conn), items=[
        StationListItem(station_id=r["station_id"], name=r["station_name"],
                        lines=_lines(r["line_names"]), lat=float(r["lat"]), lon=float(r["lon"]),
                        monthly_median=r["monthly_median"],
                        n=r["n_monthly"]) for r in rows])


@router.get("/{station_id}/rent", response_model=StationDetail, summary="역 원룸 시세")
async def station_rent(
    conn: Conn, station_id: Annotated[int, Path(ge=1)],
    months: Annotated[MonthsParam, Query(description="6 · 12 · 24개월(docs/04 D7)")] = (
        MonthsParam.m12),
) -> StationDetail:
    """월세 계약이 20건 미만이면 24개월로 넓히고 period_extended_to_24m을 단다.
    trend는 기간과 관계없이 최근 24개월이고, 계약이 적은 역은 분기로 묶는다."""
    st = await repo.station(conn, station_id)
    if st is None:
        raise HTTPException(404, "역을 찾을 수 없다")
    rent, flags = pick_rent(await repo.rents(conn, [station_id]), station_id, int(months))
    total = rent.n_monthly + rent.n_jeonse if rent else 0
    as_of = await repo.rent_as_of(conn)
    grain, points = pick_trend(await repo.trend(conn, station_id, as_of) if as_of else [])
    return StationDetail(
        station_id=station_id, name=st["station_name"], lines=_lines(st["line_names"]),
        lat=float(st["lat"]), lon=float(st["lon"]), as_of=as_of, rent=rent, flags=flags,
        jeonse_share=round(rent.n_jeonse / total, 4) if total else None,
        trend_grain=grain, trend=points)
