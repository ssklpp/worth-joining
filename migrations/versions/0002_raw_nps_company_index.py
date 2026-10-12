"""raw_nps_workplace에 (snapshot_ym, biz_no6, name_norm) 인덱스 추가

raw가 100만 행을 넘자 11.4 옵티마이저가 company를 먼저 읽고 raw를 반복 전체 스캔해
한 달 core 적재가 10분 넘게 걸렸다(troubleshooting TS-012). 월 조건과 회사 조인을
이 인덱스 하나로 받는다.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-12
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE raw_nps_workplace"
        " ADD KEY ix_snapshot_company (snapshot_ym, biz_no6, name_norm),"
        " DROP KEY ix_snapshot"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE raw_nps_workplace"
        " ADD KEY ix_snapshot (snapshot_ym),"
        " DROP KEY ix_snapshot_company"
    )
