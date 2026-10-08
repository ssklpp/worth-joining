import ssl

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import settings


def connect_args(verify: bool) -> dict:
    """배포(DB_SSL_VERIFY=true)는 인증서를 검증하는 TLS로 접속한다(SPEC 3장).

    로컬(false)은 TLS 없이 접속한다. asyncmy의 TLS 전환이 Windows 기본 이벤트 루프(Proactor)에서
    `WinError 87`로 실패하기 때문이다. 로컬호스트 접속이라 평문이어도 위험이 없다.
    """
    return {"ssl": ssl.create_default_context()} if verify else {}


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url, pool_pre_ping=True, connect_args=connect_args(settings.db_ssl_verify)
    )


engine = make_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
