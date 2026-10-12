"""geocode_cache, company_location (SPEC 5.2, Phase 8-1 · 8-2, decisions/004)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-12
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # addr_key 예: 'dong:1117013100', 'road:11170:독서당로14길', 'addr:서울특별시 강서구 하늘길 260'
    op.execute("""
    CREATE TABLE geocode_cache (
      addr_key     VARCHAR(200) PRIMARY KEY,
      status       ENUM('ok','fail') NOT NULL,
      lon          DECIMAL(10,7),
      lat          DECIMAL(10,7),
      accuracy     ENUM('building','road','dong'),
      provider     VARCHAR(20) NOT NULL,
      fail_reason  VARCHAR(100),
      requested_at DATETIME NOT NULL
    )
    """)
    op.execute("""
    CREATE TABLE company_location (
      company_id   INT PRIMARY KEY,
      lon          DECIMAL(10,7) NOT NULL,
      lat          DECIMAL(10,7) NOT NULL,
      accuracy     ENUM('building','road','dong') NOT NULL,
      basis        ENUM('dart_hq','name_search','road','dong') NOT NULL,
      addr_key     VARCHAR(200) NOT NULL,
      refreshed_at DATETIME NOT NULL
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE company_location")
    op.execute("DROP TABLE geocode_cache")
