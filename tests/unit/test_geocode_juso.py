import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from pipeline.common.http import ApiError
from pipeline.geocode.juso import Juso, clean_keyword

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "juso"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def juso(engine, search_body, coord_body=None, calls=None):
    def handler(req):
        if calls is not None:
            calls.append(req.url.path)
        body = search_body if req.url.path.endswith("addrLinkApi.do") else coord_body
        return httpx.Response(200, json=body)
    return Juso(engine, "SKEY", "CKEY", transport=httpx.MockTransport(handler), backoff=0,
                interval=0)


def error(code, message):
    return {"results": {"common": {"errorCode": code, "errorMessage": message}}}


def cache_rows(engine):
    with engine.connect() as conn:
        return conn.execute(text(
            "SELECT addr_key, status, lon, lat, accuracy, provider, fail_reason"
            " FROM geocode_cache ORDER BY addr_key")).all()


def test_geocode_saves_building_point_and_uses_cache(clean_tables):
    calls = []
    g = juso(clean_tables, load("search_one.json"), load("coord.json"), calls)

    first = g.geocode("addr:가상로 12", "서울특별시 가상구 가상로 12")
    second = g.geocode("addr:가상로 12", "서울특별시 가상구 가상로 12")

    assert first.status == "ok" and first.accuracy == "building"
    assert 126.9 < first.lon < 127.0 and 37.5 < first.lat < 37.6
    assert second == first
    assert len(calls) == 2  # 검색 1 + 좌표 1. 두 번째는 캐시
    row = cache_rows(clean_tables)[0]
    assert (row.status, row.provider) == ("ok", "juso")


def test_ambiguous_and_empty_results_are_cached_as_failures(clean_tables):
    two = juso(clean_tables, load("search_two.json"))
    empty_body = {"results": {"common": {"errorCode": "0", "totalCount": "0"}, "juso": []}}
    empty = juso(clean_tables, empty_body)

    assert two.geocode("addr:a", "가상로").fail_reason == "ambiguous:2"
    assert empty.geocode("addr:b", "없는로").fail_reason == "no_result"
    assert [r.status for r in cache_rows(clean_tables)] == ["fail", "fail"]


def test_custom_picker_chooses_road(clean_tables):
    g = juso(clean_tables, load("search_two.json"), load("coord.json"))

    result = g.geocode("name:x", "가상구 다른로 가상회사",
                       pick=lambda rs: next((r for r in rs if r["rn"] == "다른로"), None))

    assert result.status == "ok"


def test_keyword_error_is_cached_but_key_error_stops(clean_tables):
    bad_word = juso(clean_tables, error("E0008", "검색어는 두글자 이상 입력되어야 합니다."))
    bad_key = juso(clean_tables, error("E0001", "승인되지 않은 KEY 입니다."))

    assert bad_word.geocode("addr:c", "가").fail_reason.startswith("search E0008")
    with pytest.raises(ApiError, match="E0001"):
        bad_key.geocode("addr:d", "가상로 1")
    assert [r.addr_key for r in cache_rows(clean_tables)] == ["addr:c"]  # 키 오류는 캐시하지 않는다


def test_clean_keyword_removes_unsafe_characters():
    assert clean_keyword("가상로 12 [본관] % 3층") == "가상로 12 본관 3층"


def test_throttled_response_is_retried_and_not_cached(clean_tables):
    bodies = iter([error("E0007", "짧은 시간동안 다량의 주소검색 요청이 있습니다."),
                   load("search_one.json")])

    def handler(req):
        if req.url.path.endswith("addrLinkApi.do"):
            return httpx.Response(200, json=next(bodies))
        return httpx.Response(200, json=load("coord.json"))

    g = Juso(clean_tables, "S", "C", transport=httpx.MockTransport(handler), backoff=0, interval=0)
    assert g.geocode("addr:t", "가상로 12").status == "ok"

    with pytest.raises(ApiError, match="E0007"):
        juso(clean_tables, error("E0007", "다량 요청")).geocode("addr:u", "가상로 13")
    assert [r.addr_key for r in cache_rows(clean_tables)] == ["addr:t"]
