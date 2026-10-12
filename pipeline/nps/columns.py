"""국민연금 가입 사업장 내역 CSV의 실제 헤더와 내부 필드 이름(SPEC Phase 1-3).

2026-08 파일 기준. 공단이 헤더를 바꾸면 `check_header()`가 적재 전에 실패한다.
"""

ENCODING = "cp949"

# 실제 헤더 → 내부 필드. 순서도 파일과 같다.
HEADER_MAP: dict[str, str] = {
    "자료생성년월": "data_ym",  # "2026-08" 형식. snapshot_ym(202608)으로 변환해 쓴다
    "사업장명": "workplace_name",
    "사업자등록번호": "biz_no6",  # 앞 6자리만 제공
    "사업장가입상태코드 1 등록 2 탈퇴": "status_code",
    "우편번호": "zip_code",
    "사업장지번상세주소": "jibun_address",
    "사업장도로명상세주소": "road_address",
    "고객법정동주소코드": "legal_dong_code",
    "고객행정동주소코드": "admin_dong_code",
    "법정동주소광역시도코드": "sido_code",
    "법정동주소광역시시군구코드": "sigungu_code",
    "법정동주소광역시시군구읍면동코드": "emd_code",
    "사업장형태구분코드 1 법인 2 개인": "form_type",
    "사업장업종코드": "industry_code",
    "사업장업종코드명": "industry_name",
    "적용일자": "joined_on",
    "재등록일자": "rejoined_on",
    "탈퇴일자": "left_on",
    "가입자수": "members",
    "당월고지금액": "billed_amount",
    "신규취득자수": "new_members",
    "상실가입자수": "lost_members",
}

FIELDS = list(HEADER_MAP.values())
INT_FIELDS = ("members", "billed_amount", "new_members", "lost_members")


def check_header(header: list[str]) -> None:
    """헤더가 HEADER_MAP과 이름 · 순서까지 같지 않으면 ValueError."""
    expected = list(HEADER_MAP)
    if [h.strip() for h in header] != expected:
        missing = [h for h in expected if h not in header]
        extra = [h for h in header if h not in expected]
        raise ValueError(f"국민연금 CSV 헤더가 다르다. 없음={missing}, 추가={extra}")


def to_snapshot_ym(data_ym: str) -> int:
    """'2026-08' → 202608."""
    year, month = data_ym.strip().split("-")
    return int(year) * 100 + int(month)
