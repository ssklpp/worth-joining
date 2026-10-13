"""지도 조회 SQL(sql/q_map_*.sql). mart_company_summary · company · company_location만 읽는다."""

import time

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.repositories.companies import SQL_DIR

MAP = text((SQL_DIR / "q_map_companies.sql").read_text(encoding="utf-8"))
UNGEOCODED = text((SQL_DIR / "q_map_ungeocoded.sql").read_text(encoding="utf-8"))
LIMIT = 200
# ungeocoded_count는 업종 · 지역에만 달려 있고(bbox와 무관) 다시 적재하기 전에는 바뀌지 않는다.
# 지도를 옮길 때마다 summary 전체(12.6만 행)를 세지 않도록 짧게 기억한다(docs/performance.md)
CACHE_SECONDS = 600
_ungeocoded_cache: dict[tuple[str | None, str | None], tuple[float, int]] = {}


async def companies(conn: AsyncConnection, *, industry: str | None, region: str | None,
                    bbox: tuple[float, float, float, float] | None) -> list[RowMapping]:
    min_lon, min_lat, max_lon, max_lat = bbox or (None, None, None, None)
    return list((await conn.execute(MAP, {
        "industry": industry, "region": region, "min_lon": min_lon, "min_lat": min_lat,
        "max_lon": max_lon, "max_lat": max_lat,
    })).mappings())


async def ungeocoded(conn: AsyncConnection, *, industry: str | None, region: str | None) -> int:
    key, now = (industry, region), time.monotonic()
    hit = _ungeocoded_cache.get(key)
    if hit and hit[0] > now:
        return hit[1]
    count = (await conn.execute(UNGEOCODED, {"industry": industry, "region": region})).scalar_one()
    _ungeocoded_cache[key] = (now + CACHE_SECONDS, count)
    return count


def clear_cache() -> None:
    _ungeocoded_cache.clear()
