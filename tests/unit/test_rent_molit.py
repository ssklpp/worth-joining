"""국토부 전월세(성남) 적재기 (decisions/010 2단계). 가상 계약 · 가상 건물(tests/fixtures)."""

import datetime as dt
from pathlib import Path

import pytest
from sqlalchemy import text

from pipeline.rent import molit, seoul

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
VILLA = FIXTURES / "rent" / "molit_villa.csv"
OFFICETEL = FIXTURES / "rent" / "molit_officetel.csv"
DONGS = FIXTURES / "rent" / "legal_dong_sample.txt"
ADDRESS = FIXTURES / "juso" / "rnaddrkor_gyunggi.txt"  # 가상판교로 7 · 8(지번 7-0 · 8-0)
AS_OF = dt.date(2026, 10, 14)


def test_dong_codes_keep_existing_names_only():
    assert molit.dong_codes(DONGS) == {"경기도 성남시 분당구 가상판교동": "4113510900"}


def test_to_seoul_fields_follows_seoul_column_order():
    row = {"시군구": "경기도 성남시 분당구 가상판교동", "번지": "산8", "본번": "0008",
           "부번": "0000",
           "단지명": "가상", "전월세구분": "월세", "전용면적(㎡)": "22.0000", "계약년월": "202608",
           "계약일": "1", "보증금(만원)": "2,000", "월세금(만원)": "80", "층": "9",
           "건축년도": "2018", "계약기간": "-", "계약구분": "신규", "갱신요구권 사용": "-",
           "종전계약 보증금(만원)": "", "종전계약 월세(만원)": ""}

    fields = dict(zip(seoul.RAW_COLUMNS, molit.to_seoul_fields(row, molit.dong_codes(DONGS)),
                      strict=True))

    assert (fields["sgg_code"], fields["sgg_name"], fields["bjdong_code"], fields["bjdong_name"]) \
        == ("41135", "성남시 분당구", "10900", "가상판교동")
    assert (fields["jibun_type"], fields["contract_date"], fields["house_type"]) \
        == ("2", "20260801", "오피스텔")


@pytest.fixture
def engine(pipeline_engine):
    yield pipeline_engine
    with pipeline_engine.begin() as conn:
        for table in ("raw_rent_contract", "rent_contract", "building", "geocode_cache"):
            conn.execute(text(f"TRUNCATE TABLE {table}"))
        conn.execute(text("DELETE FROM ingestion_log WHERE source = 'rent_molit'"))
    with pipeline_engine.connect() as conn:
        conn.execute(text("ALTER TABLE rent_contract PARTITION BY RANGE (contract_ym)"
                          " (PARTITION pmax VALUES LESS THAN MAXVALUE)"))


def rows(engine, sql):
    with engine.connect() as conn:
        return conn.execute(text(sql)).all()


def test_run_loads_seongnam_contracts_and_links_buildings(engine):
    molit.run(engine, [VILLA, OFFICETEL], AS_OF, dong_file=DONGS, address_path=ADDRESS)

    # 연립 4행 중 같은 계약 1행 · 없는 동 1행을 빼고 2행, 오피스텔 1행
    assert rows(engine, "SELECT COUNT(*) FROM raw_rent_contract")[0][0] == 3
    assert rows(engine, """SELECT addr_key, house_type, deposit_man, monthly_man,
                           building_id IS NOT NULL FROM rent_contract ORDER BY addr_key, house_type
                        """) == [("41135-10900-1-7-0", "연립다세대", 1000, 60, 1),
                                 ("41135-10900-1-8-0", "오피스텔", 2000, 80, 1),
                                 # 산 8은 주소 파일에 없어 건물이 없다
                                 ("41135-10900-2-8-0", "연립다세대", 20000, 0, 0)]
    assert molit.run(engine, [VILLA], AS_OF, dong_file=DONGS, address_path=ADDRESS)
    assert rows(engine, "SELECT COUNT(*) FROM raw_rent_contract")[0][0] == 3  # 같은 파일은 건너뜀
