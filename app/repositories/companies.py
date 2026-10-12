"""회사 조회 SQL. mart_*와 작은 조회용 조인(company, industry, region)만 읽는다(SPEC 0장)."""

from pathlib import Path

from sqlalchemy import RowMapping, bindparam, text
from sqlalchemy.ext.asyncio import AsyncConnection

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
COMPARE = text((SQL_DIR / "q_compare.sql").read_text(encoding="utf-8")).bindparams(
    bindparam("ids", expanding=True)
)

LIST_COLUMNS = """
  s.company_id, c.display_name AS name, s.industry_code, i.industry_name,
  r.sido_name, r.sigungu_name, s.members, s.growth_12m, s.quit_rate_12m, s.avg_salary_est
"""
LOOKUPS = """
  LEFT JOIN industry i ON i.industry_code = s.industry_code
  LEFT JOIN region r ON r.region_code = s.region_code
"""
SUMMARY_FIRST = "mart_company_summary s JOIN company c ON c.company_id = s.company_id"
LIST_FROM = f"FROM {SUMMARY_FIRST} {LOOKUPS}"

# 정렬: (SQL 식, 방향, 동점 키, FROM). 같은 값이면 company_id 오름차순. growth가 NULL이면 맨 뒤.
# name은 company.ix_name_prefix(name_norm, PK) 순서대로 읽어 LIMIT에서 멈추도록 조인 순서를
# 고정한다. summary부터 읽으면 12만 행을 정렬해 약 370ms가 걸린다.
SORTS: dict[str, tuple[str, str, str, str]] = {
    "name": ("c.name_norm", "ASC", "c.company_id",
             "company c STRAIGHT_JOIN mart_company_summary s ON s.company_id = c.company_id"),
    "growth": ("COALESCE(s.growth_12m, -1000)", "DESC", "s.company_id", SUMMARY_FIRST),
}


async def latest_ym(conn: AsyncConnection) -> int | None:
    return (await conn.execute(text("SELECT latest_ym FROM mart_company_summary LIMIT 1"))).scalar()


async def search(
    conn: AsyncConnection, *, name_prefix: str | None, biz_no6: str | None,
    industry: str | None, region: str | None, sort: str, limit: int,
    after: tuple[object, int] | None,
) -> list[RowMapping]:
    """키셋 페이지네이션(docs/05 A1). limit + 1행을 돌려줘 다음 페이지가 있는지 알린다."""
    expr, direction, tie, from_ = SORTS[sort]
    where, params = [], {"limit": limit + 1}
    if name_prefix:
        where.append("c.name_norm LIKE :prefix")
        params["prefix"] = name_prefix + "%"
    if biz_no6:
        where.append("c.biz_no6 = :biz_no6")
        params["biz_no6"] = biz_no6
    if industry:
        where.append("s.industry_code = :industry")
        params["industry"] = industry
    if region:
        where.append("s.region_code = :region")
        params["region"] = region
    if after is not None:
        op = ">" if direction == "ASC" else "<"
        where.append(f"({expr} {op} :after_v OR ({expr} = :after_v AND {tie} > :after_id))")
        params["after_v"], params["after_id"] = after
    sql = (
        f"SELECT {LIST_COLUMNS}, {expr} AS sort_value FROM {from_} {LOOKUPS}"
        + (" WHERE " + " AND ".join(where) if where else "")
        + f" ORDER BY {expr} {direction}, {tie} ASC LIMIT :limit"
    )
    return list((await conn.execute(text(sql), params)).mappings())


async def get_company(conn: AsyncConnection, company_id: int) -> RowMapping | None:
    return (await conn.execute(text(
        "SELECT company_id, display_name AS name FROM company WHERE company_id = :id"
    ), {"id": company_id})).mappings().first()


async def get_summary(conn: AsyncConnection, company_id: int) -> RowMapping | None:
    return (await conn.execute(text(f"""
        SELECT {LIST_COLUMNS}, s.workplace_count, s.pct_growth, s.pct_stability, s.pct_salary,
               s.small_sample, s.short_history,
               (SELECT MIN(w.form_type) FROM workplace w
                 WHERE w.company_id = s.company_id) AS form_type
        {LIST_FROM}
        WHERE s.company_id = :id
    """), {"id": company_id})).mappings().first()


async def last_seen_ym(conn: AsyncConnection, company_id: int) -> int | None:
    """가입자가 있던 마지막 달(SPEC 5.2 주석)."""
    return (await conn.execute(text(
        "SELECT MAX(snapshot_ym) FROM mart_company_monthly WHERE company_id = :id AND members > 0"
    ), {"id": company_id})).scalar()


async def trend(
    conn: AsyncConnection, company_id: int, from_ym: int | None, to_ym: int | None
) -> list[RowMapping]:
    return list((await conn.execute(text("""
        SELECT snapshot_ym AS ym, members, new_members AS new, lost_members AS lost,
               hire_rate, quit_rate, avg_salary_est
          FROM mart_company_monthly
         WHERE company_id = :id AND snapshot_ym BETWEEN :from_ym AND :to_ym
         ORDER BY snapshot_ym
    """), {"id": company_id, "from_ym": from_ym or 0, "to_ym": to_ym or 999912})).mappings())


async def dart_link(conn: AsyncConnection, company_id: int) -> RowMapping | None:
    return (await conn.execute(text("""
        SELECT d.corp_code, d.corp_name, l.match_type, l.match_score
          FROM company_dart_link l JOIN dart_corp d ON d.corp_code = l.corp_code
         WHERE l.company_id = :id
    """), {"id": company_id})).mappings().first()


async def financials(conn: AsyncConnection, corp_code: str, years: int) -> list[RowMapping]:
    return list((await conn.execute(text("""
        SELECT bsns_year AS year, revenue, operating_income, net_income,
               total_liabilities / NULLIF(GREATEST(total_equity, 0), 0) AS debt_ratio
          FROM dart_financial
         WHERE corp_code = :c AND reprt_code = '11011'
         ORDER BY bsns_year DESC
         LIMIT :n
    """), {"c": corp_code, "n": years})).mappings())


async def summaries(conn: AsyncConnection, ids: list[int]) -> dict[int, RowMapping]:
    """비교용 요약. 최근 자료 없는(stale) 회사는 summary 컬럼이 NULL이다."""
    rows = (await conn.execute(text("""
        SELECT c.company_id, c.display_name AS name, s.industry_code, i.industry_name,
               r.sido_name, r.sigungu_name, s.members, s.growth_12m, s.quit_rate_12m,
               s.avg_salary_est, s.small_sample, s.short_history, s.company_id IS NOT NULL AS fresh
          FROM company c
          LEFT JOIN mart_company_summary s ON s.company_id = c.company_id
          LEFT JOIN industry i ON i.industry_code = s.industry_code
          LEFT JOIN region r ON r.region_code = s.region_code
         WHERE c.company_id IN :ids
    """).bindparams(bindparam("ids", expanding=True)), {"ids": ids})).mappings()
    return {r["company_id"]: r for r in rows}


async def compare_series(conn: AsyncConnection, ids: list[int]) -> list[RowMapping]:
    return list((await conn.execute(COMPARE, {"ids": ids})).mappings())
