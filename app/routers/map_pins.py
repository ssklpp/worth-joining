"""지도 핀 API(SPEC 8장 /map/companies, Phase 8). 좌표가 있는 회사만, 가입자 많은 순 최대 200곳."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.db import get_conn
from app.repositories import companies as company_repo
from app.repositories import map_pins as repo
from app.schemas.map import MapCompanies, MapCompany, MapMetric

router = APIRouter(tags=["map"])
Conn = Annotated[AsyncConnection, Depends(get_conn)]
VALUE = {"growth": "growth_12m", "quit": "quit_rate_12m", "salary": "avg_salary_est"}


def _num(value):
    return None if value is None else float(value)


def parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    """min_lon,min_lat,max_lon,max_lat" → 숫자 4개. 형식이 틀리거나 최솟값이 최댓값보다 크면 422.
    """
    if bbox is None:
        return None
    try:
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
    except ValueError as e:
        raise HTTPException(422, "bbox는 min_lon,min_lat,max_lon,max_lat 숫자 4개다") from e
    if not (min_lon < max_lon and min_lat < max_lat):
        raise HTTPException(422, "bbox의 최소값이 최대값보다 작아야 한다")
    return min_lon, min_lat, max_lon, max_lat


@router.get("/map/companies", response_model=MapCompanies, summary="지도 핀")
async def map_companies(
    conn: Conn,
    industry: str | None = Query(None, pattern=r"^\d{6}$", description="업종 코드 6자리"),
    region: str | None = Query(None, pattern=r"^\d{2}(\d{3})?$",
                               description="시도 2자리 또는 시군구 5자리"),
    metric: MapMetric = "growth",
    bbox: str | None = Query(None, description="min_lon,min_lat,max_lon,max_lat (WGS84)"),
) -> MapCompanies:
    """좌표가 있는 회사 중 가입자 많은 순 최대 200곳. 넘으면 truncated."""
    box = parse_bbox(bbox)
    rows = await repo.companies(conn, industry=industry, region=region, bbox=box)
    column = VALUE[metric]
    return MapCompanies(
        as_of=await company_repo.latest_ym(conn), metric=metric,
        items=[MapCompany(
            company_id=r["company_id"], name=r["name"], lon=float(r["lon"]), lat=float(r["lat"]),
            accuracy=r["accuracy"], basis=r["basis"], value=_num(r[column]), members=r["members"],
            growth_12m=_num(r["growth_12m"]), quit_rate_12m=_num(r["quit_rate_12m"]),
            avg_salary_est=r["avg_salary_est"],
        ) for r in rows[:repo.LIMIT]],
        truncated=len(rows) > repo.LIMIT,
        ungeocoded_count=await repo.ungeocoded(conn, industry=industry, region=region),
    )
