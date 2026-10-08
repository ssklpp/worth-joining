from alembic import context
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.db import connect_args

url = context.config.get_main_option("sqlalchemy.url") or settings.database_url_sync


def run_migrations_offline() -> None:
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(url, connect_args=connect_args(settings.db_ssl_verify))
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
