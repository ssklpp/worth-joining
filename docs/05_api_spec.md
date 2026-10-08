# 05. API 명세

| 항목 | 내용 |
|---|---|
| 대상 | T3(백엔드), T4(프론트엔드). 계약 변경은 별도 PR + T4 리뷰 |
| 기준 | SPEC 8장(API 계약). 이 문서의 "추가 제안"은 SPEC에 반영되기 전까지 확정이 아니다 |
| 화면 기준 | [03_ui_design.md](./03_ui_design.md) 5장(지도 메인 + 패널) |
| 상태 | 초안 · 2026-10-08 |

---

## 1. API 구조 결정

| 결정 | 내용 |
|---|---|
| 형식 | REST, JSON, 읽기 전용(`GET`만). 인증 없음(회원 기능 없음) |
| 데이터 원천 | `mart_*` 테이블만 읽는다. 작은 조회용 조인(`company`, `region`, `industry`, `geocode_cache`)만 허용. 요청 시점 집계 금지 |
| 계층 | `routers/`(파라미터 검증) → `repositories/`(SQL을 `text()`로 실행) → `services/`(flags · 문구 생성) → `schemas/`(Pydantic 응답) |
| 계약 | FastAPI가 만드는 `/openapi.json`이 단일 기준. 프론트는 여기서 타입을 생성 |
| 공통 필드 | 모든 응답에 `as_of`(데이터 기준월, `YYYYMM`). 추정치가 있으면 `flags[]` |
| 오류 | `{"detail": "..."}`. 없는 리소스 404, 파라미터 오류 422 |
| 페이지네이션 | 커서 방식(`cursor`, `next_cursor`), `limit` 최대 50 |
| 단위 | 비율은 소수(0.183 = 18.3%), 연봉은 원, 전월세는 만 원(`_man` 접미사), 거리는 m |
| 캐시 | (P2) `ETag` = 마지막 적재 월, `Cache-Control: public, max-age=3600` |
| CORS | 로컬 `localhost:3000`과 Vercel 배포 도메인만 허용 |

### flags 값

| 값 | 뜻 | 붙는 곳 |
|---|---|---|
| `salary_is_lower_bound` | 추정 연봉이 하한 | 연봉이 들어간 모든 응답 |
| `small_sample` | 가입자 10명 미만 / 역 계약 20건 미만 | 회사, 역 |
| `short_history` | 12개월 전 자료 없음 | 회사, 비교 |
| `stale` | 최신 월에 없음(폐업 · 탈퇴 가능) | 회사 상세 |
| `approx_location` | 좌표 정확도가 건물 단위가 아님 | 지도, 회사 상세 |
| `name_matched` | DART · 사람인을 이름 유사도로 연결 | 재무, 채용 |
| `period_extended_to_24m` | 계약이 적어 24개월로 넓힘 | 주거비 |

## 2. 엔드포인트

우선순위는 [02_requirements.md](./02_requirements.md)의 P0~P3을 따른다. "단계"는 SPEC 10장의 Phase.

| 메서드 · 경로 | 단계 | 파라미터 | 응답 핵심 |
|---|---|---|---|
| `GET /health` | 4 | — | `db`, `latest_nps_ym` |
| `GET /companies` | 4 | `q`, `biz_no6`, `industry`, `region`, `sort`, `limit`, `cursor`, (P2) `hiring` | `items[]{company_id, name, industry, region, members, growth_12m, quit_rate_12m, avg_salary_est, open_jobs}`, `next_cursor` |
| `GET /companies/{id}` | 4 | — | 기본 정보, 지표, `percentiles{growth,stability,salary}`, `flags[]`, `dart{corp_code,match_type}`. 최근 자료 없음이면 `status:"stale"`, `last_seen_ym` |
| `GET /companies/{id}/trend` | 4 | `from_ym`, `to_ym` | `points[]{ym, members, new, lost, hire_rate, quit_rate, avg_salary_est}` |
| `GET /industries` | 4 | `q` | `items[]{code, name, n_companies}` |
| `GET /industries/{code}/distribution` | 4 | `metric`(salary\|quit\|growth) | `p25, p50, p75, n` |
| `GET /meta/methodology` | 4 | — | 계산식, 한계, 기준월, 출처 |
| `GET /companies/{id}/financials` | 5 | `years`(≤5) | `rows[]{year, revenue, operating_income, net_income, debt_ratio}` |
| `GET /map/companies` | 8 | `industry`, `region`, `metric`, **`bbox`(추가 제안)** | `items[]{company_id, name, lon, lat, accuracy, value}`(최대 200), `truncated` |
| `GET /compare` | 8 | `ids`(최대 3) | 회사별 `index_series[]`(12개월 전 = 100), 요약, `flags[]` |
| `GET /stations` | 9 | `q`, `line`, `sort` | `items[]{station_id, name, lines[], monthly_median, n}` |
| `GET /stations/{id}/rent` | 9 | `months`, `contract` | 분포, 전세 비중, `trend[]{ym, median}` |
| `GET /companies/{id}/housing` | 9 | `months`(6\|12\|24) | `monthly_pay_est`, `stations[]{name, lines[], distance_m, monthly_median, jeonse_median_man, n, burden{low,mid,high}, flags[]}` |
| `GET /companies/{id}/jobs` | 10 | — | `jobs[]{title, expires_at, salary_range, url}`, `signal`, `salary_compare`, `source:"사람인"` |

### 응답 예시: `GET /companies/1`

```json
{
  "company_id": 1,
  "name": "예시소프트",
  "industry": {"code": "582200", "name": "응용 소프트웨어 개발 및 공급업"},
  "region": {"sido": "서울", "sigungu": "강남구"},
  "form_type": "corporation",
  "workplace_count": 3,
  "as_of": 202608,
  "members": 142,
  "growth_12m": 0.183,
  "quit_rate_12m": 0.091,
  "avg_salary_est": 41200000,
  "percentiles": {"growth": 81, "stability": 82, "salary": 62},
  "flags": ["salary_is_lower_bound"],
  "dart": {"corp_code": "00123456", "match_type": "exact"}
}
```

최근 자료 없음:

```json
{"company_id": 7, "name": "예시테크", "as_of": 202608, "status": "stale", "last_seen_ym": 202605, "flags": ["stale"]}
```

## 3. REST API 후보 (SPEC 밖)

화면 시안과 요구사항을 맞춰 보며 나온 후보다. 채택하려면 SPEC 8장 수정 PR이 필요하다.

| 후보 | 이유 | 판단 |
|---|---|---|
| `/map/companies`에 `bbox=min_lon,min_lat,max_lon,max_lat` | 지도 메인 화면은 "지금 지도 범위 안의 회사"로 목록을 갱신한다. 업종 · 지역만으로는 지도를 움직일 때 목록을 만들 수 없다 | **채택 권장** (Phase 8) |
| `/map/companies` 응답에 `members`, `growth_12m`, `quit_rate_12m`, `avg_salary_est`, `open_jobs` | 왼쪽 목록이 핀마다 지표 3개와 공고 수를 보여준다. 없으면 회사마다 상세를 따로 불러야 한다 | **채택 권장** |
| `/map/companies` 응답에 `ungeocoded_count` | 좌표가 없는 회사는 지도에 안 나온다. "지도 안의 회사 N곳"이 전체처럼 보이지 않게 알려야 한다 | **채택 권장** |
| `/compare` 응답에 `open_jobs`, `nearest_station_rent`, `burden_mid` | 비교 표에 채용 · 주거비 행이 있다 | 채택(확장 단계에서 필드 추가) |
| `/companies/{id}` 응답에 `rep_location{lon,lat,accuracy}` | 상세를 열 때 지도를 그 회사로 이동해야 한다 | 채택 |
| `GET /search/suggest?q=` (자동완성) | 검색창 편의 | 보류(P3). `/companies?q=&limit=5`로 대체 |
| `GET /regions` | 지역 필터 목록 | 보류. 시안 범위가 서울이라 프론트 상수로 충분 |

## 4. 외부 API

수집 파이프라인과 프론트가 호출하는 외부 API와 그 키다. 수집 주기와 파일로 받는 데이터(국민연금 월별 CSV, 역 표준데이터, 전월세 과거분, 전월세전환율)는 SPEC 4장을 따른다.

공통 호출 규칙: httpx 타임아웃 30초, 지수 백오프 재시도 3회. 소스별 일일 호출 수를 `api_call_log`에 기록하고, 한도에 닿으면 멈춘 뒤 다음 실행에서 이어간다. 키가 비어 있는 수집기는 실패하지 않고 경고 로그를 남긴 뒤 건너뛴다.

### 4.1 요약

| 외부 API | 환경 변수 | 발급처 | 발급 주체 · 보관 | 필요 시점 | 한도 |
|---|---|---|---|---|---|
| 국민연금 가입 사업장 Open API | `DATA_GO_KR_SERVICE_KEY` | data.go.kr (활용신청, 대부분 자동승인) | 팀원 각자 · `.env` | Phase 1~2 | 포털 기본 한도 |
| OpenDART | `OPENDART_API_KEY` | opendart.fss.or.kr (이메일 인증 후 즉시) | 팀원 각자 · `.env` | Phase 5 | 1일 20,000건 |
| 서울시 부동산 전월세가 정보 | `SEOUL_OPENDATA_KEY` | data.seoul.go.kr (즉시) | 팀원 각자 · `.env` | Phase 9 | 요청당 행 수 제한 |
| 주소정보누리집 검색 · 좌표제공 | `JUSO_SEARCH_KEY`, `JUSO_COORD_KEY` | business.juso.go.kr | 개발용: 팀원 각자 · `.env` / 운영용: 대표 1인 · Railway | Phase 8 (10/19), 9 | 승인키 종류별 |
| 사람인 채용공고 검색 | `SARAMIN_ACCESS_KEY` | oapi.saramin.co.kr (심사, 기간 불명) | **대표 1인만** · Railway | Phase 10 | 1일 500회 |
| 네이버 지도 Dynamic Map | `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | ncloud.com (결제수단 등록 필요) | 대표 1인 계정 · Vercel, 각자 `.env.local` | Phase 8 (10/19) | NCP 무료 이용량 |

### 4.2 키 관리 규칙

1. 키는 `.env`(백엔드)와 `.env.local`(프론트)에만 넣고 `.gitignore`에 포함한다. 저장소에는 값이 빈 `.env.example`만 커밋한다.
2. 키를 메신저 · 이슈 · PR 본문에 붙여넣지 않는다. 실수로 커밋하면 즉시 재발급하고 이력에서 제거한다.
3. CI와 테스트는 키 없이 `tests/fixtures/`로만 돌아간다.
4. 대용량 백필(국민연금 13개월, DART 전수, 전월세 24개월 좌표 변환)은 담당자 1명이 실행하고 결과를 `mariadb-dump`로 공유한다. 여러 명이 동시에 돌려 한도를 나눠 쓰지 않는다.

```dotenv
# backend (.env)
DATA_GO_KR_SERVICE_KEY=
OPENDART_API_KEY=
SEOUL_OPENDATA_KEY=
JUSO_SEARCH_KEY=
JUSO_COORD_KEY=
SARAMIN_ACCESS_KEY=

# frontend (.env.local)
NEXT_PUBLIC_NAVER_MAP_CLIENT_ID=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 4.3 공공데이터포털: 국민연금 가입 사업장 정보

- **용도:** 사업장 검색 · 상세 조회 보조, 최신월 확인. 월별 전체 자료는 키 없이 CSV 파일로 받는다.
- **주의:** 쿼리 파라미터로 넘길 때는 마이페이지의 **Decoding 키**를 쓴다(Encoding 키는 httpx에서 이중 인코딩된다). 승인 직후 1~2시간은 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`가 날 수 있다.

### 4.4 OpenDART

| API | 용도 | 주기 |
|---|---|---|
| `corpCode.xml` | 고유번호 전체(ZIP) → `dart_corp` | 월 1회 |
| `company.json` | 사업자번호 `bizr_no` 획득 → `bizr6` 생성 컬럼 | 필요 시. 호출 우선순위: 상장사 → `company`에 같은 `name_norm`이 있는 법인 |
| `fnlttSinglAcnt.json` | 단일회사 주요계정 → `dart_financial`. `reprt_code=11011`(사업보고서) 우선 | 분기 1회 |

`company.json` 전수 호출(수만 건)은 하루 한도를 넘으므로 며칠에 나눠 실행한다(4.2의 4번).

### 4.5 서울 열린데이터광장: 부동산 전월세가 정보(OA-21276)

- **용도:** 최근월 증분 수집. 주 1회 최근 3개월을 다시 받아 신고 지연을 반영한다. 과거 24개월 초기 적재는 CSV 파일로 하므로 키가 필요 없다.
- **호출:** 한 번에 받을 수 있는 행 수(시작~끝 인덱스)에 제한이 있어 최대 1,000건씩 페이지 단위로 반복한다. 원본은 매일 1회 갱신된다.

### 4.6 주소정보누리집: 도로명주소 검색 + 좌표제공

| | 도로명주소 검색 API | 좌표제공 API |
|---|---|---|
| 입력 | 국민연금 대표 사업장 주소(지도용), 전월세 지번 주소(자치구 + 법정동 + 본번-부번) | 검색 API가 돌려준 키 값 |
| 출력 | `admCd`, `rnMgtSn`, `udrtYn`, `buldMnnm`, `buldSlno` 등 | `entX`, `entY` (UTM-K, EPSG:5179) |
| 후처리 | — | pyproj로 EPSG:4326 변환 → `geocode_cache`(성공 · 실패, `accuracy`, `provider='juso'`) |

- **신청:** "주소정보 API 연계" 카드에서 API 종류를 바꿔 **두 번** 신청한다. 처음엔 개발용(즉시 발급, 사용 기간 제한), 배포할 때 운영용으로 다시 신청하고 서비스 URL을 등록한다. 용도 예시: "비상업 팀 포트폴리오. 공공 전월세 거래 데이터의 지번 주소를 좌표로 변환하여 역세권 시세 집계에 사용". 배포 서버에서 변환을 돌리면 10/16 배포 전에 운영용 키를 받아 둔다.
- **호출 대상:** 캐시에 없는 주소만 호출한다.
- **저장:** DB에 저장하는 좌표는 이 API 결과뿐이다.
- **대안:** 대상 건물이 많아 호출 한도가 부담되면, 주소정보 다운로드의 위치정보(좌표) DB 파일을 받아 로컬에서 조인한다.

### 4.7 사람인: 채용공고 검색

- **신청:** 대표 1인 명의로만 신청한다. 접근 키는 제3자 공유가 금지되어 있어, 다른 팀원은 `tests/fixtures/saramin_*.json`으로 개발한다. 이용 목적 예시(100자 이내): "공공데이터 기반 기업 분석 비상업 포트폴리오에서 기업별 진행 중 채용공고 목록과 원문 링크를 제공". 승인 시점을 알 수 없으므로 신청만 해 두고 기다리지 않는다.
- **호출 원칙:** 서버(pipeline)에서만 호출하고 브라우저에서 직접 부르지 않는다. 결과는 `job_posting`에 캐시하고 `expires_at`으로 관리해 하루 500회 안에 맞춘다. 대상 직무 코드 × 지역(서울 · 경기) 페이지 단위로 수집하고, 남은 범위는 다음 날 이어간다.
- **저장 범위:** 공고 번호, 회사 매칭, 마감일, 연봉 코드, 근무지 코드, 원문 링크만 저장한다. 본문은 저장하지 않는다.
- **표시 조건:** 화면에 "채용정보 제공: 사람인"과 링크를 표시한다. 비상업 이용만 허용되고 파생제품 제한 조항이 있다.
- **승인 전:** 사람인 검색 결과 페이지로 가는 바로가기 링크(`https://www.saramin.co.kr/zf_user/search?searchword={회사명}`)만 둔다.

### 4.8 네이버 클라우드 플랫폼 Maps

| 상품 | 사용 | 용도 |
|---|---|---|
| Dynamic Map | 필수 | 지도, 회사 핀, 팝업. `react-naver-maps`로 `ncpKeyId`(Client ID) 로드 |
| Geocoding | 선택(P2) | 지도 검색창의 주소 · 역 위치로 이동. **결과를 DB에 저장하지 않는다** |
| Static Map, Reverse Geocoding, Directions 5/15 | 사용 안 함 | — |

- **신청:** 콘솔 → Services → AI·Application Service → Maps에서 대표 1인 계정에 Application 하나를 만든다. 무료 이용량 안에서 쓰도록 이용량 알림을 켜 둔다.
- **노출 범위:** 브라우저에는 Client ID만 노출된다. Client Secret이 필요한 REST API는 쓰지 않는다. 필요해지면 FastAPI를 거쳐 호출하고, Secret은 서버 환경 변수에만 둔다.
- **도메인 등록:** Application의 Web 서비스 URL에 `http://localhost:3000`, 팀원 로컬 도메인, Vercel 배포 도메인을 등록한다. 등록하지 않은 도메인에서는 지도가 뜨지 않는다.

## 5. 설계 검토: 발견한 문제점

| # | 심각도 | 문제 | 제안 |
|---|---|---|---|
| A1 | 높음 | **커서가 정렬과 맞지 않는다.** SPEC은 `cursor`를 `company_id > :cursor`로 정의하지만, `sort=growth`나 `sort=deadline`이면 `company_id` 순서가 아니라 다음 페이지에서 항목이 빠지거나 겹친다 | 커서를 `(정렬값, company_id)` 쌍으로 인코딩(base64)하고 `WHERE (sort_col, company_id) > (:v, :id)` 키셋 페이지네이션 |
| A2 | 높음 | **이름 검색이 앞부분 일치뿐이다.** `name_norm LIKE 'q%'`라 "소프트"로 "예시소프트"를 못 찾는다. 사용자 입력에 `normalize_name`을 적용하지 않으면 "(주)예시"도 못 찾는다 | 입력도 `normalize_name`으로 정규화. 앞부분 일치를 우선 정렬하되, MVP 이후 n-gram 전문 검색(`FULLTEXT … WITH PARSER ngram`) 검토 |
| A3 | 중간 | **`/stations/{id}/rent`의 `months` 1~24 자유 입력**은 미리 집계가 불가능해 요청 시점 공간 조인이 필요하다 | `months`를 6 · 12 · 24로 제한([04 문서](./04_database_design.md) D7) |
| A4 | 중간 | **지도 메인 화면에 필요한 필드가 계약에 없다**(위 3장 bbox, 목록 지표, 좌표 없는 회사 수) | 3장 후보를 Phase 8 전에 계약에 반영. T4는 그 전까지 목 응답으로 개발 |
| A5 | 중간 | **최근 자료 없는 회사는 검색에 안 나온다.** 검색은 `mart_company_summary`를 읽는데 그 회사들은 행이 없다. 상세는 `stale`을 지원하지만 들어갈 경로가 없다 | 검색 결과에 `company`는 있고 summary가 없는 회사를 "최근 자료 없음"으로 뒤에 붙이거나(`include_stale=true`), 의도적으로 제외하고 문서에 명시 |
| A6 | 낮음 | 응답 단위가 섞여 있다. 연봉은 원, 전월세는 만 원, `monthly_pay_est`는 정의 없음 | 필드명 접미사로 단위를 고정(`_won`, `_man`)하거나 이 문서 1장 단위 규칙을 OpenAPI 설명에 넣는다 |
| A7 | 낮음 | 공개 API라 대량 수집에 열려 있다 | 배포 후 Railway 앞단 또는 미들웨어에서 IP당 요청 수 제한(P2) |
