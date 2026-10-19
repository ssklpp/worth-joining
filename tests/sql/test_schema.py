from sqlalchemy import text

EXPECTED_TABLES = {
    "ingestion_log", "api_call_log", "nps_rate", "industry", "region",
    "raw_nps_workplace", "company", "workplace", "workplace_monthly",
}


async def test_initial_tables_exist(db):
    rows = await db.execute(text("SHOW TABLES"))
    tables = {r[0] for r in rows}

    assert EXPECTED_TABLES <= tables


async def test_nps_rate_seed_covers_loaded_months(db):
    rows = (await db.execute(text(
        "SELECT valid_from_ym, valid_to_ym, rate, income_cap FROM nps_rate ORDER BY valid_from_ym"
    ))).all()

    assert [(r[0], r[1], float(r[2]), r[3]) for r in rows] == [
        (202407, 202506, 0.09, 6170000),
        (202507, 202512, 0.09, 6370000),
        (202601, 202606, 0.095, 6370000),
        (202607, 202706, 0.095, 6590000),
    ]


async def test_workplace_monthly_is_partitioned_by_year(db):
    rows = await db.execute(text(
        "SELECT PARTITION_NAME FROM information_schema.PARTITIONS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'workplace_monthly' "
        "ORDER BY PARTITION_ORDINAL_POSITION"
    ))

    assert [r[0] for r in rows] == ["p2025", "p2026", "pmax"]


async def test_monthly_mart_has_month_index(db):
    # 계산 방법 API의 데이터 기간 MIN(snapshot_ym). PK(company_id, snapshot_ym)만 있으면 표 전체를
    # 읽었다(docs/08 I-02). 월이 맨 앞인 인덱스가 있으면 끝값만 읽는다
    rows = (await db.execute(text("SHOW INDEX FROM mart_company_monthly"))).mappings().all()

    assert any(r["Key_name"] != "PRIMARY" and r["Seq_in_index"] == 1
               and r["Column_name"] == "snapshot_ym" for r in rows)
