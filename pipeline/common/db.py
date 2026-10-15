"""파이프라인 · 적재용 동기 DB 엔진(pymysql). API는 app/core/db.py의 비동기 엔진을 쓴다."""

from sqlalchemy import Engine, create_engine

from app.core.config import settings
from app.core.db import connect_args


def sync_engine(url: str | None = None) -> Engine:
    """파이프라인 · 적재용 동기 엔진(pymysql).

    LOAD DATA LOCAL INFILE을 쓰므로 local_infile을 켠다.
    """
    return create_engine(
        url or settings.database_url_sync,
        pool_pre_ping=True,
        connect_args={**connect_args(settings.db_ssl_verify), "local_infile": True},
    )
