import re
import unicodedata

CORP_TOKENS = re.compile(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\(사\)|사단법인")
NON_WORD = re.compile(r"[^0-9A-Za-z가-힣]")


def normalize_name(name: str) -> str:
    """상호 정규화(SPEC 6장). 회사 식별 키 biz_no6 + name_norm의 name_norm.

    NFKC를 먼저 적용해 전각 괄호 · 영숫자("（주）", "ＡＢＣ")를 반각으로 바꾼다. 국민연금
    원본에 섞여 있어, 없으면 "（주）골프존"이 "주골프존"이 된다(troubleshooting TS-016).
    """
    return NON_WORD.sub("", CORP_TOKENS.sub("", unicodedata.normalize("NFKC", name))).upper()
