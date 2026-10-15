"""역세권 주거비 조회. mart_station_rent · company_station과 작은 조회용 조인
(station, company_location, mart_company_summary)만 읽는다(요청 시점 집계 없음)."""

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection

RENT_COLUMNS = """r.window_months, r.n_monthly, r.n_jeonse, r.monthly_p25, r.monthly_median,
  r.monthly_p75, r.deposit_median_man, r.rent_median_man, r.jeonse_p25_man,
  r.jeonse_median_man, r.jeonse_p75_man"""


async def rent_as_of(conn: AsyncConnection) -> int | None:
    return (await conn.execute(text("SELECT MAX(period_end_ym) FROM mart_station_rent"))).scalar()


async def rents(conn: AsyncConnection, station_ids: list[int],
                radius: int = 500) -> dict[tuple[int, int], RowMapping]:
    """(역, 기간) → 반경 radius(m)의 시세 행."""
    if not station_ids:
        return {}
    rows = (await conn.execute(text(
        f"SELECT r.station_id, {RENT_COLUMNS} FROM mart_station_rent r"
        f" WHERE r.radius_m = :radius"
        f" AND r.station_id IN ({', '.join(str(int(i)) for i in station_ids)})"
    ), {"radius": radius})).mappings().all()
    return {(r["station_id"], r["window_months"]): r for r in rows}


async def company_base(conn: AsyncConnection, company_id: int) -> RowMapping | None:
    """회사 · 요약 · 좌표. company 행이 없으면 None."""
    return (await conn.execute(text("""
        SELECT c.company_id, s.company_id IS NOT NULL AS has_summary, s.avg_salary_est,
               l.accuracy
          FROM company c
          LEFT JOIN mart_company_summary s ON s.company_id = c.company_id
          LEFT JOIN company_location l ON l.company_id = c.company_id
         WHERE c.company_id = :id
    """), {"id": company_id})).mappings().first()


async def near_stations(conn: AsyncConnection, company_id: int) -> list[RowMapping]:
    return list((await conn.execute(text("""
        SELECT st.station_id, st.station_name, st.line_names, cs.distance_m
          FROM company_station cs JOIN station st ON st.station_id = cs.station_id
         WHERE cs.company_id = :id
         ORDER BY cs.rnk
    """), {"id": company_id})).mappings())


async def stations(conn: AsyncConnection, q: str | None, line: str | None,
                   sort: str) -> list[RowMapping]:
    order = "r.monthly_median IS NULL, r.monthly_median, st.station_name" \
        if sort == "monthly_median" else "st.station_name"
    return list((await conn.execute(text(f"""
        SELECT st.station_id, st.station_name, st.line_names,
               ST_Y(st.pt) AS lat, ST_X(st.pt) AS lon,
               r.monthly_median, COALESCE(r.n_monthly, 0) AS n_monthly
          FROM station st
          LEFT JOIN mart_station_rent r ON r.station_id = st.station_id AND r.window_months = 12
                                       AND r.radius_m = 500
         WHERE (:q IS NULL OR st.station_name LIKE CONCAT(:q, '%'))
           AND (:line IS NULL OR FIND_IN_SET(:line, st.line_names) > 0)
         ORDER BY {order}
    """), {"q": q, "line": line})).mappings())


async def station(conn: AsyncConnection, station_id: int) -> RowMapping | None:
    return (await conn.execute(text(
        "SELECT station_id, station_name, line_names, ST_Y(pt) AS lat, ST_X(pt) AS lon"
        " FROM station WHERE station_id = :id"
    ), {"id": station_id})).mappings().first()


async def trend(conn: AsyncConnection, station_id: int, end_ym: int,
                radius: int = 500) -> list[RowMapping]:
    """기준월 · 반경의 월 · 분기 추이 행(grain, ym 순)."""
    return list((await conn.execute(text("""
        SELECT grain, ym, n_monthly, monthly_p25, monthly_median, monthly_p75, n_jeonse,
               jeonse_median_man
          FROM mart_station_rent_trend
         WHERE station_id = :id AND period_end_ym = :end AND radius_m = :radius
         ORDER BY grain, ym
    """), {"id": station_id, "end": end_ym, "radius": radius})).mappings())
