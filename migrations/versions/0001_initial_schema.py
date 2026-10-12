"""초기 스키마: 운영 · 기준 · raw · core(회사) 테이블 (SPEC 5.2, Phase 2-1 · 2-2)

Revision ID: 0001
Revises:
Create Date: 2026-10-12
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = [
    # 운영 (docs/04 3장 제안)
    """
    CREATE TABLE ingestion_log (
      run_id      BIGINT AUTO_INCREMENT PRIMARY KEY,
      source      VARCHAR(30) NOT NULL,
      target      VARCHAR(30),
      checksum    CHAR(64),
      status      ENUM('running','success','failed','skipped') NOT NULL,
      row_count   INT,
      message     VARCHAR(500),
      started_at  DATETIME NOT NULL,
      finished_at DATETIME,
      KEY ix_source_checksum (source, checksum, status)
    )
    """,
    """
    CREATE TABLE api_call_log (
      source    VARCHAR(30) NOT NULL,
      call_date DATE NOT NULL,
      count     INT NOT NULL DEFAULT 0,
      PRIMARY KEY (source, call_date)
    )
    """,
    # 기준
    """
    CREATE TABLE nps_rate (
      valid_from_ym INT PRIMARY KEY,
      valid_to_ym   INT NOT NULL,
      rate          DECIMAL(5,4) NOT NULL,
      income_cap    INT NOT NULL
    )
    """,
    """
    CREATE TABLE industry (
      industry_code CHAR(6) PRIMARY KEY,
      industry_name VARCHAR(100) NOT NULL
    )
    """,
    """
    CREATE TABLE region (
      region_code  CHAR(5) PRIMARY KEY,
      sido_name    VARCHAR(20) NOT NULL,
      sigungu_name VARCHAR(30) NOT NULL
    )
    """,
    # raw: 국민연금 CSV 한 행 = 한 행. 필드 이름은 pipeline/nps/columns.py
    """
    CREATE TABLE raw_nps_workplace (
      raw_id          BIGINT AUTO_INCREMENT PRIMARY KEY,
      snapshot_ym     INT NOT NULL,
      run_id          BIGINT NOT NULL,
      data_ym         VARCHAR(7) NOT NULL,
      workplace_name  VARCHAR(200) NOT NULL,
      biz_no6         VARCHAR(6) NOT NULL,
      status_code     VARCHAR(1) NOT NULL,
      zip_code        VARCHAR(10),
      jibun_address   VARCHAR(300),
      road_address    VARCHAR(300),
      legal_dong_code VARCHAR(10),
      admin_dong_code VARCHAR(10),
      sido_code       VARCHAR(2),
      sigungu_code    VARCHAR(3),
      emd_code        VARCHAR(3),
      form_type       VARCHAR(1),
      industry_code   VARCHAR(6),
      industry_name   VARCHAR(200),
      joined_on       DATE,
      rejoined_on     DATE,
      left_on         DATE,
      members         INT NOT NULL,
      billed_amount   BIGINT NOT NULL,
      new_members     INT NOT NULL,
      lost_members    INT NOT NULL,
      name_norm       VARCHAR(200) NOT NULL,
      KEY ix_snapshot (snapshot_ym)
    )
    """,
    # core (회사)
    """
    CREATE TABLE company (
      company_id   INT AUTO_INCREMENT PRIMARY KEY,
      biz_no6      CHAR(6) NOT NULL,
      name_norm    VARCHAR(200) NOT NULL,
      display_name VARCHAR(200) NOT NULL,
      UNIQUE KEY uk_company (biz_no6, name_norm),
      KEY ix_name_prefix (name_norm)
    )
    """,
    """
    CREATE TABLE workplace (
      workplace_id    INT AUTO_INCREMENT PRIMARY KEY,
      company_id      INT NOT NULL,
      workplace_name  VARCHAR(200) NOT NULL,
      form_type       TINYINT NOT NULL,
      industry_code   CHAR(6),
      legal_dong_code CHAR(10),
      road_address    VARCHAR(300),
      addr_key        VARCHAR(200),
      joined_on       DATE,
      left_on         DATE,
      UNIQUE KEY uk_wp (company_id, workplace_name, legal_dong_code),
      KEY ix_industry (industry_code),
      FOREIGN KEY (company_id) REFERENCES company(company_id)
    )
    """,
    """
    CREATE TABLE workplace_monthly (
      workplace_id  INT NOT NULL,
      snapshot_ym   INT NOT NULL,
      members       INT NOT NULL,
      billed_amount BIGINT NOT NULL,
      new_members   INT NOT NULL,
      lost_members  INT NOT NULL,
      PRIMARY KEY (workplace_id, snapshot_ym)
    )
    PARTITION BY RANGE (snapshot_ym) (
      PARTITION p2025 VALUES LESS THAN (202601),
      PARTITION p2026 VALUES LESS THAN (202701),
      PARTITION pmax  VALUES LESS THAN MAXVALUE
    )
    """,
]

# SPEC 5.2 초기값. 2025-08 ~ 2026-08 월별 1인당 고지금액 최댓값으로 확인함(docs/profiling.md 7장)
NPS_RATE_SEED = """
INSERT INTO nps_rate (valid_from_ym, valid_to_ym, rate, income_cap) VALUES
  (202407, 202506, 0.0900, 6170000),
  (202507, 202512, 0.0900, 6370000),
  (202601, 202606, 0.0950, 6370000),
  (202607, 202706, 0.0950, 6590000)
"""

DROP_ORDER = [
    "workplace_monthly", "workplace", "company", "raw_nps_workplace",
    "region", "industry", "nps_rate", "api_call_log", "ingestion_log",
]


def upgrade() -> None:
    for ddl in TABLES:
        op.execute(ddl)
    op.execute(NPS_RATE_SEED)


def downgrade() -> None:
    for table in DROP_ORDER:
        op.execute(f"DROP TABLE {table}")
