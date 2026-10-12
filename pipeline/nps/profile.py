"""국민연금 CSV 프로파일링 (SPEC Phase 1-2).

python -m pipeline.nps.profile data/raw/nps/*.csv
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from pipeline.common.normalize import normalize_name
from pipeline.nps.columns import ENCODING, FIELDS, HEADER_MAP, INT_FIELDS, check_header

ROAD_SUFFIX = re.compile(r"(로|길)$")
STARTS_WITH_DIGIT = re.compile(r"^\d")


def address_level(addr: str) -> str:
    """도로명 주소의 상세 수준.

    building: 건물번호 있음, road: 도로명까지, area: 도로명보다 넓음, empty: 빈 값.
    """
    tokens = addr.split()
    if not tokens:
        return "empty"
    for cur, nxt in zip(tokens, tokens[1:], strict=False):
        if ROAD_SUFFIX.search(cur) and STARTS_WITH_DIGIT.match(nxt):
            return "building"
    return "road" if ROAD_SUFFIX.search(tokens[-1]) else "area"


def jibun_level(addr: str) -> str:
    """지번 주소의 상세 수준. lot: 번지 있음, dong: 읍면동 · 리까지, empty."""
    tokens = addr.split()
    if not tokens:
        return "empty"
    return "lot" if any(STARTS_WITH_DIGIT.match(t) for t in tokens[2:]) else "dong"


def read_csv(path: Path) -> pd.DataFrame:
    with path.open(encoding=ENCODING, newline="") as f:
        check_header(f.readline().rstrip("\r\n").split(","))
    df = pd.read_csv(
        path, encoding=ENCODING, dtype=str, keep_default_na=False, header=0, names=FIELDS
    )
    for col in INT_FIELDS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def share(part: int, total: int) -> str:
    return f"{part:,} ({part / total:.2%})" if total else "0"


def profile(path: Path) -> None:
    df = read_csv(path)
    n = len(df)
    print(f"\n=== {path.name} ===")
    print(f"인코딩: {ENCODING}, 행 수: {n:,}, 자료생성년월: {sorted(df['data_ym'].unique())}")
    print("헤더(실제 → 내부):")
    for kor, eng in HEADER_MAP.items():
        print(f"  {kor} → {eng}")

    print("결측률 (빈 문자열 기준):")
    for col in FIELDS:
        empty = int((df[col].astype(str).str.strip() == "").sum()) + int(df[col].isna().sum())
        if empty:
            print(f"  {col}: {share(empty, n)}")

    print("코드 분포:")
    print(f"  status_code: {df['status_code'].value_counts().to_dict()}")
    print(f"  form_type: {df['form_type'].value_counts().to_dict()}")
    print(f"  업종 수: {df['industry_code'].nunique():,}")

    biz = df["biz_no6"]
    dup_rows = int(biz.duplicated(keep=False).sum())
    names_per_biz = df.groupby("biz_no6")["workplace_name"].nunique()
    print("사업자번호 6자리:")
    print(f"  형식 오류(숫자 6자리 아님): {share(int((~biz.str.fullmatch(r'\d{6}')).sum()), n)}")
    print(f"  고유 값: {biz.nunique():,}, 중복 행: {share(dup_rows, n)}")
    print(f"  이름이 2개 이상인 번호: {share(int((names_per_biz > 1).sum()), len(names_per_biz))}")

    df["name_norm"] = df["workplace_name"].map(normalize_name)
    company_keys = df[["biz_no6", "name_norm"]].drop_duplicates()
    wp_key = ["biz_no6", "name_norm", "workplace_name", "legal_dong_code"]
    wp_dup = int(df.duplicated(wp_key, keep=False).sum())
    print("회사 · 사업장 키:")
    print(f"  회사(biz_no6 + name_norm): {len(company_keys):,}")
    print(f"  빈 name_norm: {share(int((df['name_norm'] == '').sum()), n)}")
    print(f"  사업장 자연키(회사 + 사업장명 + 법정동) 중복 행: {share(wp_dup, n)}")

    print("가입자 · 고지금액:")
    print(f"  members <= 0: {share(int((df['members'] <= 0).sum()), n)}")
    cross = pd.crosstab(df["status_code"], df["members"] <= 0)
    print(f"  상태코드 × (members <= 0): {cross.to_dict()}")
    print(f"  숫자 변환 실패: "
          f"{ {c: int(df[c].isna().sum()) for c in INT_FIELDS if df[c].isna().any()} or '없음'}")
    per_member = df["billed_amount"] / df["members"].where(df["members"] > 0)
    quantiles = per_member.quantile([0.5, 0.9, 0.99, 1.0]).round().to_dict()
    print(f"  1인당 고지금액 분위(원): {quantiles}")

    road = df["road_address"].map(address_level)
    jibun = df["jibun_address"].map(jibun_level)
    print("주소 상세 수준:")
    print(f"  도로명: { {k: share(v, n) for k, v in road.value_counts().items()} }")
    print(f"  지번: { {k: share(v, n) for k, v in jibun.value_counts().items()} }")
    for level in ("building", "area"):
        sample = df.loc[road == level, "road_address"].head(3).tolist()
        if sample:
            print(f"  도로명 {level} 예시: {sample}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.files:
        profile(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
