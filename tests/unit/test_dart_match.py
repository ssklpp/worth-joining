import pytest
from sqlalchemy import text

from pipeline.common.normalize import normalize_name
from pipeline.dart.match import match


@pytest.fixture
def conn(pipeline_engine):
    with pipeline_engine.connect() as c:
        trans = c.begin()
        yield c
        trans.rollback()


def company(conn, company_id, biz_no6, name):
    conn.execute(text("INSERT INTO company VALUES (:id, :b, :norm, :name)"),
                 {"id": company_id, "b": biz_no6, "norm": normalize_name(name), "name": name})


def corp(conn, code, name, bizr_no, stock=None):
    conn.execute(text("INSERT INTO dart_corp (corp_code, corp_name, corp_name_norm, stock_code,"
                      " bizr_no) VALUES (:c, :name, :norm, :s, :b)"),
                 {"c": code, "name": name, "norm": normalize_name(name), "s": stock, "b": bizr_no})


def links(conn):
    return {r[0]: (r[1], r[2], r[3] and float(r[3])) for r in conn.execute(text(
        "SELECT company_id, corp_code, match_type, match_score FROM company_dart_link"))}


def test_exact_then_fuzzy_within_same_bizr6(conn):
    company(conn, 1, "123456", "가상소프트")          # 정확
    company(conn, 2, "123456", "가나다라마바사아")     # 유사(93점)
    company(conn, 3, "123456", "가나라")              # 85점 미만
    company(conn, 4, "999999", "가상소프트")          # 6자리가 다르면 연결 안 함
    corp(conn, "00000001", "가상소프트", "1234567890")
    corp(conn, "00000002", "가나다라마바사", "1234560000")
    corp(conn, "00000003", "가나다", "1234561111")

    assert match(conn) == {"exact": 1, "fuzzy": 1}
    assert links(conn) == {1: ("00000001", "exact", 1.0), 2: ("00000002", "fuzzy", 0.933)}


def test_prefers_listed_corp_and_is_idempotent(conn):
    company(conn, 1, "123456", "가상소프트")
    corp(conn, "00000001", "가상소프트", "1234567890")
    corp(conn, "00000009", "가상소프트", "1234569999", stock="900009")

    match(conn)
    match(conn)

    assert links(conn) == {1: ("00000009", "exact", 1.0)}


def test_keeps_manual_link(conn):
    company(conn, 1, "123456", "가상소프트")
    corp(conn, "00000001", "가상소프트", "1234567890")
    corp(conn, "00000005", "전혀다른이름", None)
    conn.execute(text("INSERT INTO company_dart_link VALUES (1, '00000005', 'manual', NULL)"))

    assert match(conn) == {"exact": 0, "fuzzy": 0}
    assert links(conn)[1][:2] == ("00000005", "manual")


def test_latin_letters_match_hangul_reading(conn):
    company(conn, 1, "123456", "엘지디스플레이")
    corp(conn, "00000001", "LG디스플레이", "1234567890", stock="034220")

    assert match(conn) == {"exact": 0, "fuzzy": 1}
    assert links(conn) == {1: ("00000001", "fuzzy", 1.0)}


def test_ampersand_reads_as_hangul(conn):
    company(conn, 1, "123456", "주식회사에프앤에프")
    corp(conn, "00000001", "F&F", "1234567890", stock="383220")

    match(conn)

    assert links(conn) == {1: ("00000001", "fuzzy", 1.0)}


@pytest.mark.parametrize("company_name, corp_name, linked", [
    ("(주)엘지유플러스(영업)", "LG유플러스", True),   # 85점대지만 DART 이름으로 시작
    ("구로2동새마을금고", "구로5동새마을금고", False),  # 89점, 앞부분 다름
    ("(주)한오션", "한화오션", False),                # 86점, 다른 회사
])
def test_mid_scores_need_prefix(conn, company_name, corp_name, linked):
    company(conn, 1, "123456", company_name)
    corp(conn, "00000001", corp_name, "1234567890")

    match(conn)

    assert (1 in links(conn)) is linked
