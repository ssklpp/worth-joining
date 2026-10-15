"""juso 지오코더: 검색 API → 좌표제공 API → EPSG:4326 → geocode_cache (SPEC Phase 8-1).

Phase 8(회사 좌표)과 Phase 9(전월세 건물)가 같이 쓴다. 캐시에 있는 주소는 다시 부르지 않고,
실패도 사유와 함께 캐시한다. DB에 저장하는 좌표는 이 모듈이 juso에서 얻은 것뿐이다(SPEC 4장).

응답 형식은 juso 개발자센터 문서 기준이다. 키를 받으면 실제 응답 한 건으로 필드를 확인한다(TS-018).
"""

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import Engine, text

from pipeline.common.http import ApiClient, ApiError
from pipeline.geocode.projection import utmk_to_wgs84

log = logging.getLogger(__name__)

SEARCH_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"
COORD_URL = "https://business.juso.go.kr/addrlink/addrCoordApi.do"
PROVIDER = "juso"
DAILY_LIMIT = 50_000  # 승인키 종류별 한도가 문서에 없다. api_call_log로 실제 사용량을 본다
# 키 · 시스템 오류는 수집을 멈춘다. 그 밖의 오류(검색어 형식 등)는 그 주소만 실패로 캐시한다
FATAL = {"E0001": "승인되지 않은 키", "E0014": "키 사용 기간 만료", "-999": "시스템 오류"}
# 짧은 시간에 몰아 부르면 E0007(다량 요청)을 준다. 일시적이므로 기다렸다 다시 부르고 캐시하지 않는다
THROTTLED = "E0007"
WAITS = (1, 2, 4, 8, 16)  # 초
INTERVAL = 0.15  # 호출 사이 기본 간격(초)
# juso 검색어에 쓸 수 없는 문자(특수문자 · SQL 예약 기호)
UNSAFE = re.compile(r"[%=><\[\]{}\"'`;|\\^~!?*+$#@&]")


@dataclass
class Geocode:
    """juso 변환 결과(geocode_cache 한 행과 같은 모양). status가 fail이면 좌표 대신 fail_reason이
    있다.
    """
    status: str  # ok | fail
    lon: float | None = None
    lat: float | None = None
    accuracy: str | None = None
    fail_reason: str | None = None


Picker = Callable[[list[dict]], dict | None]


def only_one(results: list[dict]) -> dict | None:
    """결과가 정확히 1건일 때만 채택한다(decisions/004: 틀린 건물보다 대략 위치가 낫다)."""
    return results[0] if len(results) == 1 else None


def clean_keyword(keyword: str) -> str:
    """검색 API가 거부하는 특수문자를 공백으로 바꾸고 연속 공백을 하나로 줄인다."""
    return " ".join(UNSAFE.sub(" ", keyword).split())


class Juso:
    """주소정보누리집 검색 API → 좌표제공 API 두 단계 변환.
    성공 · 실패 모두 geocode_cache에 남겨 같은 주소를 다시 부르지 않는다(SPEC 4장).
    """
    def __init__(self, engine: Engine, search_key: str, coord_key: str, transport=None,
                 backoff: float = 1.0, interval: float = INTERVAL):
        self.engine, self.interval = engine, interval
        self.search_key, self.coord_key = search_key, coord_key
        self.search_api = ApiClient(engine, "juso_search", DAILY_LIMIT, secret=search_key,
                                    transport=transport, backoff=backoff)
        self.coord_api = ApiClient(engine, "juso_coord", DAILY_LIMIT, secret=coord_key,
                                   transport=transport, backoff=backoff)

    def close(self) -> None:
        self.search_api.close()
        self.coord_api.close()

    @staticmethod
    def _check(body: dict) -> tuple[str, str]:
        common = body.get("results", {}).get("common", {})
        code, message = str(common.get("errorCode", "")), common.get("errorMessage", "")
        if code in FATAL:
            raise ApiError(f"juso {code} {FATAL[code]}: {message}")
        return code, message

    def _call(self, api: ApiClient, url: str, params: dict) -> tuple[dict, str, str]:
        """E0007이면 간격을 늘려 다시 부른다. 끝내 풀리지 않으면 ApiError(캐시하지 않는다)."""
        for wait in (*WAITS, None):
            time.sleep(self.interval)
            body = api.get(url, params).json()
            code, message = self._check(body)
            if code != THROTTLED:
                return body, code, message
            if wait is None:
                raise ApiError(f"juso {code} 다량 요청 제한이 풀리지 않는다: {message}")
            log.info("juso %s, %s초 뒤 다시 부른다", code, wait)
            time.sleep(wait if self.interval else 0)
        raise AssertionError("unreachable")

    def search(self, keyword: str, count: int = 10) -> tuple[list[dict], str | None]:
        """(결과, 실패 사유). 검색어 형식 오류 등은 사유로 돌려준다."""
        body, code, message = self._call(self.search_api, SEARCH_URL, {
            "confmKey": self.search_key, "keyword": clean_keyword(keyword), "currentPage": 1,
            "countPerPage": count, "resultType": "json"})
        if code != "0":
            return [], f"search {code} {message}"[:100]
        return body["results"].get("juso") or [], None

    def coordinate(self, item: dict) -> tuple[float, float] | None:
        """검색 결과 한 건의 건물 출입구 좌표(경도, 위도)."""
        body, code, _ = self._call(self.coord_api, COORD_URL, {
            "confmKey": self.coord_key, "admCd": item["admCd"], "rnMgtSn": item["rnMgtSn"],
            "udrtYn": item["udrtYn"], "buldMnnm": item["buldMnnm"], "buldSlno": item["buldSlno"],
            "resultType": "json"})
        found = body["results"].get("juso") or []
        if code != "0" or not found or not found[0].get("entX"):
            return None
        return utmk_to_wgs84(float(found[0]["entX"]), float(found[0]["entY"]))

    def cached(self, addr_key: str) -> Geocode | None:
        """geocode_cache에 있으면 그 결과(실패 포함), 없으면 None."""
        with self.engine.connect() as conn:
            row = conn.execute(text(
                "SELECT status, lon, lat, accuracy, fail_reason FROM geocode_cache"
                " WHERE addr_key = :k"
            ), {"k": addr_key}).first()
        if row is None:
            return None
        return Geocode(row.status, None if row.lon is None else float(row.lon),
                       None if row.lat is None else float(row.lat), row.accuracy, row.fail_reason)

    def _save(self, addr_key: str, g: Geocode) -> Geocode:
        with self.engine.begin() as conn:
            conn.execute(text("""
                REPLACE INTO geocode_cache
                  (addr_key, status, lon, lat, accuracy, provider, fail_reason, requested_at)
                VALUES (:k, :s, :lon, :lat, :acc, :p, :why, NOW())
            """), {"k": addr_key[:200], "s": g.status, "lon": g.lon, "lat": g.lat,
                   "acc": g.accuracy, "p": PROVIDER, "why": g.fail_reason})
        return g

    def geocode(self, addr_key: str, keyword: str, pick: Picker = only_one) -> Geocode:
        """addr_key로 캐시를 보고, 없으면 keyword로 검색해 pick이 고른 건물의 좌표를 저장한다."""
        hit = self.cached(addr_key)
        if hit is not None:
            return hit
        results, reason = self.search(keyword)
        if reason:
            return self._save(addr_key, Geocode("fail", fail_reason=reason))
        if not results:
            return self._save(addr_key, Geocode("fail", fail_reason="no_result"))
        chosen = pick(results)
        if chosen is None:
            return self._save(addr_key, Geocode("fail", fail_reason=f"ambiguous:{len(results)}"))
        point = self.coordinate(chosen)
        if point is None:
            return self._save(addr_key, Geocode("fail", fail_reason="no_coordinate"))
        lon, lat = point
        return self._save(addr_key, Geocode("ok", round(lon, 7), round(lat, 7), "building"))
