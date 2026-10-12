"""dart_corp, company_dart_link, dart_financial (SPEC 5.2, Phase 5)

dart_corp · company_dart_link는 SPEC 5.2 DDL에 매칭용 인덱스를 더했다.
dart_financial은 docs/04 3장 제안 DDL이다.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-12
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # corp_name_norm: 정확 매칭(bizr6 + 이름)과 company.json 호출 대상 고르기에 쓴다
    op.execute("""
    CREATE TABLE dart_corp (
      corp_code      CHAR(8) PRIMARY KEY,
      corp_name      VARCHAR(200) NOT NULL,
      corp_name_norm VARCHAR(200) NOT NULL,
      stock_code     CHAR(6),
      bizr_no        VARCHAR(10),
      corp_cls       CHAR(1),
      adres          VARCHAR(300),
      bizr6          CHAR(6) AS (LEFT(bizr_no, 6)) PERSISTENT,
      KEY ix_bizr6 (bizr6),
      KEY ix_name_norm (corp_name_norm)
    )
    """)
    op.execute("""
    CREATE TABLE company_dart_link (
      company_id  INT PRIMARY KEY,
      corp_code   CHAR(8) NOT NULL,
      match_type  ENUM('exact','fuzzy','manual') NOT NULL,
      match_score DECIMAL(4,3),
      KEY ix_corp (corp_code)
    )
    """)
    op.execute("""
    CREATE TABLE dart_financial (
      corp_code         CHAR(8) NOT NULL,
      bsns_year         SMALLINT NOT NULL,
      reprt_code        CHAR(5) NOT NULL,
      revenue           BIGINT,
      operating_income  BIGINT,
      net_income        BIGINT,
      total_liabilities BIGINT,
      total_equity      BIGINT,
      PRIMARY KEY (corp_code, bsns_year, reprt_code)
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE dart_financial")
    op.execute("DROP TABLE company_dart_link")
    op.execute("DROP TABLE dart_corp")
