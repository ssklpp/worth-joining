"""dart_corp.fetched_at: company.json 조회 시각

호출 대상(약 2.2만)이 하루 한도 20,000건을 넘어 이틀에 나눠 받는다. 사업자번호가 없는
법인도 있어 bizr_no만으로는 조회 여부를 알 수 없으므로, 조회한 시각을 따로 둔다.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-12
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE dart_corp ADD COLUMN fetched_at DATETIME")


def downgrade() -> None:
    op.execute("ALTER TABLE dart_corp DROP COLUMN fetched_at")
