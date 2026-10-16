import statistics
from pathlib import Path

import pytest

from pipeline.geocode import rnaddr
from pipeline.geocode.company_location import (
    hq_query,
    medians,
    on_road,
    road_of,
    same_building,
    workplace_query,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "juso"

GN, SP = "서울특별시 강남구", "서울특별시 송파구"


@pytest.mark.parametrize("adres, expected", [
    (f"{GN} 강남대로58길 42 오케이빌딩(도곡동)",
     (f"{GN} 강남대로58길 42", "강남구", "강남대로58길", "42-0")),
    ("서울특별시 금천구 가산디지털2로 115 104,105호 (가산동)",
     ("서울특별시 금천구 가산디지털2로 115", "금천구", "가산디지털2로", "115-0")),
    (f"{SP} 양재대로71길 2-11 (방이동) 201호",
     (f"{SP} 양재대로71길 2-11", "송파구", "양재대로71길", "2-11")),
    ("서울 영등포구 여의도동 34-11",
     ("서울특별시 영등포구 여의도동 34-11", "영등포구", "여의도동", "34-11")),
    # 동 이름의 숫자를 건물번호로 읽지 않는다
    ("서울특별시 종로구 종로1가 1", ("서울특별시 종로구 종로1가 1", "종로구", "종로1가", "1-0")),
    ("서울특별시 중구 남대문로2가 국민은행본점빌딩", None),  # 번지가 없으면 쓰지 않는다
    ("경기도 수원시 영통구 삼성로 129", None),  # 성남 밖 경기(decisions/010)
    ("경기도 성남시 분당구 판교역로 235 (삼평동)",
     ("경기도 성남시 분당구 판교역로 235", "성남시 분당구", "판교역로", "235-0")),
    ("경기 성남시 분당구 삼평동 681",
     ("경기도 성남시 분당구 삼평동 681", "성남시 분당구", "삼평동", "681-0")),
])
def test_hq_query(adres, expected):
    assert hq_query(adres) == expected


@pytest.mark.parametrize("name, keyword", [
    ("(주)여인닷컴", "강남구 강남대로58길 여인닷컴"),
    ("주식회사계선-(상용)신세계남산24RM현장", "강남구 강남대로58길 계선"),
    ("동방건영(주)/일용/디에이치방배 중 도장공사", "강남구 강남대로58길 동방건영"),
    ("（주）타이드스퀘어", "강남구 강남대로58길 타이드스퀘어"),
    ("에쓰-오일(주)", "강남구 강남대로58길 에쓰-오일"),
    ("(주)A", None),
])
def test_workplace_query(name, keyword):
    result = workplace_query("강남구", "서울특별시 강남구 강남대로58길", name)
    assert (result[0] if result else None) == keyword


def test_pickers_need_exactly_one_match():
    results = [{"sggNm": "강남구", "rn": "테헤란로"}, {"sggNm": "서초구", "rn": "테헤란로"}]

    assert on_road("강남구", "테헤란로")(results) == results[0]
    assert on_road("강남구", "강남대로")(results) is None


def test_same_building_skips_annex_with_sub_number():
    main = {"sggNm": "강남구", "rn": "강남대로", "buldMnnm": "382", "buldSlno": "0"}
    kiosk = {"sggNm": "강남구", "rn": "강남대로", "buldMnnm": "382", "buldSlno": "2"}
    named = main | {"bdNm": "메리츠타워"}  # 같은 건물이 건물명만 달리 한 줄 더
    other_road = {"sggNm": "강남구", "rn": "강남대로14길", "buldMnnm": "382", "buldSlno": "0"}
    jibun = {"sggNm": "영등포구", "emdNm": "여의도동", "rn": "국제금융로", "buldMnnm": "10",
             "buldSlno": "0", "lnbrMnnm": "34", "lnbrSlno": "11"}

    pick = same_building("강남구", "강남대로", "382-0")
    assert pick([main, kiosk, other_road]) == main
    assert pick([main, named]) == main
    assert same_building("강남구", "강남대로", "382-2")([main, kiosk]) == kiosk
    assert same_building("서초구", "강남대로", "382-0")([main]) is None
    assert same_building("영등포구", "여의도동", "34-11")([jibun]) == jibun
    assert same_building("영등포구", "여의도동", "34-0")([jibun]) is None


def test_road_of_takes_road_name_only():
    assert road_of("서울특별시 성동구 독서당로14길") == "독서당로14길"
    assert road_of("서울특별시 종로구 종로1가") is None  # 동 이름
    assert road_of(None) is None and road_of("") is None


def test_rnaddr_joins_address_and_entrance_by_building_id():
    buildings = list(rnaddr.read_files(FIXTURES / "rnaddrkor_sample.txt"))

    # 깨진 행과 출입구 좌표가 없는 다른구 건물은 빠진다
    assert [b.lot_main for b in buildings] == [1, 2, 3, 4]
    assert buildings[0].sgg == "11990" and buildings[0].road == "가상로"
    assert 126.9 < buildings[0].lon < 127.0 and 37.5 < buildings[0].lat < 37.6


def test_medians_use_every_building_on_the_road_or_in_the_dong():
    buildings = list(rnaddr.read_files(FIXTURES / "rnaddrkor_sample.txt"))

    road_pt, dong_pt = medians(buildings, {("11990", "가상로"), ("11880", "가상로")},
                               {"1199010100", "1199010200"})

    first_three = buildings[:3]  # 11990 가상로의 건물
    assert road_pt[("11990", "가상로")] == (statistics.median(b.lon for b in first_three),
                                          statistics.median(b.lat for b in first_three))
    assert road_pt[("11990", "가상로")][0] == buildings[1].lon  # 경도 가운데 건물
    assert ("11880", "가상로") not in road_pt  # 좌표 없는 건물뿐
    assert dong_pt["1199010200"] == (buildings[3].lon, buildings[3].lat)


def test_rnaddr_reads_each_region_with_its_own_entrance_file():
    # 시험 폴더에는 서울 이름의 주소 파일(rnaddrkor_seoul.txt)이 없어 경기 쌍만 잡힌다
    assert rnaddr.region_pairs(FIXTURES) == [
        (FIXTURES / "rnaddrkor_gyunggi.txt", FIXTURES / "RNENTDATA_2610_41000.txt")]
    buildings = list(rnaddr.read_all(FIXTURES))

    assert [(b.sgg, b.road, b.lot_main) for b in buildings] == [
        ("41135", "가상판교로", 7), ("41135", "가상판교로", 8)]
    assert all(127.0 < b.lon < 127.3 and 37.3 < b.lat < 37.5 for b in buildings)  # 성남 근처
    # 모르는 이름의 주소 파일은 서울 출입구 파일과 짝짓는다
    assert rnaddr.sido_of(FIXTURES / "rnaddrkor_sample.txt") == "11000"
