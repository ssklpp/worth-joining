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


async def add_dart(db, company_id, *, corp_code="00000001", match_type="exact",
                   score=1, years=None):
    """DART 법인 연결과 재무. years: {연도: (매출, 영업이익, 순이익, 부채, 자본)}."""
    await db.execute(text("INSERT INTO dart_corp (corp_code, corp_name, corp_name_norm)"
                          " VALUES (:c, '가상소프트', '가상소프트')"), {"c": corp_code})
    await db.execute(text("INSERT INTO company_dart_link VALUES (:id, :c, :t, :s)"),
                     {"id": company_id, "c": corp_code, "t": match_type, "s": score})
    for year, (rev, op, net, debt, equity) in (years or {}).items():
        await db.execute(text(
            "INSERT INTO dart_financial VALUES (:c, :y, '11011', :rev, :op, :net, :debt, :eq)"
        ), {"c": corp_code, "y": year, "rev": rev, "op": op, "net": net, "debt": debt,
            "eq": equity})


async def add_location(db, company_id, lon=126.98, lat=37.57, accuracy="building", basis="dart_hq"):
    await db.execute(text(
        "INSERT INTO company_location VALUES (:id, :lon, :lat, :acc, :basis, 'test', NOW())"
    ), {"id": company_id, "lon": lon, "lat": lat, "acc": accuracy, "basis": basis})
