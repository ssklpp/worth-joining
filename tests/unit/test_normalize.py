import pytest

from pipeline.common.normalize import normalize_name


@pytest.mark.parametrize("name, expected", [
    ("(주)가상소프트", "가상소프트"),
    ("㈜가상소프트", "가상소프트"),
    ("가상 소프트 주식회사", "가상소프트"),
    ("（주）가상소프트", "가상소프트"),        # 전각 괄호
    ("가상소프트（주）/일용/현장", "가상소프트일용현장"),
    ("ｌｇ가상", "LG가상"),                    # 전각 영문
    ("유한회사 가상-2", "가상2"),
])
def test_normalize_name(name, expected):
    assert normalize_name(name) == expected
