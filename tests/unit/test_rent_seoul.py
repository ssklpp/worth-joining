"""전월세 적재기 (SPEC Phase 9-2 · 4 · 6 · 7 · 14, decisions/007). 가상 계약 · 가상 건물."""

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import text

from pipeline.rent import seoul

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FILES = [FIXTURES / "rent" / "seoul_rent_a.csv", FIXTURES / "rent" / "seoul_rent_b.csv"]
ADDRESS = FIXTURES / "juso" / "rnaddrkor_sample.txt"
AS_OF = dt.date(2026, 10, 13)


@pytest.mark.parametrize("as_of, end", [
    (dt.date(2026, 10, 13), 202608),  # 9/13이 속한 달(9월)의 전월
    (dt.date(2026, 11, 1), 202609),  # 10/2 → 9월 계약은 10/30까지 신고가 끝났다
    (dt.date(2026, 1, 15), 202511),
])
def test_period_end_is_month_before_report_deadline(as_of, end):
    assert seoul.period_end(as_of) == end


def test_month_add_crosses_years():
    assert seoul.month_add(202608, -23) == 202409
    assert seoul.month_add(202412, 1) == 202501


def test_row_hash_ignores_receipt_year_and_number_formatting():
    a = next(r for r in seoul.read_csv(FILES[0]) if r[10] == "20251215")
    b = next(r for r in seoul.read_csv(FILES[1]) if r[10] == "20251215")

    assert a[0] != b[0] and a[7] != b[7]  # 접수연도 · 본번 표기가 다르다
    assert seoul.row_hash(a) == seoul.row_hash(b)


@pytest.fixture
def engine(pipeline_engine):
    yield pipeline_engine
    with pipeline_engine.begin() as conn:
        for table in ("raw_rent_contract", "rent_contract", "building", "geocode_cache"):
            conn.execute(text(f"TRUNCATE TABLE {table}"))
        conn.execute(text("DELETE FROM ingestion_log WHERE source = 'rent_seoul'"))
    with pipeline_engine.connect() as conn:
        conn.execute(text("ALTER TABLE rent_contract PARTITION BY RANGE (contract_ym)"
                          " (PARTITION pmax VALUES LESS THAN MAXVALUE)"))


def rows(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).all()


def test_run_loads_filters_and_links_buildings(engine):
    counts = seoul.run(engine, FILES, AS_OF, address_path=ADDRESS)

    assert rows(engine, "SELECT COUNT(*) FROM raw_rent_contract")[0][0] == 7  # 9행 중 겹친 1행
    contracts = rows(engine, "SELECT contract_ym, addr_key, house_type, area_m2, deposit_man,"
                             " monthly_man, floor, building_id IS NOT NULL"
                             " FROM rent_contract ORDER BY contract_ym, addr_key")
    # 아파트 · 본번 없는 행 · 202409 이전은 빠진다. contract_ym은 계약일 기준
    assert [(c[0], c[1], c[2]) for c in contracts] == [
        (202503, "11990-10100-1-2-0", "연립다세대"),
        (202506, "11990-19900-1-9-0", "연립다세대"),
        (202512, "11990-10100-1-1-0", "오피스텔"),
        (202609, "11990-10200-1-4-0", "연립다세대"),  # 기준월 뒤의 달도 적재는 한다
    ]
    assert tuple(contracts[2][3:7]) == (Decimal("27.07"), 1000, 60, 3)
    assert [c[7] for c in contracts] == [1, 0, 1, 1]  # 주소 파일에 없는 지번은 연결 안 됨
    assert (counts["file"], counts["not_found"]) == (3, 1)
    assert rows(engine, "SELECT COUNT(*) FROM building WHERE ST_X(pt) BETWEEN 126.9 AND 127.0"
                        " AND ST_Y(pt) BETWEEN 37.5 AND 37.6")[0][0] == 3
    assert rows(engine, "SELECT build_year FROM building WHERE addr_key = '11990-10100-1-1-0'"
                        )[0][0] == 2015


def test_rerun_is_idempotent(engine):
    seoul.run(engine, FILES, AS_OF, address_path=ADDRESS)
    before = rows(engine, "SELECT row_hash, building_id FROM rent_contract ORDER BY row_hash")

    seoul.run(engine, FILES, AS_OF, address_path=ADDRESS)

    after = rows(engine, "SELECT row_hash, building_id FROM rent_contract ORDER BY row_hash")
    assert after == before
    assert rows(engine, "SELECT COUNT(*) FROM raw_rent_contract")[0][0] == 7
    assert rows(engine, "SELECT status FROM ingestion_log WHERE source = 'rent_seoul'"
                        " ORDER BY run_id DESC LIMIT 2") == [("skipped",), ("skipped",)]


def test_search_picker_accepts_one_building_on_related_lot():
    def result(dong, rn, no, lot):
        return {"sggNm": "종로구", "emdNm": dong, "rn": rn, "buldMnnm": no, "buldSlno": "0",
                "lnbrMnnm": lot, "lnbrSlno": "60"}
    pick = seoul.one_building("종로구", "원남동")
    a = result("원남동", "창경궁로18길", "20", "66")

    assert pick([a, {**a, "bdNm": "B동"}]) is a  # 같은 건물의 동만 다른 두 줄
    assert pick([a, result("원남동", "창경궁로18길", "22", "66")]) is None  # 다른 건물
    assert pick([result("연지동", "창경궁로18길", "20", "66")]) is None  # 다른 동
