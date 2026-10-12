"""테스트용 가상 국민연금 CSV 생성. 실제 회사 이름을 쓰지 않는다."""

from dataclasses import dataclass
from pathlib import Path

from pipeline.nps.columns import ENCODING, HEADER_MAP


@dataclass
class Row:
    name: str
    biz_no6: str = "123456"
    status: str = "1"
    members: int = 10
    billed: int = 3_000_000
    new: int = 0
    lost: int = 0
    dong: str = "1111010100"
    road: str = "서울특별시 종로구 가상로"
    industry: str = "620100"
    joined_on: str = "2020-01-01"
    left_on: str = ""


def write_nps_csv(path: Path, ym: int, rows: list[Row]) -> Path:
    data_ym = f"{ym // 100}-{ym % 100:02d}"
    lines = [",".join(HEADER_MAP)]
    for r in rows:
        lines.append(",".join([
            data_ym, r.name, r.biz_no6, r.status, "03000", "서울특별시 종로구 가상동", r.road,
            r.dong, r.dong, r.dong[:2], r.dong[2:5], r.dong[5:8], "1", r.industry, "가상 업종",
            r.joined_on, "", r.left_on, str(r.members), str(r.billed), str(r.new), str(r.lost),
        ]))
    path.write_text("\r\n".join(lines) + "\r\n", encoding=ENCODING, newline="")
    return path
