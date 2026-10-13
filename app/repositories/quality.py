"""/health 품질 지표(FR-OPS-05). mart_company_summary · company_dart_link · company_location ·
mart_station_rent만 읽는다. 다시 적재하기 전에는 바뀌지 않으므로 짧게 기억한다
(map_pins와 같은 방식)."""

import time

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection

CACHE_SECONDS = 600
_cache: list[tuple[float, RowMapping]] = []

QUALITY = text("""
    SELECT SUM(s.members >= 1000) AS big,
           SUM(s.members >= 1000 AND d.company_id IS NOT NULL) AS big_linked,
           COUNT(*) AS companies,
           SUM(l.company_id IS NOT NULL) AS located,
           (SELECT MAX(period_end_ym) FROM mart_station_rent) AS latest_rent_ym
      FROM mart_company_summary s
      LEFT JOIN company_dart_link d ON d.company_id = s.company_id
      LEFT JOIN company_location l ON l.company_id = s.company_id
""")


async def quality(conn: AsyncConnection) -> RowMapping:
    now = time.monotonic()
    if _cache and _cache[0][0] > now:
        return _cache[0][1]
    row = (await conn.execute(QUALITY)).mappings().one()
    _cache[:] = [(now + CACHE_SECONDS, row)]
    return row


def clear_cache() -> None:
    _cache.clear()
