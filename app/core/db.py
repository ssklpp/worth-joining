import ssl

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from app.core.config import settings


def ssl_context(verify: bool) -> ssl.SSLContext:
    """MariaDB 11.4는 서버 인증서를 자동 생성한다. 로컬은 검증을 끄고, 배포는 검증한다(SPEC 3장)."""
    ctx = ssl.create_default_context()
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        url,
        pool_pre_ping=True,
        connect_args={"ssl": ssl_context(settings.db_ssl_verify)},
    )


engine = make_engine(settings.database_url)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
