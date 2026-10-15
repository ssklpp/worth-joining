"""API용 비동기 DB 엔진(asyncmy)과 라우터 의존성 `get_conn`.

파이프라인 · 적재는 동기 엔진(pipeline/common/db.py)을 쓰고, 둘 다 `connect_args()`로 TLS를 정한다.
"""

import ssl
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    create_async_engine,
)

from app.core.config import settings


def connect_args(verify: bool) -> dict:
    """배포(DB_SSL_VERIFY=true)는 인증서를 검증하는 TLS로 접속한다(SPEC 3장).

    로컬(false)은 TLS 없이 접속한다. asyncmy의 TLS 전환이 Windows 기본 이벤트 루프(Proactor)에서
    `WinError 87`로 실패하기 때문이다. 로컬호스트 접속이라 평문이어도 위험이 없다.
    """
    return {"ssl": ssl.create_default_context()} if verify else {}


def make_engine(url: str) -> AsyncEngine:
    """pool_pre_ping으로 끊긴 연결을 쓰기 전에 확인해 다시 연다. 테스트는 테스트 DB URL로 따로
    만든다.
    """
    return create_async_engine(
        url, pool_pre_ping=True, connect_args=connect_args(settings.db_ssl_verify)
    )


engine = make_engine(settings.database_url)


async def get_conn() -> AsyncIterator[AsyncConnection]:
    """라우터용 DB 연결(읽기 전용). 테스트는 이 의존성을 테스트 DB 트랜잭션으로 바꾼다."""
    async with engine.connect() as conn:
        yield conn
