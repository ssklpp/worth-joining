from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings
from app.core.db import connect_args, make_engine

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def migrated_db() -> str:
    """세션 시작 시 테스트 DB를 비우고 `alembic upgrade head`를 한 번 실행한다(SPEC Phase 0)."""
    url = settings.test_database_url
    if not url:
        pytest.fail("TEST_DATABASE_URL이 비어 있다. .env를 확인한다")
    sync_url = url.replace("+asyncmy", "+pymysql")

    engine = create_engine(sync_url, connect_args=connect_args(settings.db_ssl_verify))
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in inspect(conn).get_table_names():
            conn.execute(text(f"DROP TABLE `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    engine.dispose()

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(cfg, "head")
    return url


@pytest.fixture
async def db(migrated_db: str):
    """테스트마다 트랜잭션을 열고 끝나면 롤백한다."""
    engine = make_engine(migrated_db)
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()
    await engine.dispose()
