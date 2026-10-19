"""mart_company_monthly에 snapshot_ym 인덱스 (docs/08 I-02)

계산 방법 API(/meta/methodology)의 데이터 기간 `MIN(snapshot_ym)`이 PK(company_id, snapshot_ym)로는
182만 행을 모두 읽어 배포에서 약 2초 걸렸다. 월 인덱스가 있으면 끝값만 읽는다.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-19
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE mart_company_monthly ADD KEY ix_snapshot_ym (snapshot_ym)")


def downgrade() -> None:
    op.execute("ALTER TABLE mart_company_monthly DROP KEY ix_snapshot_ym")
