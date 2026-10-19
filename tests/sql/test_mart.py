"""mart SQL 회귀 테스트 (SPEC Phase 3-4, docs/04 D1 · D4 · D6)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from pipeline.refresh_mart import refresh


@pytest.fixture
def conn(pipeline_engine):
    with pipeline_engine.connect() as c:
        trans = c.begin()
        yield c
        trans.rollback()


def seed(conn, company_id, months, industry="620100", dong="1111010100", name=None):
    """회사 1개 · 사업장 1개와 월별 행을 넣는다. months: {ym: (members, billed, new, lost)}."""
    name = name or f"가상{company_id}"
    conn.execute(text("INSERT INTO company VALUES (:id, '123456', :n, :n)"),
                 {"id": company_id, "n": name})
    wp = conn.execute(text(
        "INSERT INTO workplace (company_id, workplace_name, form_type, industry_code,"
        " legal_dong_code) VALUES (:id, :n, 1, :ind, :dong)"
    ), {"id": company_id, "n": name, "ind": industry, "dong": dong}).lastrowid
    for ym, (members, billed, new, lost) in months.items():
        conn.execute(text("INSERT INTO workplace_monthly VALUES (:wp, :ym, :m, :b, :new, :lost)"),
                     {"wp": wp, "ym": ym, "m": members, "b": billed, "new": new, "lost": lost})


def months(start, n, members=20, billed=6_000_000, new=1, lost=1):
    out, ym = {}, start
    for _ in range(n):
        out[ym] = (members, billed, new, lost)
        ym = ym + 1 if ym % 100 < 12 else (ym // 100 + 1) * 100 + 1
    return out


def monthly(conn, company_id, ym):
    return conn.execute(text(
        "SELECT hire_rate, quit_rate, avg_salary_est FROM mart_company_monthly"
        " WHERE company_id = :c AND snapshot_ym = :ym"
    ), {"c": company_id, "ym": ym}).one()


def summary(conn, company_id):
    return conn.execute(text(
        "SELECT * FROM mart_company_summary WHERE company_id = :c"
    ), {"c": company_id}).mappings().one_or_none()


def test_rate_is_null_after_missing_month(conn):
    seed(conn, 1, {202601: (20, 6_000_000, 2, 1), 202603: (20, 6_000_000, 2, 1),
                   202604: (20, 6_000_000, 2, 4)})
    refresh(conn)

    assert monthly(conn, 1, 202603)[:2] == (None, None)  # 202602가 없다
    assert float(monthly(conn, 1, 202604)[1]) == 0.2  # 4 / 20


def test_salary_uses_9_5_percent_from_2026(conn):
    seed(conn, 1, {202512: (10, 1_000_000, 0, 0), 202601: (10, 1_000_000, 0, 0)})
    refresh(conn)

    assert monthly(conn, 1, 202512)[2] == round(1_000_000 / 10 / 0.09 * 12)
    assert monthly(conn, 1, 202601)[2] == round(1_000_000 / 10 / 0.095 * 12)


def test_nine_members_is_small_sample_without_percentiles(conn):
    seed(conn, 1, months(202508, 13, members=9))
    seed(conn, 2, months(202508, 13, members=50))
    refresh(conn)

    s = summary(conn, 1)
    assert s["small_sample"] == 1
    assert (s["pct_growth"], s["pct_stability"], s["pct_salary"]) == (None, None, None)
    assert summary(conn, 2)["small_sample"] == 0


def test_five_month_history_has_no_growth(conn):
    seed(conn, 1, months(202604, 5))
    seed(conn, 2, months(202508, 13))
    refresh(conn)

    s = summary(conn, 1)
    assert (s["growth_12m"], s["pct_growth"], s["short_history"]) == (None, None, 1)
    assert summary(conn, 2)["short_history"] == 0


def test_company_missing_in_latest_month_is_removed_on_next_refresh(conn):
    seed(conn, 1, months(202606, 2))  # 202606 ~ 202607
    refresh(conn)
    assert summary(conn, 1) is not None

    seed(conn, 2, months(202606, 3))  # 202608까지 → 회사 1은 최신 월에 없다
    refresh(conn)

    assert summary(conn, 1) is None
    assert summary(conn, 2) is not None


def test_zero_members_in_latest_month_has_no_summary(conn):
    seed(conn, 1, {202607: (10, 3_000_000, 0, 0), 202608: (0, 0, 0, 10)})
    seed(conn, 2, months(202607, 2))
    refresh(conn)

    assert summary(conn, 1) is None
    assert float(monthly(conn, 1, 202608)[1]) == 1.0  # 탈퇴한 달의 퇴사는 월별에 남는다


def test_small_sample_does_not_shift_industry_percentiles(conn):
    seed(conn, 1, months(202508, 13, members=50, billed=10_000_000))
    seed(conn, 2, months(202508, 13, members=50, billed=20_000_000))
    seed(conn, 3, months(202508, 13, members=3, billed=9_000_000))  # 1인당 최고지만 표본 부족
    refresh(conn)

    assert (summary(conn, 1)["pct_salary"], summary(conn, 2)["pct_salary"]) == (0, 100)
    assert summary(conn, 3)["pct_salary"] is None


def test_percentiles_are_per_industry(conn):
    seed(conn, 1, months(202508, 13, billed=10_000_000), industry="620100")
    seed(conn, 2, months(202508, 13, billed=20_000_000), industry="620100")
    seed(conn, 3, months(202508, 13, billed=1_000_000), industry="471000")
    refresh(conn)

    assert summary(conn, 3)["pct_salary"] == 0  # 업종 안에 혼자
    assert summary(conn, 2)["pct_salary"] == 100


def test_unclassified_industry_has_no_percentiles(conn):
    # 999999는 국민연금 원본에 업종 분류가 없는 회사 묶음이다.
    # 서로 다른 업종끼리라 백분위가 뜻이 없다(I-01)
    seed(conn, 1, months(202508, 13, billed=10_000_000), industry="999999")
    seed(conn, 2, months(202508, 13, billed=20_000_000), industry="999999")
    seed(conn, 3, months(202508, 13, billed=15_000_000), industry="620100")
    refresh(conn)

    for company_id in (1, 2):
        s = summary(conn, company_id)
        assert (s["pct_growth"], s["pct_stability"], s["pct_salary"]) == (None, None, None)
        assert s["avg_salary_est"] is not None and s["small_sample"] == 0  # 지표 자체는 그대로
    assert summary(conn, 3)["pct_salary"] == 0  # 다른 업종 분포에는 영향 없음


def test_refresh_twice_gives_same_rows(conn):
    seed(conn, 1, months(202508, 13))
    seed(conn, 2, months(202510, 11, members=9))
    all_rows = text("SELECT * FROM mart_company_summary ORDER BY company_id")
    first = refresh(conn)
    rows1 = conn.execute(all_rows).all()

    assert refresh(conn) == first
    assert conn.execute(all_rows).all() == rows1


# SPEC 5.3 MariaDB 주의사항이 11.4에서도 성립하는지 (DDL은 암묵 커밋이라 롤백 없이 만들고 지운다)


@pytest.fixture
def ddl(pipeline_engine):
    with pipeline_engine.connect() as c:
        yield c
        c.execute(text("DROP TABLE IF EXISTS t_caveat_char, t_caveat_part"))


def test_generated_column_from_char_is_rejected(ddl):
    with pytest.raises(OperationalError) as e:
        ddl.execute(text("CREATE TABLE t_caveat_char (src CHAR(10),"
                         " g CHAR(6) AS (LEFT(src, 6)) PERSISTENT)"))
    assert e.value.orig.args[0] == 1901


def test_partition_key_must_be_in_unique_keys(ddl):
    with pytest.raises(OperationalError) as e:
        ddl.execute(text("CREATE TABLE t_caveat_part (id INT, ym INT, UNIQUE KEY (id))"
                         " PARTITION BY RANGE (ym) (PARTITION p VALUES LESS THAN MAXVALUE)"))
    assert e.value.orig.args[0] == 1503
