import httpx
import pytest
from sqlalchemy import text

from pipeline.common.http import ApiClient, ApiError
from pipeline.dart.company_info import parse, run


def test_parse_keeps_digits_and_empty_as_none():
    body = {"status": "000", "bizr_no": "123-45-67890", "corp_cls": "Y", "adres": " 서울 중구 "}

    assert parse(body) == {"bizr_no": "1234567890", "corp_cls": "Y", "adres": "서울 중구"}
    assert parse({"status": "000", "bizr_no": "", "corp_cls": "E", "adres": ""}) == {
        "bizr_no": None, "corp_cls": "E", "adres": None}
    assert parse({"status": "013", "message": "조회된 데이타가 없습니다."}) is None
    foreign = {"status": "000", "bizr_no": "3834099500008074", "corp_cls": "E", "adres": "HK"}
    assert parse(foreign)["bizr_no"] is None


def test_parse_raises_on_key_error():
    with pytest.raises(ApiError, match="010"):
        parse({"status": "010", "message": "등록되지 않은 키입니다."})


def seed(engine):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO company VALUES (1, '123456', '가상물산', '가상물산')"))
        conn.execute(text(
            "INSERT INTO dart_corp (corp_code, corp_name, corp_name_norm, stock_code) VALUES"
            " ('00000001', '가상소프트', '가상소프트', '900001'),"  # 상장사
            " ('00000002', '가상물산', '가상물산', NULL),"         # 서울 회사와 이름 같음
            " ('00000003', '무관한법인', '무관한법인', NULL)"))     # 대상 아님


def test_run_fetches_targets_and_stops_at_limit(clean_tables):
    seed(clean_tables)
    seen = []

    def handler(req):
        seen.append(req.url.params["corp_code"])
        return httpx.Response(200, json={"status": "000", "bizr_no": "1234567890",
                                         "corp_cls": "N", "adres": "서울"})

    client = ApiClient(clean_tables, "dart", 1, transport=httpx.MockTransport(handler), backoff=0)
    assert run(clean_tables, client, "KEY", interval=0) == 1  # 한도 1건에서 멈춘다
    client.daily_limit = 10
    assert run(clean_tables, client, "KEY", interval=0) == 1  # 남은 1건만 이어서

    assert seen == ["00000001", "00000002"]
    with clean_tables.connect() as conn:
        fetched = conn.execute(text(
            "SELECT corp_code FROM dart_corp WHERE fetched_at IS NOT NULL ORDER BY 1")).all()
        statuses = conn.execute(text(
            "SELECT status FROM ingestion_log WHERE source = 'dart_company'")).all()
    assert [r[0] for r in fetched] == ["00000001", "00000002"]
    assert [r[0] for r in statuses] == ["success", "success"]
