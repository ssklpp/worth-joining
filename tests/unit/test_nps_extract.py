import pytest

from pipeline.nps.columns import ENCODING, HEADER_MAP
from pipeline.nps.extract_seoul import extract

HEADER = ",".join(HEADER_MAP) + "\r\n"


def row(ym: str, name: str, sido: str) -> str:
    values = [ym, name, "123456", "1", "", "", "", "", "", sido] + ["1"] * 12
    return ",".join(values) + "\r\n"


def test_extract_keeps_only_seoul_and_names_by_data_month(tmp_path):
    src = tmp_path / "202609.csv"  # 공개 월 이름, 내용은 2026-08
    src.write_text(HEADER + row("2026-08", "서울회사", "11") + row("2026-08", "경기회사", "41"),
                   encoding=ENCODING, newline="")

    out, total, kept = extract(src, tmp_path)

    assert (out.name, total, kept) == ("202608.csv", 2, 1)
    assert out.read_text(encoding=ENCODING) == HEADER.replace("\r\n", "\n") + (
        row("2026-08", "서울회사", "11").replace("\r\n", "\n")
    )


def test_extract_rejects_mixed_months(tmp_path):
    src = tmp_path / "x.csv"
    src.write_text(HEADER + row("2026-07", "a", "11") + row("2026-08", "b", "11"),
                   encoding=ENCODING, newline="")

    with pytest.raises(ValueError, match="자료 월"):
        extract(src, tmp_path / "out")
