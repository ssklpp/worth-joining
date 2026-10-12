import io
import zipfile
from pathlib import Path

from sqlalchemy import text

from pipeline.dart.corp_code import parse, run

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "dart" / "CORPCODE.xml"


def make_zip(xml: bytes) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("CORPCODE.xml", xml)
    return buf.getvalue()


def test_parse_normalizes_name_and_blank_stock_code():
    rows = parse(make_zip(FIXTURE.read_bytes()))

    assert rows == [
        {"code": "00000001", "name": "가상소프트", "norm": "가상소프트", "stock": "900001"},
        {"code": "00000002", "name": "(주)가상물산", "norm": "가상물산", "stock": None},
        {"code": "00000003", "name": "가상 테크 주식회사", "norm": "가상테크", "stock": None},
    ]


def test_run_loads_skips_same_zip_and_keeps_company_json_fields(clean_tables):
    zip_bytes = make_zip(FIXTURE.read_bytes())

    assert run(clean_tables, zip_bytes) == "success"
    assert run(clean_tables, zip_bytes) == "skipped"

    # company.json으로 채운 값은 다음 corpCode 적재에서 지워지면 안 된다
    with clean_tables.begin() as conn:
        conn.execute(text("UPDATE dart_corp SET bizr_no = '1234567890', adres = '서울 어딘가'"
                          " WHERE corp_code = '00000002'"))
    renamed = FIXTURE.read_bytes().replace("(주)가상물산".encode(), "가상상사".encode())
    assert run(clean_tables, make_zip(renamed)) == "success"

    with clean_tables.connect() as conn:
        row = conn.execute(text("SELECT corp_name, corp_name_norm, bizr6, adres FROM dart_corp"
                                " WHERE corp_code = '00000002'")).one()
        total = conn.execute(text("SELECT COUNT(*) FROM dart_corp")).scalar()
    assert tuple(row) == ("가상상사", "가상상사", "123456", "서울 어딘가")
    assert total == 3
