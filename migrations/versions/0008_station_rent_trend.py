"""mart_station_rent_trend (SPEC 5.2, FR-HOUS-04, decisions/007 9번)

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-13
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 역세권 원룸 시세의 최근 24개월 추이. grain은 month(계약 달) 또는 quarter(기준월부터 3개월씩
    # 거꾸로 묶은 구간), ym은 구간의 마지막 달이다. 배포 DB에는 rent_contract가 없어 미리 집계한다
    op.execute("""
    CREATE TABLE mart_station_rent_trend (
      station_id        INT NOT NULL,
      period_end_ym     INT NOT NULL,
      grain             VARCHAR(7) NOT NULL,
      ym                INT NOT NULL,
      n_monthly         INT NOT NULL,
      monthly_p25       INT, monthly_median INT, monthly_p75 INT,
      n_jeonse          INT NOT NULL,
      jeonse_median_man INT,
      PRIMARY KEY (station_id, period_end_ym, grain, ym)
    )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE mart_station_rent_trend")
