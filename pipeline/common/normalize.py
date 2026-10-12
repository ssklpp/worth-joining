import re

CORP_TOKENS = re.compile(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\(사\)|사단법인")
NON_WORD = re.compile(r"[^0-9A-Za-z가-힣]")


def normalize_name(name: str) -> str:
    """상호 정규화(SPEC 6장). 회사 식별 키 biz_no6 + name_norm의 name_norm."""
    return NON_WORD.sub("", CORP_TOKENS.sub("", name)).upper()
