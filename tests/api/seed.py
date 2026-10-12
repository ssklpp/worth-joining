"""API 테스트용 시드. mart 행을 테스트 트랜잭션에 직접 넣는다(롤백된다)."""

from sqlalchemy import text

from pipeline.common.normalize import normalize_name

LATEST = 202608


async def add_company(db, company_id, name, *, form_type=1, biz_no6="123456"):
    await db.execute(text("INSERT INTO company VALUES (:id, :b, :norm, :name)"),
                     {"id": company_id, "b": biz_no6, "norm": normalize_name(name), "name": name})
    await db.execute(text(
        "INSERT INTO workplace (company_id, workplace_name, form_type, industry_code)"
        " VALUES (:id, :name, :f, '620100')"
    ), {"id": company_id, "name": name, "f": form_type})


async def add_summary(db, company_id, *, members=50, growth=0.1, quit=0.12, salary=50_000_000,
                      small=False, short=False, pct=(50, 60, 70), industry="620100"):
    await db.execute(text("""
        INSERT INTO mart_company_summary
          (company_id, industry_code, region_code, workplace_count, latest_ym, members,
           growth_12m, quit_rate_12m, avg_salary_est, pct_growth, pct_stability, pct_salary,
           small_sample, short_history)
        VALUES (:id, :ind, '11680', 1, :ym, :m, :g, :q, :sal, :p1, :p2, :p3, :small, :short)
    """), {"id": company_id, "ind": industry, "ym": LATEST, "m": members, "g": growth, "q": quit,
           "sal": salary, "p1": None if small else pct[0], "p2": None if small else pct[1],
           "p3": None if small else pct[2], "small": small, "short": short})


async def add_monthly(db, company_id, yms, members=50):
    for ym in yms:
        await db.execute(text(
            "INSERT INTO mart_company_monthly VALUES (:id, :ym, :m, 2, 1, 0.04, 0.02, 48000000)"
        ), {"id": company_id, "ym": ym, "m": members})
