"""업종 조회 SQL. mart_company_summary와 industry만 읽는다."""

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncConnection

# 분포 지표 → summary 컬럼. 사용자 입력을 SQL에 넣지 않도록 고정 매핑만 쓴다
METRICS = {"salary": "avg_salary_est", "quit": "quit_rate_12m", "growth": "growth_12m"}


async def list_industries(conn: AsyncConnection, q: str | None) -> list[RowMapping]:
    """회사가 있는 업종만, 회사 수가 많은 순."""
    return list((await conn.execute(text("""
        SELECT i.industry_code AS code, i.industry_name AS name, n.n_companies
          FROM (SELECT industry_code, COUNT(*) AS n_companies
                  FROM mart_company_summary GROUP BY industry_code) n
          JOIN industry i ON i.industry_code = n.industry_code
         WHERE :q IS NULL OR i.industry_name LIKE CONCAT('%', :q, '%')
         ORDER BY n.n_companies DESC, i.industry_code
    """), {"q": q})).mappings())


async def get_industry(conn: AsyncConnection, code: str) -> RowMapping | None:
    return (await conn.execute(text(
        "SELECT industry_code AS code, industry_name AS name FROM industry WHERE industry_code = :c"
    ), {"c": code})).mappings().first()


async def distribution(conn: AsyncConnection, code: str, metric: str) -> RowMapping:
    """표본 부족 회사를 뺀 업종 분포(docs/04 D6). 회사가 없으면 n = 0, 분위수는 NULL."""
    col = METRICS[metric]
    row = (await conn.execute(text(f"""
        SELECT DISTINCT
               PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY v) OVER () AS p25,
               PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY v) OVER () AS p50,
               PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY v) OVER () AS p75,
               COUNT(*) OVER () AS n
          FROM (SELECT {col} AS v FROM mart_company_summary
                 WHERE industry_code = :c AND NOT small_sample AND {col} IS NOT NULL) t
    """), {"c": code})).mappings().first()
    return row or {"p25": None, "p50": None, "p75": None, "n": 0}
