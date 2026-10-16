"""전월세전환율에 시도(sido) 추가: 서울 11 · 경기 41 (SPEC 5.2, decisions/010)

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-16
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 기존 행은 모두 서울 값이라 기본값 '11'로 채운다. 시도도 PK에 넣는다.
    # q5 · q5t는 건물 addr_key 앞 2자리(시도)와 같은 행을 쓴다
    op.execute("""
    ALTER TABLE conversion_rate
      ADD COLUMN sido VARCHAR(2) NOT NULL DEFAULT '11' FIRST,
      DROP PRIMARY KEY,
      ADD PRIMARY KEY (sido, ym)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM conversion_rate WHERE sido <> '11'")
    op.execute("""
    ALTER TABLE conversion_rate
      DROP PRIMARY KEY,
      DROP COLUMN sido,
      ADD PRIMARY KEY (ym)
    """)
