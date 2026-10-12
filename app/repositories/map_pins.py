"""지도 조회 SQL(sql/q_map_*.sql). mart_company_summary · company · company_location만 읽는다."""

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.repositories.companies import SQL_DIR

MAP = text((SQL_DIR / "q_map_companies.sql").read_text(encoding="utf-8"))
UNGEOCODED = text((SQL_DIR / "q_map_ungeocoded.sql").read_text(encoding="utf-8"))
LIMIT = 200


async def companies(conn: AsyncConnection, *, industry: str | None, region: str | None,
                    bbox: tuple[float, float, float, float] | None) -> list[RowMapping]:
    min_lon, min_lat, max_lon, max_lat = bbox or (None, None, None, None)
    return list((await conn.execute(MAP, {
        "industry": industry, "region": region, "min_lon": min_lon, "min_lat": min_lat,
        "max_lon": max_lon, "max_lat": max_lat,
    })).mappings())


async def ungeocoded(conn: AsyncConnection, *, industry: str | None, region: str | None) -> int:
    return (await conn.execute(UNGEOCODED, {"industry": industry, "region": region})).scalar_one()
