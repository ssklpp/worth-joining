import pytest

from pipeline.common.normalize import normalize_name
from pipeline.nps.columns import HEADER_MAP, check_header, to_snapshot_ym
from pipeline.nps.profile import address_level, jibun_level


def test_to_snapshot_ym():
    assert to_snapshot_ym("2026-08") == 202608


def test_check_header_accepts_real_header():
    check_header(list(HEADER_MAP))


def test_check_header_rejects_changed_header():
    header = list(HEADER_MAP)
    header[18] = "가입자 수"
    with pytest.raises(ValueError, match="가입자수"):
        check_header(header)


@pytest.mark.parametrize(
    ("addr", "level"),
    [
        ("서울특별시 용산구 독서당로14길", "road"),
        ("경기도 광주시 도척면 도척윗로", "road"),
        ("서울특별시 강남구 테헤란로 152", "building"),
        ("울산광역시 중구 시계탑거리", "area"),
        ("", "empty"),
    ],
)
def test_address_level(addr, level):
    assert address_level(addr) == level


def test_jibun_level():
    assert jibun_level("서울특별시 용산구 한남동") == "dong"
    assert jibun_level("서울특별시 용산구 한남동 683-2") == "lot"


def test_normalize_name():
    assert normalize_name("우성기전(주)") == "우성기전"
    assert normalize_name("주식회사 abc-Tech") == "ABCTECH"
