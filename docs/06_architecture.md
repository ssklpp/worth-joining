# 06. 아키텍처

| 항목 | 내용 |
|---|---|
| 대상 | 팀 전원. 트랙 간 경계와 배포 구성을 맞추는 문서 |
| 기준 | SPEC 1~4장, 10장(Phase 7 배포), 12장(팀 운영) |
| 관련 문서 | [03_ui_design.md](./03_ui_design.md) · [04_database_design.md](./04_database_design.md) · [05_api_spec.md](./05_api_spec.md) |
| 상태 | 초안 · 2026-10-08 |

---

## 1. 전체 구조

```mermaid
flowchart LR
  subgraph SRC[데이터 출처]
    NPS[국민연금 사업장 CSV<br/>월]
    DART[OpenDART<br/>수시 · 분기]
    RENT[서울시 전월세<br/>CSV + Open API, 주]
    STN[도시철도 역 XLSX<br/>연]
    JUSO[주소정보누리집<br/>검색 + 좌표, 신규 주소만]
    SRM[사람인 API<br/>일, 500회]
  end

  subgraph PIPE[pipeline/ · Python 3.12]
    COMMON[common/<br/>http 재시도 · 호출 수 기록<br/>normalize · ingestion_log]
    LOADERS[nps · dart · rent · stations<br/>geocode · saramin]
    MART[refresh_mart<br/>sql/q1 → q2 → q6 …]
  end

  subgraph DB[MariaDB 11.4]
    RAW[(raw_*)]
    CORE[(core)]
    MARTDB[(mart_*)]
    OPS[(ingestion_log<br/>api_call_log)]
  end

  subgraph API[app/ · FastAPI]
    R[routers] --> REPO[repositories<br/>SQL text()] --> SVC[services<br/>flags]
  end

  subgraph WEB[web/ · Next.js]
    MAP[지도 메인 + 패널]
    NMAP[NaverMap.tsx]
  end

  SRC --> LOADERS
  COMMON -.-> LOADERS
  LOADERS --> RAW --> CORE
  LOADERS --> OPS
  CORE --> MART --> MARTDB
  MARTDB --> REPO
  SVC --> WEB
  NMAP -.표시만.-> MAP
```

### 구성 요소와 책임

| 구성 요소 | 책임 | 하지 않는 것 | 트랙 |
|---|---|---|---|
| `pipeline/` | 수집, 인코딩 변환(CP949 → UTF-8), 정규화, 매칭, 지오코딩, 품질 검사, mart 갱신 | 화면용 응답 생성 | T1 |
| `migrations/`, `sql/` | 스키마(Alembic), mart 갱신 SQL, 공간 SQL | 데이터 수집 | T2 |
| `app/` | 읽기 전용 REST, 파라미터 검증, flags · 문구 | 집계 계산, 외부 API 호출 | T3 |
| `web/` | 화면, 차트, 지도, 비교 상태 | 데이터 가공(계산은 API가 끝내서 준다) | T4 |

## 2. 데이터 흐름

| 흐름 | 주기 | 경로 | 멱등 장치 |
|---|---|---|---|
| 국민연금 | 월 1회 | CSV → UTF-8 → `LOAD DATA LOCAL INFILE` → `raw_nps_workplace`(해당 월 삭제 후 적재) → `company` → `workplace` → `workplace_monthly` → 품질 검사 → `refresh_mart` | 해당 월 raw 교체, 자연키 UNIQUE, 체크섬 |
| DART | 월 1회(고유번호) · 분기 1회(재무) | corpCode.xml → `dart_corp` → 매칭 → `company_dart_link` → 주요계정 → `dart_financial` | PK 기준 UPSERT |
| 지오코딩 | 신규 주소만 | `rep_addr_key` 중 캐시에 없는 것 → juso 검색 → 좌표 → pyproj(5179→4326) → `geocode_cache` | `addr_key` PK, 실패도 기록 |
| 전월세 | 주 1회(최근 3개월 재수집) | CSV(초기) · Open API(증분) → `raw_rent_contract` → 필터 → `rent_contract` → `building` 연결 → q5 | `row_hash` UNIQUE, 월 파티션 |
| 사람인 | 일 1회 | 검색 API → `raw_saramin_job` → 매칭 → `job_posting`(본문 없음) → `mart_company_jobs` | `job_id` PK, 마감 30일 뒤 삭제 |

모든 수집기는 키가 비어 있으면 실패하지 않고 경고 후 건너뛴다. 호출 한도에 닿으면 멈추고 다음 실행에서 이어간다.

## 3. 기술 스택 (최종)

SPEC 1장을 확정안으로 삼는다. 아래 "확정 사항"은 SPEC에서 둘 중 하나로 열려 있던 것을 정한 것이다.

| 영역 | 기술 |
|---|---|
| 언어 | Python 3.12, TypeScript, Node.js 20+ |
| 수집 · 가공 | httpx, pandas(파일 정제만), openpyxl, rapidfuzz, pyproj |
| DB | MariaDB 11.4 LTS (InnoDB, utf8mb4). Alembic |
| DB 드라이버 | API: SQLAlchemy 2.0 async + asyncmy (`DATABASE_URL`). 파이프라인 · Alembic: pymysql (`DATABASE_URL_SYNC`, `local_infile=True`) |
| 백엔드 | FastAPI, uvicorn, Pydantic v2, pydantic-settings |
| 프론트엔드 | Next.js(App Router), Recharts, 네이버 지도 Web Dynamic Map(`react-naver-maps`) |
| 테스트 | pytest, pytest-asyncio, httpx AsyncClient, locust. 로컬 테스트 DB + CI 서비스 컨테이너 `mariadb:11.4` |
| 품질 | ruff |
| 배포 | Railway(mariadb, api, pipeline cron), Vercel(web), GitHub Actions(CI) |

| 확정 사항 | 결정 | 이유 |
|---|---|---|
| 배치 스케줄러 | **Railway cron이 CLI를 실행**(`python -m pipeline.<source>.load`, `python -m pipeline.refresh_mart`). APScheduler는 로컬 개발용으로만 둔다 | 상시 프로세스 없이 cron 한 번에 끝난다. 두 스케줄러가 같은 작업을 겹쳐 돌리는 것을 막는다(아래 R1) |
| 화면 메인 | 지도 메인(03 문서 5장) | SPEC 9장은 검색 메인. **SPEC 수정은 팀장 결정 필요** |
| 동기 · 비동기 | API만 async, 파이프라인은 sync | `LOAD DATA LOCAL INFILE`과 대량 적재는 sync 드라이버가 단순하다 |

## 4. 배포 구성

```
GitHub (main 보호, PR + 리뷰 1 + CI)
  ├─ GitHub Actions: ruff check + pytest (mariadb:11.4 서비스 컨테이너)
  ├─ Railway (팀 계정)
  │    ├─ mariadb   : mariadb:11.4 이미지 + 볼륨. 초기 데이터는 로컬 백필 DB를 mariadb-dump로 복원
  │    ├─ api       : uvicorn app.main:app. 환경 변수: DATABASE_URL, DB_SSL_VERIFY=true
  │    └─ pipeline  : cron (월 1회 국민연금 + mart, 주 1회 전월세, 일 1회 사람인)
  └─ Vercel: web. 환경 변수: NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_NAVER_MAP_CLIENT_ID
```

| 비밀 정보 | 보관 위치 |
|---|---|
| 공공데이터포털 · DART · 서울 열린데이터 · juso(개발용) | 각자 `.env` |
| juso(운영용), 사람인 | Railway 환경 변수에만 |
| 네이버 지도 Client ID | 공개 값. NCP 콘솔에 도메인 등록으로 보호. Secret은 쓰지 않는다 |

## 5. 아키텍처 검토: 발견한 문제점

| # | 심각도 | 문제 | 제안 |
|---|---|---|---|
| R1 | 중간 | **스케줄러가 둘이다.** SPEC 2장은 `pipeline/scheduler.py`(APScheduler), 10장은 Railway `pipeline` cron을 둔다. 둘 다 켜면 같은 적재가 겹쳐 돈다 | 운영은 Railway cron 하나(3장 확정 사항). 겹침 방지로 `ingestion_log`에 `running` 행이 있으면 시작하지 않는 잠금 추가 |
| R2 | 중간 | **국민연금 월 파일 자동 수집이 정해지지 않았다.** 파일 데이터는 공공데이터포털에서 내려받는 방식일 수 있어 cron만으로 받을 수 있는지 불확실하다 | Phase 1에서 자동 다운로드 가능 여부 확인. 안 되면 runbook에 "월 1회 수동 다운로드 → 업로드 → 적재 명령" 절차를 적는다 |
| R3 | 중간 | **mart 갱신 중 일관성.** q1 → q2를 한 트랜잭션으로 묶어도 q6(회사-역), 지도용 지오코딩은 별도 단계라, 갱신 사이에 API가 서로 다른 기준월의 데이터를 섞어 볼 수 있다 | `refresh_mart`가 q1 · q2 · q6를 한 트랜잭션에서 실행하고, 마지막에 `as_of`를 기록하는 `mart_meta(latest_ym, refreshed_at)` 한 행을 갱신. API의 `as_of`는 이 행에서 읽는다 |
| R4 | 중간 | **지오코딩 범위가 지도 기능을 제한한다.** juso 호출 한도 때문에 Phase 8은 일부 회사만 좌표를 얻는다. 지도 메인 화면에서는 좌표 없는 회사가 아예 안 보인다 | 좌표 없는 회사 수를 응답에 넣고 화면에 안내([05 문서](./05_api_spec.md) 3장). 백필은 가입자 많은 순, 담당자 1명이 여러 날 실행 |
| R5 | 중간 | **화면 구조가 SPEC과 다르다.** 지도 메인 + 패널 구조(03 문서)는 SPEC 9장(검색 메인, `/map` 별도)과 다르고, API에도 bbox 같은 필드가 더 필요하다 | 팀장이 채택 여부를 정하고 `docs/decisions/001-지도-메인-화면.md`로 기록. 채택하면 SPEC 8 · 9장 수정 PR |
| R6 | 낮음 | **단일 DB에서 배치 쓰기와 API 읽기를 같이 한다.** 월 1회 대량 `LOAD DATA`와 mart 재계산 동안 API 응답이 느려질 수 있다 | MVP 규모에서는 허용. 적재는 새벽 시간대 cron. p95 300ms 목표는 locust로 적재 중에도 한 번 측정 |
| R7 | 낮음 | **백업이 정해지지 않았다.** Railway 볼륨 하나에 모든 데이터가 있다 | 월 적재 후 `mariadb-dump`를 받아 보관하는 절차를 runbook에 추가 |

### 설계 문제점 요약 (03~06 문서 전체)

결정이 필요한 순서대로 정리했다.

| 우선 | 항목 | 담당 | 언제까지 |
|---|---|---|---|
| 1 | D1 q2가 사라진 회사 요약을 지우지 않음 | T2 | Phase 3 (10/14) |
| 2 | D2 `nps_rate` 범위 밖 달이 조용히 빠짐 | T1 · T2 | Phase 2 (10/13) |
| 3 | A1 정렬과 맞지 않는 커서 | T3 | Phase 4 (10/15) |
| 4 | A2 이름 검색이 앞부분 일치뿐 | T3 · T1 | Phase 4 (10/15) |
| 5 | R2 국민연금 파일 자동 수집 가능 여부 | T1 | Phase 1 (10/08) |
| 6 | R5 · A4 지도 메인 채택과 API 필드 추가 | 팀장 · T3 · T4 | Phase 8 전 (10/16) |
| 7 | D6 표본 부족 회사를 백분위에서 뺄지 | T2 | Phase 3 (10/14) |
| 8 | D4 · D5 · R3 mart 갱신의 삭제 · 트랜잭션 정리 | T2 | Phase 3 (10/14) |
| 9 | D7 · A3 역 시세 기간을 6 · 12 · 24로 제한 | T2 · T3 | Phase 9 |
| 10 | D3 상호 변경 시 회사 분리 | T1 | MVP 이후 |
