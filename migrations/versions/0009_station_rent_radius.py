"""역세권 시세 반경(radius_m) 추가: 500m · 750m (SPEC 5.2, decisions/009)

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-15
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

TABLES = {
    "mart_station_rent": "station_id, period_end_ym, {r}window_months",
    "mart_station_rent_trend": "station_id, period_end_ym, {r}grain, ym",
}


def upgrade() -> None:
    # 기존 행은 모두 500m로 집계한 값이라 기본값 500으로 채운다. 반경도 PK에 넣는다
    for table, pk in TABLES.items():
        op.execute(f"""
        ALTER TABLE {table}
          ADD COLUMN radius_m SMALLINT NOT NULL DEFAULT 500 AFTER period_end_ym,
          DROP PRIMARY KEY,
          ADD PRIMARY KEY ({pk.format(r="radius_m, ")})
        """)


def downgrade() -> None:
    for table, pk in TABLES.items():
        op.execute(f"DELETE FROM {table} WHERE radius_m <> 500")
        op.execute(f"""
        ALTER TABLE {table}
          DROP PRIMARY KEY,
          DROP COLUMN radius_m,
          ADD PRIMARY KEY ({pk.format(r="")})
        """)
