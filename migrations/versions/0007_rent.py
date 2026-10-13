"""역세권 전월세: raw_rent_contract, station, building, rent_contract, conversion_rate,
company_station, mart_station_rent (SPEC 5.2, Phase 9, decisions/007)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-13
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 원본 23열을 글자 그대로 보관한다(서울 열린데이터광장 OA-21276 CSV, 2026 파일은 머리글 이름만 다르다).
    # 연도 파일끼리 기간이 겹치므로 접수연도를 뺀 원본 필드의 row_hash로 한 번만 넣는다
    op.execute("""
    CREATE TABLE raw_rent_contract (
      raw_id         BIGINT AUTO_INCREMENT PRIMARY KEY,
      run_id         BIGINT NOT NULL,
      row_hash       CHAR(32) NOT NULL,
      receipt_year   VARCHAR(4),
      sgg_code       VARCHAR(5),
      sgg_name       VARCHAR(20),
      bjdong_code    VARCHAR(5),
      bjdong_name    VARCHAR(40),
      jibun_type     VARCHAR(1),
      jibun_type_name VARCHAR(10),
      main_no        VARCHAR(4),
      sub_no         VARCHAR(4),
      floor          VARCHAR(5),
      contract_date  VARCHAR(8),
      rent_type      VARCHAR(4),
      area_m2        VARCHAR(12),
      deposit_man    VARCHAR(12),
      monthly_man    VARCHAR(12),
      building_name  VARCHAR(200),
      build_year     VARCHAR(4),
      house_type     VARCHAR(10),
      contract_term  VARCHAR(20),
      new_or_renew   VARCHAR(4),
      renewal_right  VARCHAR(4),
      prev_deposit   VARCHAR(12),
      prev_monthly   VARCHAR(12),
      UNIQUE KEY uk_raw_rent (row_hash),
      KEY ix_raw_rent_date (contract_date)
    )
    """)
    # 물리적 역 하나가 한 행이다(환승역의 노선별 행을 묶는다, decisions/007). station_key는 정규화한 역 이름
    op.execute("""
    CREATE TABLE station (
      station_id   INT AUTO_INCREMENT PRIMARY KEY,
      station_key  VARCHAR(50) NOT NULL,
      station_name VARCHAR(50) NOT NULL,
      line_names   VARCHAR(300) NOT NULL,  -- LINES는 예약어(TS-023)
      pt           POINT NOT NULL,
      UNIQUE KEY uk_station (station_key),
      SPATIAL INDEX sx_station (pt)
    )
    """)
    # addr_key: 자치구코드-법정동코드-지번구분-본번-부번 (예: 11710-10100-1-183-4)
    op.execute("""
    CREATE TABLE building (
      building_id INT AUTO_INCREMENT PRIMARY KEY,
      addr_key    VARCHAR(200) NOT NULL,
      house_type  ENUM('연립다세대','오피스텔') NOT NULL,
      build_year  SMALLINT,
      pt          POINT NOT NULL,
      UNIQUE KEY uk_building (addr_key, house_type),
      SPATIAL INDEX sx_building (pt)
    )
    """)
    # 월 파티션은 pipeline/rent/partitions.py가 pmax를 나눠 만든다(SPEC 7장 파티션 순환)
    op.execute("""
    CREATE TABLE rent_contract (
      contract_id BIGINT AUTO_INCREMENT,
      contract_ym INT NOT NULL,
      row_hash    CHAR(32) NOT NULL,
      addr_key    VARCHAR(200) NOT NULL,
      building_id INT NULL,
      house_type  ENUM('연립다세대','오피스텔') NOT NULL,
      area_m2     DECIMAL(7,2) NOT NULL,
      deposit_man INT NOT NULL,
      monthly_man INT NOT NULL,
      floor       SMALLINT,
      PRIMARY KEY (contract_id, contract_ym),
      UNIQUE KEY uk_row (row_hash, contract_ym),
      KEY ix_bld_ym (building_id, contract_ym),
      KEY ix_addr (addr_key)
    )
    PARTITION BY RANGE (contract_ym) (
      PARTITION pmax VALUES LESS THAN MAXVALUE
    )
    """)
    op.execute("""
    CREATE TABLE conversion_rate (
      ym        INT PRIMARY KEY,
      rate_year DECIMAL(5,4) NOT NULL
    )
    """)
    op.execute("""
    CREATE TABLE company_station (
      company_id INT NOT NULL,
      station_id INT NOT NULL,
      distance_m INT NOT NULL,
      rnk        TINYINT NOT NULL,
      PRIMARY KEY (company_id, station_id)
    )
    """)
    # window_months는 6 · 12 · 24(docs/04 D7). period_end_ym은 신고가 끝난 달(decisions/007)
    op.execute("""
    CREATE TABLE mart_station_rent (
      station_id         INT NOT NULL,
      period_end_ym      INT NOT NULL,
      window_months      TINYINT NOT NULL,
      n_monthly          INT NOT NULL,
      n_jeonse           INT NOT NULL,
      monthly_p25        INT, monthly_median INT, monthly_p75 INT,
      deposit_median_man INT,
      rent_median_man    INT,
      jeonse_p25_man     INT, jeonse_median_man INT, jeonse_p75_man INT,
      PRIMARY KEY (station_id, period_end_ym, window_months)
    )
    """)


def downgrade() -> None:
    for table in ("mart_station_rent", "company_station", "conversion_rate", "rent_contract",
                  "building", "station", "raw_rent_contract"):
        op.execute(f"DROP TABLE {table}")
