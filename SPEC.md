# SPEC: 다닐만한가 (worth-joining)

공공데이터로 회사의 인원 추이·입퇴사율·추정 연봉을 보여주고, 채용공고(사람인)와 회사 근처 역세권 전월세 시세를 연결하는 구직자용 웹 서비스.

이 문서는 구현 지시서다. 4인 팀이 4개 트랙으로 나눠 병렬로 진행한다(12장). 각 단계의 완료 조건을 모두 만족해야 그 단계가 끝난 것으로 본다. 10장의 단계별 기간은 1인 작업량 기준이며, 실제 일정은 12.2의 일정표(2026-10-02 ~ 10-21)를 따른다. Phase 9 · 10은 기간 이후 과제다. 요구사항 ID · 우선순위(P0~P3) · User Story · Task 분해는 `docs/02_requirements.md`, API 명세와 외부 API 키 신청은 `docs/05_api_spec.md`를 따른다.

---

## 0. 작업 규칙

- AI 기능(LLM, RAG, 임베딩)은 사용하지 않는다.
- 통계 계산은 SQL로 작성한다. pandas는 파일 정제에만 쓴다.
- 모든 적재는 멱등이어야 한다. 같은 입력을 두 번 넣어도 결과 행 수와 값이 같아야 한다.
- 원본은 `raw_*` 테이블에 그대로 보존하고, 정제 규칙이 바뀌면 raw에서 다시 만든다.
- API는 `mart_*` 테이블만 읽는다. 무거운 집계를 요청 시점에 하지 않는다.
- 보험료율, 소득 상한, 전월세전환율 같은 기준값은 코드 상수로 두지 않고 테이블에 둔다.
- 추정값을 내려주는 응답에는 반드시 `flags`를 포함한다.
- API 키는 `.env`에만 두고 커밋하지 않는다.
- 모든 변경은 기능 브랜치 → PR → 리뷰 1명 이상 승인 → CI 통과 → main 병합 순서를 따른다. 커밋 메시지는 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/ko/v1.0.0/)(`<type>(<scope>): <설명>`)을 따른다. type은 `feat`, `fix`, `test`, `docs`, `chore`를 기본으로 하고 필요하면 `refactor`, `perf`, `style`, `ci`, `build`도 쓴다. 세부 규칙은 `CLAUDE.md` 팀 규칙을 따른다.
- 이슈와 PR에는 관련 요구사항 ID와 Task ID(docs/02_requirements.md 10장, 예: `T1-04`)를 적는다.

---

## 1. 기술 스택 (고정)

| 영역 | 사용 |
|---|---|
| 언어 | Python 3.12, TypeScript |
| 수집·가공 | httpx, pandas, openpyxl, rapidfuzz, pyproj, APScheduler |
| DB | MariaDB 11.4 LTS (InnoDB, utf8mb4). 로컬·CI·배포 모두 11.4로 통일 |
| 마이그레이션 | Alembic |
| 백엔드 | FastAPI, uvicorn, Pydantic v2, SQLAlchemy 2.0 async + asyncmy |
| 프론트엔드 | Next.js (App Router), Recharts, 네이버 지도 Web Dynamic Map (`react-naver-maps`) |
| 테스트 | pytest, pytest-asyncio, httpx AsyncClient, locust. DB 테스트는 로컬 테스트 DB(`worth_joining_test`), CI는 GitHub Actions 서비스 컨테이너(`mariadb:11.4`) |
| 배포 | Railway(api, pipeline cron, mariadb), Vercel(web), GitHub Actions(CI) |

---

## 2. 저장소 구조

```
worth-joining/
├─ app/
│  ├─ main.py
│  ├─ core/            # config.py (pydantic-settings), db.py
│  ├─ routers/         # companies.py, industries.py, map.py, stations.py, meta.py
│  ├─ schemas/
│  ├─ repositories/    # SQL은 text()로 직접 작성
│  └─ services/        # flags 생성
├─ pipeline/
│  ├─ common/          # http 클라이언트(재시도·호출 수 집계), normalize.py, ingestion_log
│  ├─ nps/  dart/  rent/  stations/  geocode/  saramin/
│  ├─ refresh_mart.py
│  └─ scheduler.py
├─ sql/                # mart 갱신 SQL (q1_company_monthly.sql ...)
├─ migrations/
├─ web/
├─ tests/  unit/  sql/  api/  fixtures/
├─ docs/              # 01_project_overview, 02_requirements, 03_ui_design, 04_database_design, 05_api_spec, 06_architecture, profiling, matching, explain, performance, validation, runbook, decisions/
├─ .github/workflows/ci.yml
├─ .github/CODEOWNERS
├─ .github/pull_request_template.md
├─ docker-compose.yml   # 선택: Docker로 로컬 DB를 띄울 때만 사용
├─ .env.example
├─ README.md
└─ SPEC.md
```

---

## 3. 환경 변수

```dotenv
DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/worth_joining
DATABASE_URL_SYNC=mysql+pymysql://user:password@localhost:3306/worth_joining
TEST_DATABASE_URL=mysql+asyncmy://user:password@localhost:3306/worth_joining_test
DB_SSL_VERIFY=false            # 로컬 11.4 자동 생성 인증서 검증 여부. 배포 환경은 true
DATA_GO_KR_SERVICE_KEY=          # 공공데이터포털 (국민연금 Open API 등)
SEOUL_OPENDATA_KEY=              # 서울 열린데이터광장 인증키 (전월세 Open API)
OPENDART_API_KEY=
JUSO_SEARCH_KEY=                 # 주소정보누리집 검색 API (Phase 8 지도 회사 좌표부터 사용)
JUSO_COORD_KEY=                  # 주소정보누리집 좌표제공 API
SARAMIN_ACCESS_KEY=
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=   # NCP Maps Client ID (도메인 등록으로 보호)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

키가 비어 있는 데이터 소스의 수집기는 실패하지 말고 경고 로그를 남기고 건너뛴다.

### 로컬 DB 준비 (Docker 없이, 설치된 MariaDB 11.4 사용)

```sql
CREATE DATABASE worth_joining      CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE worth_joining_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'wj'@'localhost' IDENTIFIED BY '...';
GRANT ALL PRIVILEGES ON worth_joining.*      TO 'wj'@'localhost';
GRANT ALL PRIVILEGES ON worth_joining_test.* TO 'wj'@'localhost';
```

- `LOAD DATA LOCAL INFILE`을 쓰므로 서버 `local_infile=ON`, 클라이언트 연결에 `local_infile=True`를 설정한다.
- MariaDB 11.4는 서버 인증서를 자동 생성하고 클라이언트가 기본으로 검증한다. 로컬에서는 `DB_SSL_VERIFY=false`로 검증을 끄고(CLI는 `--skip-ssl-verify-server-cert`), 배포 환경에서는 검증한다. `app/core/db.py`에서 이 값으로 드라이버 SSL 옵션을 구성한다. asyncmy는 Windows 기본 이벤트 루프에서 TLS 전환이 실패하므로 `false`일 때는 TLS 없이 접속한다.

---

## 4. 데이터 소스와 수집 규칙

| 소스 | 형식 | 수집 주기 | 비고 |
|---|---|---|---|
| 국민연금 가입 사업장 내역 | CSV(ZIP), 월별 스냅샷 | 월 1회 | 인코딩 CP949 가능성. 사업자번호는 앞 6자리만 제공 |
| OpenDART corpCode.xml | ZIP(XML) | 월 1회 | 회사 고유번호 마스터 |
| OpenDART company.json | JSON | 필요 시 | 일 20,000건 한도. bizr_no 획득용 |
| OpenDART fnlttSinglAcnt.json | JSON | 분기 1회 | reprt_code 11011(사업보고서) 우선 |
| 서울시 부동산 전월세가 정보 (서울 열린데이터광장 OA-21276) | 연도별 CSV 파일 + Open API | 일 1회 갱신, 수집은 주 1회 | 서울 전체 자치구. 초기 적재는 CSV(2024 · 2025 · 2026), 증분은 Open API(최근 3년만 제공). 최근 24개월만 보관. [https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do](https://data.seoul.go.kr/dataList/OA-21276/S/1/datasetView.do) |
| 전국도시철도역사정보 표준데이터 | XLSX | 연 1회 | 위도·경도 포함 |
| 주소정보누리집 검색 API + 좌표제공 API | REST | 신규 주소만 | Phase 8: 지도 대상 회사의 대표 사업장, Phase 9: 전월세 건물. 좌표계 EPSG:5179 → pyproj로 EPSG:4326 변환 후 저장 |
| 법정동코드 전체자료 (행정표준코드관리시스템) | TXT | 연 1회 | `region`(시군구 코드 → 시도 · 시군구 이름). 검색 결과 지역 표시용 |
| 한국부동산원 전월세전환율 | 통계표 | 월 1회 | `conversion_rate`에 수동/반자동 적재 |
| 사람인 채용공고 검색 API | REST | 일 1회 | 1일 500회 한도. 본문 저장 금지, 출처 표시 필수 |

### 반드시 지킬 이용 조건

- 카카오·네이버·브이월드 지오코딩 결과는 DB에 저장하지 않는다. 저장하는 좌표는 주소정보누리집에서만 얻는다.
- 네이버 지도는 화면 표시용으로만 쓰고, 배경지도를 다른 라이브러리로 가져가지 않는다.

### 네이버 지도(NCP Maps) 사용 범위

| 상품 | 사용 | 용도 | 방식 |
|---|---|---|---|
| Dynamic Map | 필수 | 지도 비교 화면의 지도 · 회사 핀 · 팝업 | Web JS |
| Geocoding | 선택 | 지도 검색창: 입력한 주소 · 역 이름 위치로 지도 이동. 결과는 저장하지 않음 | Web JS (지오코더 서브모듈) |
| Map Style Editor | 선택 | 지도 색을 단순화해 핀을 강조 | Web JS |
| Reverse Geocoding, Static Map, Directions | 사용 안 함 | — | — |

- Web JS만 사용하므로 브라우저에는 Client ID만 노출된다. NCP 콘솔 Application에 사용 도메인(`localhost:3000`, Vercel 배포 주소)을 등록해 보호한다.
- Client Secret이 필요한 REST API는 사용하지 않는다. 필요해지면 FastAPI를 거쳐 호출하고 Secret은 서버 환경 변수에만 둔다.
- 무료 이용량은 대표 계정 기준이므로 대표 1인의 NCP 계정에서 Application을 만들고 팀원 개발 도메인을 함께 등록한다.
- 사람인 공고는 공고 번호, 회사 매칭, 마감일, 연봉 코드, 근무지 코드, 원문 링크만 저장한다. 화면에 "채용정보 제공: 사람인"을 표시한다.

### 공통 수집기 요구사항

- httpx 타임아웃 30초, 지수 백오프 재시도 3회.
- 소스별 일일 호출 수를 `api_call_log(source, call_date, count)`에 기록하고 한도 도달 시 중단한다. 다음 실행에서 이어서 수집한다.
- 모든 실행은 `ingestion_log`에 시작·종료·상태·행 수·체크섬을 남긴다. 같은 체크섬이 `success`면 건너뛴다.

---

## 5. 데이터베이스

### 5.1 테이블 목록

| 계층 | 테이블 |
|---|---|
| 운영 | `ingestion_log`, `api_call_log` |
| 기준 | `nps_rate`, `conversion_rate`, `industry`(업종 코드 · 이름, 국민연금 파일에서 추출), `region`(시군구 코드 · 이름) |
| raw | `raw_nps_workplace`, `raw_rent_contract`, `raw_saramin_job` |
| core (회사) | `company`, `workplace`, `workplace_monthly`, `dart_corp`, `company_dart_link`, `dart_financial` |
| core (주거) | `geocode_cache`, `station`, `building`, `rent_contract`, `company_station` |
| core (채용) | `saramin_company_link`, `job_posting` |
| mart | `mart_company_monthly`, `mart_company_summary`, `mart_station_rent`, `mart_company_jobs` |

### 5.2 핵심 DDL

```sql
CREATE TABLE nps_rate (
  valid_from_ym INT PRIMARY KEY,
  valid_to_ym   INT NOT NULL,
  rate          DECIMAL(5,4) NOT NULL,
  income_cap    INT NOT NULL
);
-- 초기값: (202407,202506,0.0900,6170000), (202507,202512,0.0900,6370000),
--         (202601,202606,0.0950,6370000), (202607,202706,0.0950,6590000)
-- 적재 전 공단 공지로 값 재확인

CREATE TABLE company (
  company_id   INT AUTO_INCREMENT PRIMARY KEY,
  biz_no6      CHAR(6) NOT NULL,
  name_norm    VARCHAR(200) NOT NULL,
  display_name VARCHAR(200) NOT NULL,
  UNIQUE KEY uk_company (biz_no6, name_norm),
  KEY ix_name_prefix (name_norm)
);

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
);

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
);

CREATE TABLE dart_corp (
  corp_code      CHAR(8) PRIMARY KEY,
  corp_name      VARCHAR(200) NOT NULL,
  corp_name_norm VARCHAR(200) NOT NULL,
  stock_code     CHAR(6),
  bizr_no        VARCHAR(10),
  corp_cls       CHAR(1),
  bizr6          CHAR(6) AS (LEFT(bizr_no, 6)) PERSISTENT,
  KEY ix_bizr6 (bizr6)
);

CREATE TABLE company_dart_link (
  company_id  INT PRIMARY KEY,
  corp_code   CHAR(8) NOT NULL,
  match_type  ENUM('exact','fuzzy','manual') NOT NULL,
  match_score DECIMAL(4,3)
);

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
);

CREATE TABLE mart_company_summary (
  company_id      INT PRIMARY KEY,
  industry_code   CHAR(6),
  region_code     CHAR(5),          -- 대표 사업장 법정동코드 앞 5자리(시군구)
  rep_addr_key    VARCHAR(200),     -- 대표 사업장 주소 키 → geocode_cache
  workplace_count SMALLINT NOT NULL,
  latest_ym       INT NOT NULL,
  members         INT NOT NULL,
  growth_12m      DECIMAL(7,4),     -- 12개월 전 자료가 없으면 NULL
  quit_rate_12m   DECIMAL(6,4),
  avg_salary_est  INT,
  pct_growth      TINYINT,          -- 원값이 NULL이면 NULL
  pct_stability   TINYINT,
  pct_salary      TINYINT,
  small_sample    BOOLEAN NOT NULL DEFAULT FALSE,
  short_history   BOOLEAN NOT NULL DEFAULT FALSE,
  KEY ix_ind_salary (industry_code, avg_salary_est),
  KEY ix_ind_region (industry_code, region_code)
);
-- 최신 월에 없는 회사(폐업 · 탈퇴 가능)는 summary에 행이 없다.
-- 상세 API는 company는 있고 summary가 없으면 mart_company_monthly의 MAX(snapshot_ym)을 last_seen_ym으로 내려준다.

CREATE TABLE region (
  region_code  CHAR(5) PRIMARY KEY,
  sido_name    VARCHAR(20) NOT NULL,
  sigungu_name VARCHAR(30) NOT NULL
);

CREATE TABLE geocode_cache (
  addr_key     VARCHAR(200) PRIMARY KEY,
  status       ENUM('ok','fail') NOT NULL,
  lon          DECIMAL(10,7),
  lat          DECIMAL(10,7),
  accuracy     ENUM('building','road','dong'),   -- 건물번호까지 맞으면 building
  provider     VARCHAR(20) NOT NULL,             -- 'juso'만 허용 (5.3, 4장 이용 조건)
  fail_reason  VARCHAR(100),
  requested_at DATETIME NOT NULL
);

CREATE TABLE station (
  station_id   INT AUTO_INCREMENT PRIMARY KEY,
  station_code VARCHAR(10) NOT NULL,
  station_name VARCHAR(50) NOT NULL,
  line_name    VARCHAR(50) NOT NULL,
  pt           POINT NOT NULL,
  UNIQUE KEY uk_station (station_code, line_name),
  SPATIAL INDEX sx_station (pt)
);

CREATE TABLE building (
  building_id INT AUTO_INCREMENT PRIMARY KEY,
  addr_key    VARCHAR(200) NOT NULL,
  house_type  ENUM('연립다세대','오피스텔') NOT NULL,
  build_year  SMALLINT,
  pt          POINT NOT NULL,
  UNIQUE KEY uk_building (addr_key, house_type),
  SPATIAL INDEX sx_building (pt)
);

-- 월 단위 파티션. 매월 새 파티션 추가, 24개월 지난 파티션 DROP
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
  KEY ix_bld_ym (building_id, contract_ym)
)
PARTITION BY RANGE (contract_ym) (
  PARTITION p202409 VALUES LESS THAN (202410),
  -- ... 월별 생성 스크립트로 채움
  PARTITION pmax VALUES LESS THAN MAXVALUE
);

CREATE TABLE conversion_rate (
  ym        INT PRIMARY KEY,
  rate_year DECIMAL(5,4) NOT NULL
);

CREATE TABLE company_station (
  company_id INT NOT NULL,
  station_id INT NOT NULL,
  distance_m INT NOT NULL,
  rnk        TINYINT NOT NULL,
  PRIMARY KEY (company_id, station_id)
);

CREATE TABLE mart_station_rent (
  station_id           INT NOT NULL,
  period_end_ym        INT NOT NULL,
  window_months        TINYINT NOT NULL,
  n_monthly            INT NOT NULL,
  n_jeonse             INT NOT NULL,
  monthly_p25          INT, monthly_median INT, monthly_p75 INT,   -- 환산 월세(원)
  deposit_median_man   INT,                                         -- 월세 계약 보증금 중위
  rent_median_man      INT,                                         -- 월세 계약 월세 중위
  jeonse_p25_man       INT, jeonse_median_man INT, jeonse_p75_man INT,
  PRIMARY KEY (station_id, period_end_ym, window_months)
);

CREATE TABLE saramin_company_link (
  saramin_company_key VARCHAR(200) PRIMARY KEY,  -- 기업정보 링크 또는 정규화 기업명
  company_id          INT NULL,
  match_type          ENUM('exact','fuzzy','manual','none') NOT NULL,
  match_score         DECIMAL(4,3)
);

CREATE TABLE job_posting (
  job_id        VARCHAR(20) PRIMARY KEY,
  company_id    INT NULL,
  title         VARCHAR(300) NOT NULL,
  salary_code   VARCHAR(10),
  location_code VARCHAR(50),
  expires_at    DATETIME,
  url           VARCHAR(500) NOT NULL,
  fetched_at    DATETIME NOT NULL,
  KEY ix_company_exp (company_id, expires_at)
);
```

### 5.3 MariaDB 주의사항

아래 항목은 MariaDB 10.11.14에서 직접 실행해 확인했다. 11.4에서도 같을 것으로 보지만, Phase 3의 SQL 회귀 테스트에 각 항목을 테스트로 넣어 11.4에서 다시 확인한다.


- 생성 컬럼의 원본이 `CHAR`면 오류 1901로 거부된다. 원본은 `VARCHAR`로 둔다.
- 함수 인덱스 문법(`KEY ((LEFT(col,6)))`)은 쓰지 않는다. 생성 컬럼 + 일반 인덱스로 대체한다.
- 컬럼 정의에 `SRID 4326` 속성을 쓰지 않는다(문법 오류). `POINT(경도, 위도)` 순서를 규칙으로 고정한다.
- 공간 인덱스 컬럼은 `NOT NULL`이어야 한다. 좌표가 없는 행은 `building`에 넣지 않는다.
- 파티션 키는 모든 PK·UNIQUE 키에 포함되어야 한다.
- `PERCENTILE_CONT`는 윈도 함수로만 동작한다. `OVER (PARTITION BY ...)` + `DISTINCT`로 쓴다.
- `ST_Distance_Sphere` 단독 조건은 전체 스캔이다. 반드시 `MBRContains(ST_Buffer(pt, deg), other)`를 앞에 붙인다. 500m는 0.006°, 1km는 0.012°.

---

## 6. 계산 규칙

| 지표 | 정의 |
|---|---|
| 회사 | `biz_no6` + `name_norm`이 같은 사업장 묶음 |
| 대표 사업장 | 최신 월 가입자 수가 가장 많은 사업장 |
| 대표 업종 | 대표 사업장의 업종 |
| 추정 연봉 | `billed_amount ÷ members ÷ rate(snapshot_ym) × 12` |
| 입사율·퇴사율 | `new ÷ 전월 members`, `lost ÷ 전월 members`. 직전 달이 없으면 NULL |
| 12개월 성장률 | `members(최신) ÷ members(12개월 전) − 1` |
| 연간 퇴사율 | 최근 12개월 `lost` 합 ÷ 같은 기간 평균 `members` |
| 백분위 | 대표 업종 내 `PERCENT_RANK` × 100. 안정 = 100 − 퇴사율 백분위 |
| 표본 부족 | 회사: members < 10. 역: 계약 < 20건 |
| 원룸 | 전용 33㎡ 이하 연립다세대·오피스텔 |
| 월세/전세 | `monthly_man > 0`이면 월세, 0이면 전세 |
| 환산 월세(원) | `(monthly_man + deposit_man × rate_year ÷ 12) × 10000` |
| 역세권 | 역 좌표에서 500m 이내 |
| 회사 근처 역 | 대표 사업장 좌표에서 1km 이내, 가까운 순 최대 3곳 |
| 주거비 부담률 | 역 환산 월세(p25/중위/p75) ÷ (추정 연봉 ÷ 12) |
| 기간 N개월 | `contract_ym > PERIOD_ADD(최신월, -N)` (`>=` 아님) |
| 성장형 채용 가능성 | 진행 중 공고 있음 AND `pct_growth ≥ 50` AND 퇴사율 ≤ 업종 중위 |
| 결원 충원형 가능성 | 진행 중 공고 있음 AND 퇴사율 백분위 상위 20% AND `growth_12m ≤ 0` |

상호 정규화(`pipeline/common/normalize.py`):

```python
import re
CORP_TOKENS = re.compile(r"\(주\)|㈜|주식회사|\(유\)|유한회사|\(사\)|사단법인")
NON_WORD = re.compile(r"[^0-9A-Za-z가-힣]")

def normalize_name(name: str) -> str:
    return NON_WORD.sub("", CORP_TOKENS.sub("", name)).upper()
```

매칭 순서: ① 정규화 이름 완전 일치(+사업자번호 6자리 일치 가능 시) → `exact` ② rapidfuzz `token_sort_ratio` ≥ 85 → `fuzzy` ③ 그 외 연결하지 않음.

---

## 7. 핵심 SQL (10.11에서 검증, 11.4 회귀 테스트로 재확인. `sql/`에 파일로 저장)

### q1_company_monthly.sql

```sql
INSERT INTO mart_company_monthly
  (company_id, snapshot_ym, members, new_members, lost_members, hire_rate, quit_rate, avg_salary_est)
SELECT company_id, snapshot_ym, members, new_m, lost_m, hire_rate, quit_rate, avg_salary_est
FROM (
  WITH agg AS (
    SELECT w.company_id, m.snapshot_ym,
           SUM(m.members) AS members, SUM(m.billed_amount) AS billed,
           SUM(m.new_members) AS new_m, SUM(m.lost_members) AS lost_m
    FROM workplace_monthly m
    JOIN workplace w ON w.workplace_id = m.workplace_id
    GROUP BY w.company_id, m.snapshot_ym
  ),
  with_prev AS (
    SELECT a.*,
           LAG(members)     OVER (PARTITION BY company_id ORDER BY snapshot_ym) AS prev_members,
           LAG(snapshot_ym) OVER (PARTITION BY company_id ORDER BY snapshot_ym) AS prev_ym
    FROM agg a
  )
  SELECT p.company_id, p.snapshot_ym, p.members, p.new_m, p.lost_m,
         CASE WHEN p.prev_ym = PERIOD_ADD(p.snapshot_ym, -1) THEN p.new_m  / NULLIF(p.prev_members, 0) END AS hire_rate,
         CASE WHEN p.prev_ym = PERIOD_ADD(p.snapshot_ym, -1) THEN p.lost_m / NULLIF(p.prev_members, 0) END AS quit_rate,
         ROUND(p.billed / NULLIF(p.members, 0) / r.rate * 12) AS avg_salary_est
  FROM with_prev p
  JOIN nps_rate r ON p.snapshot_ym BETWEEN r.valid_from_ym AND r.valid_to_ym
) src
ON DUPLICATE KEY UPDATE
  members = VALUES(members), new_members = VALUES(new_members), lost_members = VALUES(lost_members),
  hire_rate = VALUES(hire_rate), quit_rate = VALUES(quit_rate), avg_salary_est = VALUES(avg_salary_est);
```

### q2_company_summary.sql

```sql
REPLACE INTO mart_company_summary
  (company_id, industry_code, region_code, rep_addr_key, workplace_count, latest_ym, members,
   growth_12m, quit_rate_12m, avg_salary_est, pct_growth, pct_stability, pct_salary,
   small_sample, short_history)
SELECT company_id, industry_code, region_code, rep_addr_key, workplace_count, latest_ym, members,
       growth_12m, quit_rate_12m, avg_salary_est,
       -- NULL 지표는 별도 파티션으로 분리해 백분위 0을 받지 않게 한다
       CASE WHEN growth_12m IS NOT NULL THEN ROUND(100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, growth_12m IS NULL ORDER BY growth_12m)) END,
       CASE WHEN quit_rate_12m IS NOT NULL THEN ROUND(100 - 100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, quit_rate_12m IS NULL ORDER BY quit_rate_12m)) END,
       CASE WHEN avg_salary_est IS NOT NULL THEN ROUND(100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, avg_salary_est IS NULL ORDER BY avg_salary_est)) END,
       members < 10,
       members_12m_ago IS NULL
FROM (
  WITH latest AS (SELECT MAX(snapshot_ym) AS ym FROM mart_company_monthly),
  win AS (
    SELECT m.company_id, l.ym AS latest_ym,
           MAX(CASE WHEN m.snapshot_ym = l.ym THEN m.members END) AS members,
           MAX(CASE WHEN m.snapshot_ym = PERIOD_ADD(l.ym, -12) THEN m.members END) AS members_12m_ago,
           SUM(CASE WHEN m.snapshot_ym > PERIOD_ADD(l.ym, -12) THEN m.lost_members END) AS lost_12m,
           AVG(CASE WHEN m.snapshot_ym > PERIOD_ADD(l.ym, -12) THEN m.members END) AS avg_members_12m,
           MAX(CASE WHEN m.snapshot_ym = l.ym THEN m.avg_salary_est END) AS avg_salary_est
    FROM mart_company_monthly m CROSS JOIN latest l
    WHERE m.snapshot_ym >= PERIOD_ADD(l.ym, -12)
    GROUP BY m.company_id, l.ym
  ),
  cur_wp AS (   -- 최신 월에 존재하는 사업장
    SELECT w.company_id, w.industry_code, LEFT(w.legal_dong_code, 5) AS region_code, w.addr_key, m.members,
           ROW_NUMBER() OVER (PARTITION BY w.company_id ORDER BY m.members DESC, w.workplace_id) AS rn,
           COUNT(*)     OVER (PARTITION BY w.company_id) AS workplace_count
    FROM workplace w
    JOIN workplace_monthly m ON m.workplace_id = w.workplace_id
    JOIN latest l ON m.snapshot_ym = l.ym
  )
  SELECT w.company_id, r.industry_code, r.region_code, r.addr_key AS rep_addr_key, r.workplace_count,
         w.latest_ym, w.members, w.members_12m_ago,
         w.members / NULLIF(w.members_12m_ago, 0) - 1 AS growth_12m,
         w.lost_12m / NULLIF(w.avg_members_12m, 0)    AS quit_rate_12m,
         w.avg_salary_est
  FROM win w JOIN cur_wp r ON r.company_id = w.company_id AND r.rn = 1
  WHERE w.members IS NOT NULL      -- 최신 월에 없는 회사(최근 자료 없음)는 summary에 넣지 않는다
) s;
```

- NULL 원값은 `PARTITION BY industry_code, 지표 IS NULL`로 분리해 백분위 0을 받지 않는다(이전 버전의 알려진 문제 수정).
- 대표 사업장의 업종 · 지역 · 주소 키와 최신 월 사업장 수를 함께 저장한다.
- MariaDB 10.11.14에서 실행 확인: 짧은 이력 회사는 `growth_12m`·`pct_growth` NULL, `short_history = 1`. 최신 월에 없는 회사는 행 없음.

### q_map_companies.sql (지도 핀)

```sql
SELECT s.company_id, c.display_name, s.members, s.growth_12m, s.quit_rate_12m, s.avg_salary_est,
       g.lon, g.lat, g.accuracy
FROM mart_company_summary s
JOIN company c        ON c.company_id = s.company_id
JOIN geocode_cache g  ON g.addr_key = s.rep_addr_key AND g.status = 'ok'
WHERE s.industry_code = '620100'
  AND s.region_code LIKE '11%'
ORDER BY s.members DESC
LIMIT 201;
```

- 필터는 업종 · 지역(시도 접두어 또는 시군구)을 바인딩 파라미터로 받는다. 201번째 행이 있으면 응답에 `truncated: true`를 넣고 200개만 내려준다.

### q_compare.sql (비교 지수, 12개월 전 = 100)

```sql
WITH latest AS (SELECT MAX(snapshot_ym) AS ym FROM mart_company_monthly),
base AS (
  SELECT m.company_id, m.members AS base_members
  FROM mart_company_monthly m JOIN latest l ON m.snapshot_ym = PERIOD_ADD(l.ym, -12)
  WHERE m.company_id IN (1, 2, 3)
)
SELECT m.company_id, m.snapshot_ym,
       ROUND(100 * m.members / NULLIF(b.base_members, 0), 1) AS idx
FROM mart_company_monthly m
JOIN latest l ON m.snapshot_ym >= PERIOD_ADD(l.ym, -12)
LEFT JOIN base b ON b.company_id = m.company_id
WHERE m.company_id IN (1, 2, 3)
ORDER BY m.company_id, m.snapshot_ym;
```

- 12개월 전 자료가 없는 회사는 `idx`가 NULL이며, 응답에 `short_history` flag를 붙인다.

### q5_station_rent.sql (월세 부분, 전세는 같은 구조로 `monthly_man = 0` 조건)

```sql
SET @end_ym = (SELECT MAX(contract_ym) FROM rent_contract);
SET @n = 12;

SELECT DISTINCT s.station_id,
       COUNT(*) OVER (PARTITION BY s.station_id) AS n_monthly,
       ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY c.conv_rent) OVER (PARTITION BY s.station_id)) AS p25,
       ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY c.conv_rent) OVER (PARTITION BY s.station_id)) AS p50,
       ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY c.conv_rent) OVER (PARTITION BY s.station_id)) AS p75
FROM station s
JOIN building b
  ON MBRContains(ST_Buffer(s.pt, 0.006), b.pt)
 AND ST_Distance_Sphere(s.pt, b.pt) <= 500
JOIN (
  SELECT r.building_id,
         (r.monthly_man + r.deposit_man * cr.rate_year / 12) * 10000 AS conv_rent
  FROM rent_contract r
  JOIN conversion_rate cr ON cr.ym = r.contract_ym
  WHERE r.contract_ym > PERIOD_ADD(@end_ym, -@n)
    AND r.area_m2 <= 33
    AND r.monthly_man > 0
) c ON c.building_id = b.building_id;
```

### q6_company_station.sql

```sql
DELETE FROM company_station;
INSERT INTO company_station (company_id, station_id, distance_m, rnk)
SELECT company_id, station_id, distance_m, rnk
FROM (
  WITH latest AS (SELECT MAX(snapshot_ym) AS ym FROM workplace_monthly),
  rep AS (
    SELECT company_id, addr_key FROM (
      SELECT w.company_id, w.addr_key,
             ROW_NUMBER() OVER (PARTITION BY w.company_id ORDER BY m.members DESC) AS rn
      FROM workplace w
      JOIN workplace_monthly m ON m.workplace_id = w.workplace_id
      JOIN latest l ON m.snapshot_ym = l.ym
    ) t WHERE rn = 1
  )
  SELECT r.company_id, s.station_id,
         ROUND(ST_Distance_Sphere(s.pt, POINT(g.lon, g.lat))) AS distance_m,
         ROW_NUMBER() OVER (PARTITION BY r.company_id
                            ORDER BY ST_Distance_Sphere(s.pt, POINT(g.lon, g.lat))) AS rnk
  FROM rep r
  JOIN geocode_cache g ON g.addr_key = r.addr_key AND g.status = 'ok'
  JOIN station s
    ON MBRContains(ST_Buffer(POINT(g.lon, g.lat), 0.012), s.pt)
   AND ST_Distance_Sphere(s.pt, POINT(g.lon, g.lat)) <= 1000
) t
WHERE rnk <= 3;
```

대표 사업장 하나만 쓴다. 모든 사업장을 기준으로 순위를 매기면 같은 역이 중복되어 1순위가 사라진다(검증된 버그).

### 파티션 순환 (월 1회)

```sql
ALTER TABLE rent_contract REORGANIZE PARTITION pmax INTO (
  PARTITION p{YYYYMM} VALUES LESS THAN ({다음달YYYYMM}),
  PARTITION pmax VALUES LESS THAN MAXVALUE
);
ALTER TABLE rent_contract DROP PARTITION p{24개월 전 YYYYMM};
```

---

## 8. API 계약

공통: JSON, 오류는 `{"detail": "..."}`. 없는 리소스 404, 파라미터 오류 422. 모든 응답에 `as_of`(데이터 기준월)를 둔다. 응답 헤더 `ETag`(마지막 적재 월), `Cache-Control: public, max-age=3600`은 P2(선택)로, 기간 내에는 넣지 않아도 된다.

| 메서드·경로 | 파라미터 | 응답 핵심 필드 |
|---|---|---|
| `GET /companies` | `q`(접두어), `biz_no6`, `industry`, `hiring`(bool, P2), `sort`(name\|growth\|deadline), `limit`(≤50), `cursor` | `items[]{company_id, name, industry{code,name}, region{sido,sigungu}, members, growth_12m, quit_rate_12m, avg_salary_est, open_jobs}`, `next_cursor`. 결과 0건이면 `items: []` |
| `GET /companies/{id}` | — | `name, industry{code,name}, region{sido,sigungu}, form_type, workplace_count, as_of, members, growth_12m, quit_rate_12m, avg_salary_est, percentiles{growth,stability,salary}, flags[], dart{corp_code,match_type}`. 최근 자료 없음이면 `status:"stale", last_seen_ym`만 내려준다. 없는 ID는 404 |
| `GET /companies/{id}/trend` | `from_ym`, `to_ym` | `points[]{ym, members, new, lost, hire_rate, quit_rate, avg_salary_est}` |
| `GET /companies/{id}/financials` | `years`(≤5) | `rows[]{year, revenue, operating_income, net_income, debt_ratio}` |
| `GET /companies/{id}/jobs` | — | `jobs[]{title, expires_at, salary_range, url}, signal(growth\|backfill\|none), salary_compare{posted, company_est, industry_median}, source:"사람인"` |
| `GET /companies/{id}/housing` | `months`(6\|12\|24) | `monthly_pay_est, stations[]{name, lines[], distance_m, monthly_median, jeonse_median_man, n, burden{low,mid,high}, flags[]}` |
| `GET /stations` | `q`, `line`, `sort=monthly_median` | `items[]{station_id, name, lines[], monthly_median, n}` |
| `GET /stations/{id}/rent` | `months`(1~24, 기본 12), `contract`(all\|monthly\|jeonse) | 분포, 전세 비중, `trend[]{ym, median}` |
| `GET /industries` | `q`(이름 일부) | `items[]{code, name, n_companies}` |
| `GET /industries/{code}/distribution` | `metric`(salary\|quit\|growth) | `p25, p50, p75, n` |
| `GET /compare` | `ids`(최대 3) | 회사별 `index_series[]`(12개월 전 = 100) + 요약 + `flags[]` |
| `GET /map/companies` | `industry`, `region`(시도 2자리 또는 시군구 5자리), `metric`(growth\|quit\|salary) | `items[]{company_id, name, lon, lat, accuracy, value}`(최대 200), `truncated` |
| `GET /meta/methodology` | — | 계산식, 한계, 데이터 기준월, 출처 목록 |
| `GET /health` | — | `db:"ok"`, `latest_nps_ym`. 확장 시 `latest_rent_ym`, (P2) `match_rate`, `geocode_success_rate` |

`flags` 값: `salary_is_lower_bound`, `small_sample`, `short_history`(12개월 미만 이력), `stale`(최신 월에 없음), `approx_location`(좌표 정확도가 building이 아님), `name_matched`, `period_extended_to_24m`.

`months`는 Pydantic `Query(12, ge=1, le=24)`로 검증한다.

---

## 9. 화면

| 화면 | 경로 | 구성 |
|---|---|---|
| 검색 | `/` | 검색창(회사명·사업자번호 6자리), 업종 선택(이름 검색), "채용 중" 필터(P2), 결과 표(회사명 + 시·구 + 업종명, 가입자, 12개월 증감, 퇴사율, 추정 연봉, 공고 수), "비교에 담기", 결과 없음 안내(공개 기준 미만 가능성, 사업자번호 검색 안내) |
| 회사 상세 | `/companies/[id]` | 기본 정보(지역, 업종, 사업장 수, 법인/개인), 체력 카드 3개(백분위 막대), 가입자 추이 그래프, 월별 입퇴사 표, 추정 연봉 카드(하한 경고), 재무 표, "사람인에서 채용공고 보기" 버튼, "비교에 담기". 짧은 이력 · 표본 부족 안내. 최근 자료 없음이면 마지막 등장 월과 안내만 표시. 확장: 채용 현황 카드(사람인 출처), 역세권 주거비 카드 |
| 회사 없음 | `/companies/[id]` (404) | 안내 문구, 검색으로 돌아가기 |
| 지도 비교 | `/map` | 업종 · 지역 필터(최대 200개, 초과 시 범위 좁히기 안내), 지표 토글(증감/퇴사율/연봉), 회사 핀(값 표시, 대략 위치는 다른 모양), 핀 팝업(미니 그래프, 지표 4개, 비교 추가), 비교 패널(지수 그래프 최대 3개, 회사별 행) |
| 역 시세 (확장) | `/stations/[id]` | 기간 버튼(6/12/24), 월세·전세 분포, 전세 비중, 24개월 추이 |
| 계산 방법 | `/methodology` | 계산식, 한계, 출처 |

공통: 모든 추정치 옆에 "추정" 표기와 툴팁. 모든 화면 하단에 데이터 기준월 · 출처 · 면책 문구. 데이터 영역마다 로딩 · 오류(다시 시도) 상태. 휴대폰 폭에서 카드·표가 세로로 쌓이고 넓은 표는 가로 스크롤. 비교 대상은 최대 3개, 화면 상단에 담은 수 표시.

---

## 10. 진행 단계

### Phase 0. 프로젝트 시작 (0.5일)

1. 저장소 `worth-joining` 생성, `.gitignore`(Python, Node, `.env`), MIT `LICENSE`.
2. 2장 구조대로 디렉터리 생성.
3. `pyproject.toml`에 1장 의존성 추가. `ruff`, `pytest` 설정.
4. 설치된 MariaDB 11.4에 개발 DB와 테스트 DB를 만든다(3장 "로컬 DB 준비"). `docker-compose.yml`(`mariadb:11.4`)은 선택 사항으로 함께 둔다.
5. `app/core/config.py`에서 3장 환경 변수를 pydantic-settings로 로드. `.env.example` 작성.
6. GitHub Actions: push 시 `ruff check` + `pytest`. DB는 서비스 컨테이너로 띄운다.

```yaml
services:
  mariadb:
    image: mariadb:11.4
    env:
      MARIADB_ROOT_PASSWORD: test
      MARIADB_DATABASE: worth_joining_test
    ports: ["3306:3306"]
    options: >-
      --health-cmd="healthcheck.sh --connect --innodb_initialized"
      --health-interval=5s --health-timeout=5s --health-retries=10
```

7. `tests/conftest.py`: 세션 시작 시 테스트 DB의 테이블을 모두 지우고 `alembic upgrade head`, 테스트마다 트랜잭션을 열고 끝나면 롤백한다.

완료 조건: 로컬 MariaDB 11.4 접속(`/health` 수준) 확인, `pytest`가 빈 상태로 통과, CI가 서비스 컨테이너로 녹색.

### Phase 1. 데이터 프로파일링 (1~2일)

1. 국민연금 최근 13개월 파일을 내려받아 `data/raw/`(gitignore)에 둔다.
2. `notebooks/` 대신 `pipeline/nps/profile.py`로 다음을 출력한다: 인코딩, 실제 헤더명, 행 수, 컬럼별 결측률, 사업자번호 6자리 중복률, 가입자 0 이하 행 수, **주소 상세 수준(도로명 주소에 건물번호가 있는지)**.
   - 과거 월 파일을 몇 개월까지 구할 수 있는지 확인한다. 13개월이 안 되면 확보 범위를 기록하고 팀장에게 알린다.
   - 건물번호가 없으면 Phase 8의 회사 좌표는 건물 단위가 아니다. 대체 방법(예: 법정동 경계 공개 데이터의 중심점)을 정하고 `accuracy`를 `road` 또는 `dong`으로 저장한다.
3. 실제 헤더명과 6장의 필드 매핑을 `pipeline/nps/columns.py`에 고정한다.
4. 결과를 `docs/profiling.md`에 기록한다.

완료 조건: 확보한 파일 모두 파싱 성공, 헤더 매핑 확정, 주소 상세 수준과 과거 파일 확보 범위가 `docs/profiling.md`에 기록됨.

### Phase 2. 스키마와 국민연금 적재 (3~4일)

1. Alembic으로 5.2의 회사 관련 테이블 + `nps_rate`, `ingestion_log`, `api_call_log`, `raw_nps_workplace` 생성.
2. `nps_rate` 초기값 시드 마이그레이션. `region`은 법정동코드 전체자료에서, `industry`는 국민연금 파일의 업종 코드 · 이름에서 채운다.
3. 적재기 `python -m pipeline.nps.load --ym YYYYMM`:
   - CSV → UTF-8 변환 → `LOAD DATA LOCAL INFILE`로 `raw_nps_workplace`(해당 월 삭제 후 적재)
   - `normalize_name`으로 `name_norm` 계산
   - `INSERT ... SELECT ... ON DUPLICATE KEY UPDATE`로 `company` → `workplace` → `workplace_monthly`
4. 품질 검사(실패 시 `ingestion_log.status='failed'`, mart 갱신 중단):
   - 전월 대비 행 수 ±10% 초과
   - `members ≤ 0`
   - `billed_amount > members × income_cap × rate`
5. 13개월 백필.

완료 조건: 같은 월 2회 적재 시 행 수 동일(테스트), 13개월 적재 완료, 품질 검사 테스트 통과.

### Phase 3. mart SQL (3일)

1. `sql/q1_company_monthly.sql`, `sql/q2_company_summary.sql` 작성(7장).
2. q2는 7장의 수정본(NULL 백분위 분리, 대표 사업장 지역 · 주소 키, `short_history`)을 쓴다.
3. `python -m pipeline.refresh_mart`가 q1 → q2를 한 트랜잭션으로 실행.
4. SQL 회귀 테스트(로컬 테스트 DB, CI 11.4):
   - 빠진 달 다음 달의 `quit_rate`가 NULL
   - 2026년 1월 이후 행이 9.5%로 계산됨
   - 가입자 9명 회사는 `small_sample = 1`
   - 5개월 이력 회사는 `growth_12m`, `pct_growth`가 NULL이고 `short_history = 1`
   - 최신 월에 없는 회사는 `mart_company_summary`에 행이 없음
   - 5.3의 MariaDB 주의사항(CHAR 원본 생성 컬럼 거부, 파티션 키 포함 규칙 등)이 11.4에서도 성립
5. 주요 조회 쿼리의 `EXPLAIN` 결과를 `docs/explain.md`에 기록. 11.4는 비용 기반 옵티마이저라 10.11과 계획이 다를 수 있으므로 11.4 결과를 기준으로 삼는다.

완료 조건: 회귀 테스트 통과, `mart_company_summary`에 전 회사 행 존재.

### Phase 4. FastAPI MVP (4일)

1. 라우터: `/companies`, `/companies/{id}`, `/companies/{id}/trend`, `/industries`, `/industries/{code}/distribution`, `/meta/methodology`, `/health`.
2. 커서 페이지네이션(`company_id > :cursor`), `q`는 `name_norm LIKE 'q%'`.
3. `services/flags.py`에서 flags 생성(`short_history`, `stale` 포함). summary 행이 없는 회사는 `status:"stale"`로 응답한다.
4. (P2, 선택) ETag, Cache-Control 미들웨어.
5. API 테스트: 정상, 404, 422, 페이지네이션 경계, 결과 0건, 최근 자료 없음 회사, 짧은 이력 회사.

완료 조건: `/docs`에서 전 엔드포인트 동작, API 테스트 통과, 상세 조회 p95 300ms 이하(locust, 로컬).

### Phase 5. DART 연동 (3일)

1. `dart_corp`, `company_dart_link`, `dart_financial` 마이그레이션.
2. corpCode.xml 적재 → `corp_name_norm` 계산.
3. company.json 호출 우선순위: 상장사 → `name_norm`이 `company`에 존재하는 법인. 일 20,000건 한도 관리.
4. 정확 매칭 SQL(`d.bizr6 = c.biz_no6 AND d.corp_name_norm = c.name_norm`) → 실패분 rapidfuzz.
5. 사업보고서 주요계정 적재, `/companies/{id}/financials`.
6. 매칭률을 `docs/matching.md`에 기록한다(`/health` 노출은 P2).

완료 조건: 상장사 매칭률 측정·기록, financials API 테스트 통과.

### Phase 6. 프론트엔드 MVP (4일)

1. Next.js 프로젝트 `web/`, API 클라이언트(`NEXT_PUBLIC_API_BASE_URL`).
2. 검색(`/`), 회사 상세(`/companies/[id]`), 계산 방법(`/methodology`).
3. Recharts로 가입자 추이, 체력 카드 백분위 막대.
4. 추정치 표기·툴팁, 표본 부족 · 짧은 이력 · 최근 자료 없음 안내, 회사 없음(404) 화면, 검색 결과 없음 안내.
   - 결과 행과 상세 상단에 시·구, 업종명, 사업장 수를 표시해 동명 회사를 구분한다.
   - 모든 화면 하단에 데이터 기준월(`as_of`) · 출처 · 면책 문구. 데이터 영역마다 로딩 · 오류 상태.
5. "사람인에서 채용공고 보기" 버튼: `https://www.saramin.co.kr/zf_user/search?searchword={회사명}` 새 탭.
6. 모바일 폭 레이아웃 확인.

완료 조건: 검색 → 상세 → 사람인 이동 흐름이 동작, 빈 결과 · 404 · 오류 상태가 화면에 나옴, 모바일에서 가로 스크롤 없음(표 제외).

### Phase 7. MVP 배포 (1~2일)

1. Railway: `mariadb`(`mariadb:11.4` 이미지 + 볼륨. Railway가 서버에서 실행하므로 로컬 Docker 불필요), `api`(uvicorn), `pipeline`(월 1회 cron, `refresh_mart` 포함).
2. 로컬에서 백필한 DB를 `mariadb-dump` → Railway에 복원. 복원 명령과 순서를 `docs/runbook.md`에 적어 누구나 다시 만들 수 있게 한다.
3. Vercel에 `web` 배포, CORS 허용 도메인 설정.
4. README 실행 방법을 실제 명령으로 갱신.

완료 조건: 배포 URL에서 검색·상세 동작, `/health` 정상, 다음 달 cron 실행 확인 계획 기록.

**여기까지가 MVP(10/16 배포 목표). Phase 8은 10/19~10/20에 진행하고, Phase 9 · 10은 기간(10/21) 이후 과제다(12.2).**

### Phase 8. 지도 비교 (3일)

1. 지오코더(`pipeline/geocode/juso.py`)를 먼저 만든다: 검색 API(주소 → 도로명 키) → 좌표제공 API → pyproj(EPSG:5179 → 4326) → `geocode_cache`(`accuracy`, 실패 사유 포함). 일일 호출 수는 `api_call_log`로 관리. Phase 9도 이 모듈을 그대로 쓴다.
2. 지도 대상 회사 좌표 변환: `mart_company_summary.rep_addr_key` 중 아직 캐시에 없는 주소만 호출한다. 범위는 호출 한도를 보고 정한다(예: 서울, 가입자 많은 순). 건물번호가 없는 주소는 Phase 1에서 정한 대체 방법으로 저장하고 `accuracy`를 낮춘다. 성공률은 로그와 `docs/validation.md`에 기록한다.
3. 네이버 지도 Dynamic Map을 `react-naver-maps`로 연동. 스크립트는 `ncpKeyId`(Client ID)로 불러온다.
4. 지도 컴포넌트를 `web/components/map/NaverMap.tsx`로 분리하고, 화면은 `markers`, `onSelect`, `center` 같은 공통 props만 사용한다(SDK 교체 대비).
5. `/map/companies` API(7장 `q_map_companies.sql`): 업종 · 지역 필터, 최대 200개, `truncated`.
6. `/compare` API(7장 `q_compare.sql`): 12개월 전 = 100 지수 시계열.
7. `/map`: 필터, 지표 토글, 핀(대략 위치는 다른 모양), 팝업, 비교 패널(최대 3). 검색 결과 · 상세의 "비교에 담기"와 같은 상태를 쓴다.
8. (선택, P2) 지도 검색창: 네이버 Geocoding으로 입력 주소 · 역 위치로 이동, 주변 회사는 DB 좌표로 조회. 결과 저장 금지.
9. (선택, P2) 비교 상태 URL 공유(`/map?ids=1,2,3`), Map Style Editor 스타일.

완료 조건: 지도에서 필터 → 핀 클릭 → 팝업 → 비교 추가 → 비교 그래프 갱신. 200개 초과 시 안내. 배포 도메인에서 지도 인증 오류 없음. `geocode_cache`의 provider가 모두 `juso`.

### Phase 9. 역세권 전월세 (3주, 서울)

1주차:
1. 역 표준데이터 적재(서울만), `station`.
2. 전월세 적재기(`pipeline/rent/seoul.py`):
   - **초기 적재:** 서울 열린데이터광장의 연도별 CSV(2024 · 2025 · 2026)를 내려받아 `raw_rent_contract`에 적재한다. 인코딩을 확인하고 UTF-8로 변환한다.
   - **증분 수집:** 주 1회 Open API로 최근 3개월 계약을 다시 받는다(신고 지연 반영). 한 번에 최대 1,000건씩 페이지 단위로 호출한다.
   - **필터:** 건물용도가 연립다세대 · 오피스텔인 행만 core로 옮긴다. 아파트는 제외, 단독다가구는 프로파일링에서 지번 공개 여부를 확인한 뒤 결정한다.
   - **중복 방지:** 원본 필드로 만든 `row_hash`로 CSV와 API에서 겹친 계약을 한 번만 반영한다.
   - **기준월:** `contract_ym`은 접수연도가 아니라 계약일에서 만든다.
3. `rent_contract` 월 파티션 생성 스크립트와 순환 작업.
4. `addr_key` 생성: `자치구코드 + 법정동코드 + 지번구분 + 본번-부번`. 서울 데이터는 코드와 본번 · 부번이 분리되어 있어 문자열 정규화가 거의 필요 없다. 주소정보누리집 검색에는 `자치구명 + 법정동명 + 본번-부번` 문자열을 만들어 쓴다.
5. 프로파일링: 실제 컬럼명(한글 · 영문), 건물용도 값 종류, 본번 · 부번 결측률, 연도별 건수를 `docs/profiling.md`에 기록한다.

2주차:
6. Phase 8의 지오코더로 전월세 건물 주소(지번)를 변환한다. 수천 건이므로 여러 날에 나눠 실행한다.
7. `building` 채우기, `rent_contract.building_id` 연결.
8. `conversion_rate` 적재.
9. `q5_station_rent.sql`로 `mart_station_rent`(window 12, 24) 갱신.
10. `/stations`, `/stations/{id}/rent`(`months`는 요청 시 계산).

3주차:
11. `q6_company_station.sql`(회사 좌표는 Phase 8에서 확보한 것을 쓴다).
12. `/companies/{id}/housing`. 계약 < 20건이면 24개월로 자동 확장하고 `period_extended_to_24m` flag.
13. 회사 상세의 주거비 카드, `/stations/[id]` 화면.
14. 테스트: CSV · API 중복 계약 1건 반영, 499m 포함·501m 제외, 24개월 경계(`>`), 파티션 DROP 후 데이터 보존, 공간 인덱스 사용 EXPLAIN.

완료 조건: 서울 역별 시세 생성, 지오코딩 성공률 기록, 회사 상세에서 부담률 범위 표시.

### Phase 10. 채용 정보 연계 (2주, 사람인 API 승인 후)

1주차:
1. 사람인 API 승인·키 발급 확인. 승인 전에는 Phase 6의 바로가기만 유지.
2. 수집기: 대상 직무 코드 × 지역(서울·경기) 페이지 단위, 일 500회 한도 관리, 미수집 범위 다음 날 이어서.
3. `raw_saramin_job` → `saramin_company_link` 매칭(정규화 이름 + 근무지 지역 보조, rapidfuzz) → `job_posting`(본문 미저장).
4. 마감 후 30일 지난 공고 삭제 작업.

2주차:
5. `mart_company_jobs`: 회사별 진행 중 공고 수, 최근 마감일, 채용 신호(6장 기준).
6. 연봉 코드 → 금액 범위 매핑 테이블.
7. `/companies/{id}/jobs`, `/companies?hiring=true&sort=deadline`.
8. 회사 상세 채용 현황 카드("채용정보 제공: 사람인" 표기), 검색 "채용 중" 필터.

완료 조건: 일일 배치가 500회 안에서 종료, 매칭 결과에 `match_type` 기록, 화면에 출처 표시.

### Phase 11. 프로젝트 마무리 (3일)

1. 성능: 인덱스 전후 `EXPLAIN`과 응답 시간 비교를 `docs/performance.md`에 정리.
2. 검증: 업종이 다른 회사 5곳을 골라 추정 인원·연봉을 공개 자료와 대조해 `docs/validation.md`에 오차 기록.
3. 데이터 품질 지표 정리: 매칭률, 지오코딩 성공률, 표본 부족 비율.
4. README 최종화: 배포 URL, 화면 캡처, 아키텍처, 실제 실행 명령, 한계.
5. 발표 자료 소재 정리(`docs/presentation.md`): 문제 → 데이터 → 설계 → 핵심 SQL → 결과 1~2개 → 트러블슈팅(CHAR 생성 컬럼, 빈 달 처리, 공간 인덱스, 대표 사업장 중복) → 한계.
6. 모든 테스트 통과, CI 녹색, `main` 브랜치에 태그 `v1.0.0`.

완료 조건: 배포 서비스 정상, 문서 6종(profiling, explain, matching, performance, validation, runbook) 존재, `docs/02_requirements.md` 8.3 누락 재점검 완료, 태그 생성.

---

## 11. 하지 않는 것

- 회원가입, 로그인, 즐겨찾기
- 기업 리뷰 작성·수집
- 채용공고 본문 저장·재배포
- 직무별·개인별 연봉 산출
- 단독·다가구 전월세(프로파일링 결과에 따라 재검토), 서울 외 지역 전월세
- 실시간 부동산 매물 정보(민간 플랫폼 크롤링 · 매물 링크 포함). 시세는 신고된 실거래가로만 제공한다
- 유료 기능

---

## 12. 팀 운영 (4인)

### 12.1 트랙과 담당

| 트랙 | 담당 영역 | 주요 디렉터리 | 확장 단계 담당 |
|---|---|---|---|
| T1 데이터 파이프라인 | 국민연금 · DART · 전월세 · 역 수집, 정제, 매칭, 지오코딩, 스케줄러 | `pipeline/` | 역세권 전월세 수집 · 지오코딩 |
| T2 DB · SQL | 스키마 · Alembic 마이그레이션, 품질 검사, mart SQL, 공간 SQL, EXPLAIN · 성능 | `migrations/`, `sql/`, `tests/sql/` | 역세권 시세 · 회사-역 SQL |
| T3 백엔드 · 운영 | FastAPI, API 계약(OpenAPI), API 테스트, CI, 배포 | `app/`, `tests/api/`, `.github/` | 사람인 채용 연계 |
| T4 프론트엔드 | Next.js 화면, 차트, 지도, 반응형 · 접근성 | `web/` | 지도 비교, 확장 화면 |

- 4명이 트랙을 하나씩 맡고, 그중 1명이 팀장(일정 · 이슈 보드 · 회의 진행)을 겸한다.
- 트랙 구성과 배정은 첫 주 회의에서 확정한다.

### 12.2 일정 (2026-10-02 ~ 2026-10-21)

전체 기간: **2026-10-02(금) ~ 2026-10-21(수)**. 공휴일 10/3(개천절), 10/9(한글날)과 주말은 선택 작업일로 두고, 아래 계획은 평일 기준이다.

| 날짜 | T1 데이터 | T2 DB · SQL | T3 백엔드 · 운영 | T4 프론트엔드 | 마일스톤 |
|---|---|---|---|---|---|
| 10/02~10/07 | 데이터 소스 조사 | 설계 · 핵심 SQL 검증 | 요구사항 · SPEC | 화면 시안 | **기획 · 설계 완료** |
| 10/08 (목) | 국민연금 파일 확보, 프로파일링 | 프로파일링, ERD 확정 | 저장소 · CI · 로컬 DB(Phase 0), API 키 신청 | API 계약 확정(T3와), 화면 골격 | Phase 0~1, API 계약 |
| 10/12 (월) | 국민연금 적재기 | 스키마 · 마이그레이션 | API 골격 + 목 응답 | 검색 화면(목 데이터) | |
| 10/13 (화) | 13개월 백필 · 품질 검사 | q1 월별 지표 | 검색 API(실DB) | 상세 화면 골격 | Phase 2 완료 |
| 10/14 (수) | DART 고유번호 · 기업개황 | q2 요약 · 백분위, 회귀 테스트 | 상세 · 추이 API | 추이 차트 · 체력 카드 | Phase 3 완료 |
| 10/15 (목) | DART 매칭 · 재무 | 인덱스 · EXPLAIN | 재무 API, flags, API 테스트 | 상세 완성, 사람인 링크, 반응형 | Phase 4~6 완료 |
| 10/16 (금) | 월 배치(cron) 점검 | 배포 DB 복원 | Railway · Vercel 배포 | 통합 점검 | **MVP 배포 (Phase 7)** |
| 10/19 (월) | 지도용 회사 좌표 변환, 데이터 검증(회사 5곳 대조) | 성능 측정(locust) | `/compare` API | 지도 비교 화면(Phase 8) | |
| 10/20 (화) | 문서: profiling · matching · validation | 문서: explain · performance | 버그 수정, README | 지도 완성, 화면 캡처 | Phase 8 완료 |
| 10/21 (수) | 최종 점검 | 최종 점검 | 최종 배포, `v1.0.0` 태그 | 발표 자료 화면 | **종료 (Phase 11)** |

- **기간 안에 하는 것:** MVP(Phase 0~7), DART 연동, 회사 비교 · 지도(Phase 8), 검증 · 문서화(Phase 11).
- **기간 이후 과제:** 역세권 전월세(Phase 9), 사람인 채용 연계(Phase 10). 전월세 24개월 수집과 수천 건의 주소 → 좌표 변환은 API 호출 한도 때문에 여러 날이 필요하고, 사람인 API는 승인 시점을 알 수 없어 10/21 안에 끝낼 수 없다.
- **여유가 생기면:** 10/16 MVP 배포가 일정대로 끝나면, T1 · T2가 10/19~10/20에 서울 일부 구(예: 강남 · 서초 · 마포) 12개월로 축소한 역세권 시세를 시연용으로 만든다.
- **첫날 할 일:** 공공데이터포털 · OpenDART · 주소정보누리집 · 네이버 클라우드 플랫폼(Maps) 키를 10/08에 모두 신청한다. 사람인 API도 이날 신청하되 결과를 기다리지 않는다.
- T4는 10/08~10/13에 API 계약(OpenAPI)과 목 데이터로 화면을 먼저 만들어 백엔드를 기다리지 않는다.
- 트랙별 Task(ID, 선행 관계, 마감)와 MVP 핵심 경로는 `docs/02_requirements.md` 10장을 따른다. 이슈 하나 = Task 하나.

### 12.3 협업 규칙

**브랜치 · PR**

- `main`은 보호 브랜치. 직접 push 금지, PR 병합만 허용.
- 브랜치 이름: `<type>/<track>-<topic>` (예: `feat/t1-nps-loader`, `fix/t2-q2-null-pct`).
- PR 조건: 리뷰 승인 1명 이상, CI 통과, 관련 요구사항 ID 기재. Squash merge.
- PR은 작게 나눈다(변경 400줄 이하 권장). 하루 이상 열린 PR은 데일리 회의에서 공유한다.

**CODEOWNERS**

```
/pipeline/     @t1-owner
/migrations/   @t2-owner
/sql/          @t2-owner
/tests/sql/    @t2-owner
/app/          @t3-owner
/.github/      @t3-owner
/web/          @t4-owner
/SPEC.md       @team-lead
/docs/         @team-lead
```

**트랙 간 인터페이스**

- **API 계약 우선:** 1주차에 T3 · T4가 8장 API 계약을 FastAPI 스키마로 먼저 작성하고 병합한다. 프론트는 `/openapi.json`에서 타입을 생성하고, 백엔드 구현 전에는 목 응답으로 개발한다. 계약 변경은 별도 PR로 하고 T4 리뷰를 받는다.
- **DB 스키마:** 마이그레이션 파일은 T2가 검토하고 병합한다. 병합 전에 `alembic heads`가 1개인지 확인한다. 다른 트랙이 테이블이 필요하면 이슈로 요청한다.
- **mart 테이블:** T2가 컬럼을 정의하면 T3는 그 컬럼만 읽는다. 컬럼 변경 시 두 트랙이 함께 리뷰한다.
- **테스트 데이터:** `tests/fixtures/`에 국민연금 축소 CSV(가상 회사 20~40개, 20개월), DART · 전월세 · 사람인 응답 샘플을 둔다. 실제 키가 없어도 모든 테스트가 돌아가야 한다.

**API 키 관리**

| 키 | 발급 방식 | 보관 |
|---|---|---|
| 공공데이터포털, OpenDART, 서울 열린데이터광장, 주소정보누리집(개발용) | 팀원별 개발용 키 각자 발급 | 각자 `.env` |
| 주소정보누리집(운영용) | 대표 1인, 배포 서비스 URL 등록 | 배포 환경 변수 |
| 사람인 | 대표 1인 명의로 신청 (접근 키 공유 금지 조건) | 배포 환경 변수에만. 다른 팀원은 fixture로 개발 |
| 네이버 지도 (NCP Maps) | 대표 1인 NCP 계정에서 Application 생성, 팀원 로컬 도메인 · 배포 도메인 등록 | Client ID는 배포 · 각자 `.env`(공개되어도 도메인으로 보호). Secret은 사용하지 않음 |
| 배포(Railway, Vercel) | 팀 조직(Team) 계정으로 생성, 팀원 초대 | 각 플랫폼 |

- 대용량 백필(국민연금 13개월, 이후 전월세 24개월)은 담당자 1명이 실행해 호출 한도를 나눠 쓰지 않는다. 결과는 `mariadb-dump`로 팀에 공유한다.

**회의 · 추적**

- 데일리 15분: 어제 한 일, 오늘 할 일, 막힌 것.
- 주간 회의(주 1회): 마일스톤 점검, 다음 주 계획, 트랙 간 인터페이스 변경 논의.
- GitHub Projects 보드: 이슈 = Task 단위(`T1-04` 등), 본문에 요구사항 ID. 상태(To do / In progress / Review / Done).
- 결정 사항은 `docs/decisions/NNN-제목.md`에 짧게 기록한다(예: 네이버 지도 선택, MariaDB 11.4).

### 12.4 공동 완료 기준 (Definition of Done)

- 요구사항 인수 조건 충족
- 테스트 추가 · 통과, CI 녹색
- 리뷰 승인 1명 이상
- 관련 문서(README, SPEC, docs) 갱신
- 화면 변경은 PR에 스크린샷 첨부
