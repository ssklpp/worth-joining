# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 상태

다닐만한가(Worth Joining)는 공공데이터(국민연금 사업장 내역, OpenDART, 서울시 전월세 실거래가, 사람인 채용공고)로 회사의 인원 추이 · 입퇴사율 · 추정 연봉을 보여주는 구직자용 웹 서비스다. 4인 팀, 기간은 2026-10-02 ~ 2026-10-21이고 MVP 배포 목표는 10/16이다.

지금 저장소에는 **기획 문서만 있고 코드는 아직 없다.** `SPEC.md`가 구현 지시서이며 다른 문서와 충돌하면 SPEC을 따른다. 무엇이든 만들기 전에 먼저 읽는다.
- `SPEC.md`: 기술 스택, 저장소 구조, DDL(5장), 계산 규칙(6장), 핵심 SQL(7장), API 계약(8장), 화면(9장), 단계별 진행과 완료 조건(10장), 팀 운영 규칙(12장)
- `docs/01_project_overview.md`, `README.md`: 개요와 범위
- `docs/02_requirements.md`: 요구사항 ID, 우선순위(P0~P3), Task ID(10장, 예: `T1-04`)
- `docs/03_ui_design.md`, `docs/mockups/map-home.html`: 화면 디자인 가이드(지도 메인 구조, 색 · 글꼴 토큰, 기준 범위 막대, flags 표현)와 시안. `web/` 작업 전에 읽는다. `company-detail.html`은 이전안
- `docs/04_database_design.md`: ERD, 테이블 관계, SPEC에 없는 DDL 제안, DB 설계 문제점(D1~D9)
- `docs/05_api_spec.md`: API 구조 · 엔드포인트 · SPEC 밖 후보, 외부 API와 키(4장: 발급 · 보관 · `.env.example` · 한도 · 호출 원칙), API 문제점(A1~A7)
- `docs/06_architecture.md`: 전체 구조, 데이터 흐름, 최종 기술 스택, 배포, 아키텍처 문제점(R1~R7)과 전체 우선순위표. 이 문서들의 "제안"은 SPEC에 반영되기 전까지 확정이 아니다

**SPEC.md는 약 950줄(약 27k 토큰)이라 전체를 읽지 않는다.** 먼저 `Grep "^##+ " SPEC.md`로 장 위치를 확인하고, 필요한 장만 줄 범위(offset/limit)로 읽는다. 장별 대략의 시작 줄은 아래와 같다(문서가 수정되면 바뀔 수 있다).

| 장 | 내용 | 시작 줄 |
|---|---|---|
| 0 | 작업 규칙 | 9 |
| 1 · 2 · 3 | 기술 스택 · 저장소 구조 · 환경 변수 | 24 · 39 · 71 |
| 4 | 데이터 소스와 수집 규칙 | 105 |
| 5 | DB (5.2 DDL 161, 5.3 MariaDB 주의사항 371) | 147 |
| 6 | 계산 규칙 · 상호 정규화 · 매칭 순서 | 386 |
| 7 | 핵심 SQL (q1, q2, 지도, 비교, q5, q6, 파티션 순환) | 424 |
| 8 · 9 | API 계약 · 화면 | 618 · 645 |
| 10 | 진행 단계 (Phase 0~11과 완료 조건) | 660 |
| 11 · 12 | 하지 않는 것 · 팀 운영 | 848 · 860 |

## 명령어 (예정. SPEC 3장 · 10장 참고)

```bash
alembic upgrade head                         # 스키마 적용 (DB: worth_joining, worth_joining_test)
python -m pipeline.nps.load --ym 202608      # 국민연금 한 달치 적재 (멱등)
python -m pipeline.refresh_mart              # sql/q1 → q2를 한 트랜잭션으로 실행
uvicorn app.main:app --reload                # API, :8000/docs
cd web && npm install && npm run dev         # 프론트엔드, :3000
ruff check .
pytest                                       # 전체 테스트
pytest tests/sql/test_x.py::test_name        # 단일 테스트
```

필요한 것: Python 3.12, Node 20+, MariaDB 11.4(로컬 설치. Docker는 선택). `.env.example`을 `.env`로 복사해 쓴다. 로컬에서는 `DB_SSL_VERIFY=false`로 둔다. 11.4는 서버 인증서를 자동 생성하고 클라이언트가 기본으로 검증하기 때문이다. 적재기가 `LOAD DATA LOCAL INFILE`을 쓰므로 서버와 클라이언트 연결 양쪽에서 `local_infile`을 켜야 한다. API 키가 비어 있는 수집기는 실패하지 않고 경고 로그를 남긴 뒤 건너뛴다.

## 아키텍처

```
데이터 출처 → pipeline/ (Python 배치, APScheduler) → MariaDB raw_* → core → mart_* → app/ (FastAPI, 읽기 전용) → web/ (Next.js)
```

- **3계층 DB.** `raw_*`는 원본을 받은 그대로 보존한다. core 테이블(`company`, `workplace`, `workplace_monthly`, `dart_*`, `geocode_cache`, `station`, `building`, `rent_contract` 등)은 정규화된 데이터, `mart_*`는 미리 집계한 데이터다. **API는 `mart_*`만 읽고**, `company` · `region` · `industry` · `geocode_cache` 같은 작은 조회용 조인만 허용한다. 요청 시점에 집계하지 않는다. 정제 규칙이 바뀌면 raw에서 다시 만든다.
- **회사 식별**은 `biz_no6` + `name_norm`(`pipeline/common/normalize.py`의 `normalize_name`)이다. 출처 사이에 공통 키가 없다. DART · 사람인 매칭 순서는 정규화 이름 완전 일치(+사업자번호 6자리) → rapidfuzz `token_sort_ratio ≥ 85` → 그 외에는 연결하지 않음. `match_type`과 `match_score`는 항상 기록한다.
- **멱등 적재.** `INSERT … ON DUPLICATE KEY UPDATE` 또는 `REPLACE`와 해시 키(`row_hash`)를 쓴다. 같은 월을 다시 넣어도 행 수와 값이 같아야 한다. 모든 실행은 체크섬과 함께 `ingestion_log`에 기록하고, 이미 `success`인 체크섬은 건너뛴다. 소스별 일일 호출 수는 `api_call_log`에 남기고 한도에 닿으면 수집을 멈춘다. 품질 검사(전월 대비 행 수 ±10% 초과, `members ≤ 0`, 고지금액이 상한 초과)에 걸리면 `status='failed'`로 남기고 mart를 갱신하지 않는다.
- **기준값은 코드 상수가 아니라 테이블에 둔다.** 보험료율 · 소득 상한은 `nps_rate`(2025년까지 9%, 2026년부터 9.5%), 전월세전환율은 `conversion_rate`에 둔다.
- **통계는 SQL로 작성한다**(윈도 함수, CTE, 조건부 집계). SQL은 `sql/`에 파일로 두고, `app/repositories/`에서는 `text()`로 실행한다. pandas는 파일 정제에만 쓴다.
- **모든 응답에 `as_of`를 넣는다.** 추정치가 들어간 응답에는 `flags`(`salary_is_lower_bound`, `small_sample`, `short_history`, `stale`, `approx_location`, `name_matched`, `period_extended_to_24m`)도 넣으며, `app/services/flags.py`에서 만든다. `company` 행은 있는데 `mart_company_summary` 행이 없는 회사는 `status:"stale"`과 `last_seen_ym`을 내려준다.
- **프론트엔드.** 타입은 `/openapi.json`에서 생성하고, 백엔드가 준비되기 전에는 목 응답으로 개발한다. 네이버 지도는 `web/components/map/NaverMap.tsx`로 감싸고 화면에서는 `markers`, `onSelect`, `center` 같은 공통 props만 쓴다.

## 틀리기 쉬운 계산 규칙

- 직전 달 자료가 없으면 비율은 NULL이다. `LAG`만 쓰지 말고 `prev_ym = PERIOD_ADD(snapshot_ym, -1)`을 확인한다.
- 지표가 NULL인 행은 윈도 파티션을 따로 나눠(`PARTITION BY industry_code, 지표 IS NULL`) 백분위 0을 받지 않게 한다.
- N개월 기간 조건은 `contract_ym > PERIOD_ADD(최신월, -N)`이다. `>=`가 아니라 `>`다.
- 대표 사업장은 최신 월 가입자 수가 가장 많은 사업장이다. 회사-역 순위는 대표 사업장 하나로만 매긴다. 모든 사업장으로 매기면 같은 역이 중복된다(검증된 버그).
- 추정 연봉은 소득 상한 때문에 **하한 추정치**다. 표본 부족 기준은 회사 가입자 10명 미만, 역 계약 20건 미만이다.

## MariaDB 주의사항 (SPEC 5.3장. SQL 회귀 테스트로도 확인)

- 생성 컬럼의 원본이 `CHAR`면 오류 1901로 거부되므로 원본은 `VARCHAR`로 둔다. 함수 인덱스 문법은 쓰지 않고 생성 컬럼 + 일반 인덱스로 대체한다.
- 컬럼 정의에 `SRID 4326`을 쓰지 않는다. 좌표는 항상 `POINT(경도, 위도)` 순서다. 공간 인덱스 컬럼은 `NOT NULL`이어야 한다.
- 파티션 키는 모든 PK · UNIQUE 키에 포함되어야 한다.
- `PERCENTILE_CONT`는 윈도 함수로만 동작하므로 `DISTINCT`와 함께 쓴다.
- `ST_Distance_Sphere`만 단독으로 쓰면 전체 스캔이 된다. 반드시 앞에 `MBRContains(ST_Buffer(pt, deg), other)`를 붙인다(0.006° ≈ 500m, 0.012° ≈ 1km).
- 11.4는 비용 기반 옵티마이저라 10.11과 실행 계획이 다를 수 있다. `EXPLAIN`은 11.4 결과를 기준으로 삼는다.

## 데이터 이용 조건 (반드시 지킬 것)

- DB에 저장하는 좌표는 주소정보누리집(juso)에서 얻은 것만 쓴다. 카카오 · 네이버 · 브이월드 지오코딩 결과는 저장하지 않는다. `geocode_cache.provider`는 모두 `juso`여야 한다. EPSG:5179 → 4326 변환은 pyproj로 한다.
- 네이버 지도는 화면 표시용으로만, Web JS와 Client ID로만 쓴다. Client Secret이 필요한 REST API는 쓰지 않는다.
- 사람인은 공고 번호, 회사 매칭, 마감일, 연봉 코드, 근무지 코드, 원문 링크만 저장하고 본문은 저장하지 않는다. 화면에 "채용정보 제공: 사람인"을 표시한다. 하루 500회 한도다. 키는 대표 1인만 가지고 있으므로 다른 팀원은 fixture로 개발한다.
- 서비스 어디에도 LLM · RAG · 임베딩 기능을 쓰지 않는다.

## 팀 규칙

- 브랜치 이름은 `<type>/<track>-<topic>`(예: `feat/t1-nps-loader`)이다. 보호된 `main`에는 리뷰 승인 1명 이상과 CI 통과 후 squash merge한다. 이슈와 PR에는 요구사항 ID와 Task ID를 적는다.
- **GitHub에 push하는 모든 커밋은 [Conventional Commits 1.0.0](https://www.conventionalcommits.org/ko/v1.0.0/)을 지킨다.** squash merge 커밋 제목과 PR 제목도 같은 형식을 쓴다.
  - 제목 형식: `<type>(<scope>): <설명>`. scope는 선택이다(예: `docs(readme): 화면 시안 추가`, `feat(pipeline): 국민연금 월 적재기 추가`).
  - type: SPEC의 `feat`, `fix`, `test`, `docs`, `chore`를 기본으로 쓰고, 필요하면 `refactor`, `perf`, `style`, `ci`, `build`도 쓴다.
  - 설명은 한국어로, 무엇을 바꿨는지 한 줄로 쓴다. 마침표는 붙이지 않는다.
  - 호환성을 깨는 변경(API 계약 · 스키마)은 `feat!:`처럼 `!`를 붙이고, 본문에 `BREAKING CHANGE: <내용>`을 적는다.
  - 본문에는 왜 바꿨는지를 쓴다. 커밋 하나에는 논리적인 변경 하나만 담는다.
  - push 전에 `git log origin/main..HEAD --format=%s`로 모든 제목이 형식에 맞는지 확인하고, 맞지 않으면 push하지 않고 고친다.
- 트랙별 담당 영역: T1 `pipeline/`, T2 `migrations/` · `sql/` · `tests/sql/`, T3 `app/` · `tests/api/` · `.github/`, T4 `web/`. 마이그레이션은 T2가 관리하므로 병합 전에 `alembic heads`가 정확히 1개인지 확인한다. API 계약 변경은 별도 PR로 하고 T4의 리뷰를 받는다.
- 테스트는 실제 API 키 없이 `tests/fixtures/`(국민연금 축소 CSV, DART · 전월세 · 사람인 응답 샘플)로 돌아가야 한다. `tests/conftest.py`는 세션마다 테스트 DB를 비우고 `alembic upgrade head`를 한 번 실행하며, 테스트마다 트랜잭션을 롤백한다.
- 결정 사항은 `docs/decisions/NNN-제목.md`에 기록한다.
- ponytail 스킬(코드 최소화)을 쓰더라도 SPEC이 정한 구조(`repositories/`, `services/`, 3계층 DB, Alembic)와 위 테스트 규칙(`tests/fixtures/`, SPEC의 회귀 테스트 목록)은 줄이지 않는다. 이것들은 요청된 사항이다.
