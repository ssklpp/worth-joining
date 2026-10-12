"""mart_company_monthly, mart_company_summary (SPEC 5.2, Phase 3)

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-12
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE mart_company_monthly (
      company_id     INT NOT NULL,
      snapshot_ym    INT NOT NULL,
      members        INT NOT NULL,
      new_members    INT NOT NULL,
      lost_members   INT NOT NULL,
      hire_rate      DECIMAL(6,4),
      quit_rate      DECIMAL(6,4),
      avg_salary_est INT,
      PRIMARY KEY (company_id, snapshot_ym)
    )
    """)
    op.execute("""
    CREATE TABLE mart_company_summary (
      company_id      INT PRIMARY KEY,
      industry_code   CHAR(6),
      region_code     CHAR(5),
      rep_addr_key    VARCHAR(200),
      workplace_count SMALLINT NOT NULL,
      latest_ym       INT NOT NULL,
      members         INT NOT NULL,
      growth_12m      DECIMAL(7,4),
      quit_rate_12m   DECIMAL(6,4),
      avg_salary_est  INT,
      pct_growth      TINYINT,
      pct_stability   TINYINT,
      pct_salary      TINYINT,
      small_sample    BOOLEAN NOT NULL DEFAULT FALSE,
      short_history   BOOLEAN NOT NULL DEFAULT FALSE,
      KEY ix_ind_salary (industry_code, avg_salary_est),
      KEY ix_ind_region (industry_code, region_code)
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE mart_company_summary")
    op.execute("DROP TABLE mart_company_monthly")
