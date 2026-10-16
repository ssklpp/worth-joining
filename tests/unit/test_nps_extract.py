import pytest

from pipeline.nps.columns import ENCODING, HEADER_MAP
from pipeline.nps.extract_seoul import extract, in_scope

HEADER = ",".join(HEADER_MAP) + "\r\n"


def row(ym: str, name: str, sido: str, sigungu: str = "1") -> str:
    values = [ym, name, "123456", "1", "", "", "", "", "", sido, sigungu] + ["1"] * 11
    return ",".join(values) + "\r\n"


def test_extract_keeps_seoul_and_seongnam_and_names_by_data_month(tmp_path):
    src = tmp_path / "202609.csv"  # 공개 월 이름, 내용은 2026-08
    kept_rows = [row("2026-08", "서울회사", "11", "680"), row("2026-08", "판교회사", "41", "135")]
    src.write_text(HEADER + kept_rows[0] + row("2026-08", "수원회사", "41", "111") + kept_rows[1]
                   + row("2026-08", "부산회사", "26", "350"), encoding=ENCODING, newline="")

    out, total, kept = extract(src, tmp_path)

    assert (out.name, total, kept) == ("202608.csv", 4, 2)
    assert out.read_text(encoding=ENCODING) == HEADER.replace("\r\n", "\n") + "".join(
        r.replace("\r\n", "\n") for r in kept_rows)


@pytest.mark.parametrize("sido, sigungu, expected", [
    ("11", "680", True), ("41", "131", True), ("41", "133", True), ("41", "135", True),
    ("41", "130", False), ("41", "111", False), ("26", "135", False),
])
def test_in_scope(sido, sigungu, expected):
    assert in_scope(sido, sigungu) is expected


def test_extract_rejects_mixed_months(tmp_path):
    src = tmp_path / "x.csv"
    src.write_text(HEADER + row("2026-07", "a", "11") + row("2026-08", "b", "11"),
                   encoding=ENCODING, newline="")

    with pytest.raises(ValueError, match="자료 월"):
        extract(src, tmp_path / "out")
