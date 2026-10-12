"""외부 API 공통 클라이언트 (SPEC 4장 공통 수집기 요구사항).

- httpx 타임아웃 30초, 5xx · 네트워크 오류는 지수 백오프로 3회 재시도
- 호출마다 api_call_log(source, call_date, count)를 올리고, 한도에 닿으면 QuotaExceeded.
  한도는 키마다 따로라서 source에 키 해시 앞 8자리를 붙여 센다(예: dart:1a2b3c4d).
  키 원문은 남기지 않는다
- 오류 메시지 · 로그에 API 키가 남지 않게 가린다(ingestion_log.message에 들어가므로)
"""

import hashlib
import logging
import time
from datetime import date

import httpx
from sqlalchemy import Engine, text

# httpx는 INFO 로그에 쿼리 문자열(키 포함) 전체 URL을 찍는다
logging.getLogger("httpx").setLevel(logging.WARNING)

TIMEOUT = 30.0
RETRIES = 3


class QuotaExceeded(RuntimeError):
    """오늘 호출 한도에 닿았다. 다음 실행에서 이어서 수집한다."""


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, engine: Engine, source: str, daily_limit: int, secret: str = "",
                 transport: httpx.BaseTransport | None = None, backoff: float = 1.0):
        self.engine, self.daily_limit = engine, daily_limit
        key_id = hashlib.sha256(secret.encode()).hexdigest()[:8] if secret else ""
        self.source = f"{source}:{key_id}" if secret else source
        self.secret, self.backoff = secret, backoff
        self.client = httpx.Client(timeout=TIMEOUT, transport=transport)

    def calls_today(self) -> int:
        with self.engine.connect() as conn:
            return conn.execute(text(
                "SELECT count FROM api_call_log WHERE source = :s AND call_date = :d"
            ), {"s": self.source, "d": date.today()}).scalar() or 0

    def _count_call(self) -> None:
        # 적재 트랜잭션과 따로 커밋한다. 적재가 롤백돼도 쓴 호출 수는 남아야 한다
        with self.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO api_call_log (source, call_date, count) VALUES (:s, :d, 1)"
                " ON DUPLICATE KEY UPDATE count = count + 1"
            ), {"s": self.source, "d": date.today()})

    def _redact(self, message: str) -> str:
        return message.replace(self.secret, "***") if self.secret else message

    def get(self, url: str, params: dict) -> httpx.Response:
        """재시도 한 번도 호출 한 건으로 센다(한도는 서버가 받은 요청 수 기준)."""
        last: Exception | None = None
        for attempt in range(RETRIES + 1):
            if self.calls_today() >= self.daily_limit:
                raise QuotaExceeded(f"{self.source} 오늘 호출 한도 {self.daily_limit}건에 닿았다")
            self._count_call()
            try:
                response = self.client.get(url, params=params)
                if response.status_code < 500:
                    response.raise_for_status()
                    return response
                last = ApiError(f"HTTP {response.status_code}")
            except httpx.HTTPStatusError as e:  # 4xx는 재시도해도 같다
                raise ApiError(self._redact(f"HTTP {e.response.status_code}: {e}")) from None
            except httpx.TransportError as e:
                last = ApiError(self._redact(f"{type(e).__name__}: {e}"))
            if attempt < RETRIES:
                time.sleep(self.backoff * 2 ** attempt)
        raise last

    def close(self) -> None:
        self.client.close()
