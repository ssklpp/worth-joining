"""전국 국민연금 CSV에서 서울특별시 사업장만 추출한다(docs/decisions/002).

python -m pipeline.nps.extract_seoul data/raw/nps/all/*.csv

출력은 data/raw/nps/<자료 월>.csv. 공단 파일 이름은 공개 월이라 자료 월보다 한 달 늦을 수 있으므로
이름은 파일 안의 자료생성년월로 정한다. 인코딩 · 헤더 · 행 내용은 바꾸지 않는다.
"""

import argparse
import csv
import sys
from pathlib import Path

from pipeline.nps.columns import ENCODING, FIELDS, check_header, to_snapshot_ym

SEOUL_SIDO_CODE = "11"
SIDO = FIELDS.index("sido_code")


def extract(src: Path, out_dir: Path) -> tuple[Path, int, int]:
    total, lines, months = 0, [], set()
    with src.open(encoding=ENCODING, newline="") as f:
        header = f.readline()
        check_header(next(csv.reader([header])))
        for line in f:
            row = next(csv.reader([line]))
            total += 1
            months.add(row[0])
            if row[SIDO] == SEOUL_SIDO_CODE:
                lines.append(line)
    if len(months) != 1:
        raise ValueError(f"{src.name}: 자료 월이 하나가 아니다 {sorted(months)}")
    out = out_dir / f"{to_snapshot_ym(months.pop())}.csv"
    with out.open("w", encoding=ENCODING, newline="") as f:
        f.write(header)
        f.writelines(lines)
    return out, total, len(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/raw/nps"))
    args = parser.parse_args(argv)
    for src in args.files:
        out, total, kept = extract(src, args.out)
        print(f"{src.name} -> {out.name}: 전체 {total:,}행, 서울 {kept:,}행 ({kept / total:.1%})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
