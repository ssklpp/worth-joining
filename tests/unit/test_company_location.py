import pytest

from pipeline.geocode.company_location import hq_query, on_road, same_building, workplace_query

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
    ("경기도 수원시 영통구 삼성로 129", None),
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
