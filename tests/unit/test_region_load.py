import pytest
from sqlalchemy import text

from pipeline.region.load import ENCODING, parse_sigungu, run

SAMPLE = [
    "법정동코드\t법정동명\t폐지여부",
    "1100000000\t서울특별시\t존재",
    "1111000000\t서울특별시 종로구\t존재",
    "1111010100\t서울특별시 종로구 청운동\t존재",
    "1199000000\t서울특별시 옛구\t폐지",
    "1199000000\t서울특별시 새구\t존재",
    "4100000000\t경기도\t존재",
    "4111000000\t경기도 수원시\t존재",
    "4111100000\t경기도 수원시 장안구\t존재",
    "4113000000\t경기도 성남시\t존재",
    "4113500000\t경기도 성남시 분당구\t존재",
    "4113510900\t경기도 성남시 분당구 삼평동\t존재",
    "2611000000\t부산광역시 중구\t존재",
]


def write(path, lines):
    path.write_text("\r\n".join(lines) + "\r\n", encoding=ENCODING, newline="")
    return path


def test_parse_keeps_only_sigungu_in_scope_and_prefers_existing(tmp_path):
    regions = parse_sigungu(write(tmp_path / "r.txt", SAMPLE))

    assert regions == {"11110": ("서울특별시", "종로구"), "11990": ("서울특별시", "새구"),
                       "41135": ("경기도", "성남시 분당구")}


def test_parse_rejects_changed_header(tmp_path):
    with pytest.raises(ValueError, match="헤더"):
        parse_sigungu(write(tmp_path / "r.txt", ["코드\t이름\t상태", *SAMPLE[1:]]))


def test_run_loads_and_skips_same_file(tmp_path, clean_tables):
    path = write(tmp_path / "r.txt", SAMPLE)

    assert run(clean_tables, path) == "success"
    assert run(clean_tables, path) == "skipped"
    with clean_tables.connect() as conn:
        rows = conn.execute(text("SELECT * FROM region ORDER BY region_code")).all()
    assert [tuple(r) for r in rows] == [("11110", "서울특별시", "종로구"),
                                        ("11990", "서울특별시", "새구"),
                                        ("41135", "경기도", "성남시 분당구")]
