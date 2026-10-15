# 06. 아키텍처

| 항목 | 내용 |
|---|---|
| 대상 | 팀 전원. 트랙 간 경계와 배포 구성을 맞추는 문서 |
| 기준 | SPEC 1~4장, 10장(Phase 7 배포), 12장(팀 운영) |
| 관련 문서 | [03_ui_design.md](./03_ui_design.md) · [04_database_design.md](./04_database_design.md) · [05_api_spec.md](./05_api_spec.md) |
| 상태 | 최종 수정 2026-10-15 (실제 운영 방식 반영: 적재 cron 없음, 채용 연계 없음) |

---

## 1. 전체 구조

```mermaid
flowchart LR
  subgraph SRC[데이터 출처]
    NPS[국민연금 사업장 CSV<br/>월]
    DART[OpenDART<br/>수시 · 분기]
    RENT[서울시 전월세<br/>연도별 CSV, 갱신 때]
    STN[도시철도 역 XLSX<br/>연]
    JUSO[주소정보누리집<br/>검색 API 일부 + 서울 주소 파일]
  end

  subgraph PIPE[pipeline/ · Python 3.12]
    COMMON[common/<br/>http 재시도 · 호출 수 기록<br/>normalize · ingestion_log]
    LOADERS[nps · dart · rent · stations<br/>geocode · region]
    MART[refresh_mart<br/>q1 → q2 → q6 → q5 → q5t]
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
| 국민연금 | 월 1회(수동, runbook 4장) | CSV → UTF-8 → `LOAD DATA LOCAL INFILE` → `raw_nps_workplace`(해당 월 삭제 후 적재) → `company` → `workplace` → `workplace_monthly` → 품질 검사 → `refresh_mart` | 해당 월 raw 교체, 자연키 UNIQUE, 체크섬 |
| DART | 월 1회(고유번호) · 분기 1회(재무) | corpCode.xml → `dart_corp` → 매칭 → `company_dart_link` → 주요계정 → `dart_financial` | PK 기준 UPSERT |
| 지오코딩 | 신규 주소만 | 회사마다 DART 본사 주소 → 도로명 + 사업장명 검색 → 도로 중심 → 동 중심 순서(decisions/004). juso 검색 → 좌표 → pyproj(5179→4326) → `geocode_cache` → `company_location` | `addr_key` · `company_id` PK, 실패도 기록 |
| 전월세 | 갱신할 때(수동, 분기 또는 필요할 때) | 연도별 CSV 재다운로드 → `raw_rent_contract` → 필터 → `rent_contract` → `building` 연결(주소 파일 좌표) → q5 · q5t(반경 500 · 750m). 계획했던 Open API 주 1회 증분은 만들지 않았다 | `row_hash` UNIQUE, 월 파티션 |
| ~~사람인~~ | — | 하지 않음([decisions/008](./decisions/008-채용-연계를-바로가기로-대체.md)). 회사 상세의 검색 바로가기만 | — |

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
| 프론트엔드 | Next.js 15(App Router), Recharts, 네이버 지도 Web Dynamic Map(`react-naver-maps`) |
| 테스트 | pytest, pytest-asyncio, httpx AsyncClient, locust. 로컬 테스트 DB + CI 서비스 컨테이너 `mariadb:11.4` |
| 품질 | ruff |
| 배포 | Railway(mariadb, api), Vercel(web), GitHub Actions(CI). 적재는 로컬에서 하고 덤프 · 테이블로 반영한다(cron 없음) |

| 확정 사항 | 결정 | 이유 |
|---|---|---|
| 배치 스케줄러 | 계획: Railway cron이 CLI를 실행. **실제(2026-10-12~): 스케줄러 없음.** 로컬에서 CLI를 순서대로 실행하고 덤프 복원 또는 테이블 업로드로 배포 DB에 반영한다([runbook](./runbook.md) 4장). APScheduler도 쓰지 않는다 | 국민연금 파일을 자동으로 받을 수 없고(R2), 품질 검사 결과를 사람이 본 데이터만 올리는 편이 안전하다. Railway 비용도 아낀다 |
| 화면 메인 | 지도 메인(03 문서 5장) | 2026-10-13 채택([decisions/006](./decisions/006-지도-메인-화면.md)), SPEC 9장도 고쳤다 |
| 동기 · 비동기 | API만 async, 파이프라인은 sync | `LOAD DATA LOCAL INFILE`과 대량 적재는 sync 드라이버가 단순하다 |

## 4. 배포 구성

```
GitHub (main 보호, PR + 리뷰 1 + CI)
  ├─ GitHub Actions: test(ruff + pytest, mariadb:11.4 서비스 컨테이너) · web(lint · typecheck · build · API 타입 생성 비교) · api-image(Docker 빌드)
  ├─ Railway (팀 계정)
  │    ├─ mariadb   : mariadb:11.4 이미지 + 볼륨. 초기 데이터는 로컬 백필 DB를 mariadb-dump로 복원
  │    ├─ api       : Dockerfile(uvicorn app.main:app). 환경 변수: DATABASE_URL, DB_SSL_VERIFY=false(사설망), CORS_ORIGINS
  │    └─ (pipeline 서비스는 두지 않는다. 로컬 적재 → 덤프 복원 · 테이블 업로드, runbook 4 · 6장. DB는 TCP Proxy를 반영할 때만 켠다)
  └─ Vercel: web. 환경 변수: NEXT_PUBLIC_API_BASE_URL, NEXT_PUBLIC_NAVER_MAP_CLIENT_ID
```

GitHub 보호 규칙은 목표 상태다. 지금 적용된 단계는 [decisions/001](./decisions/001-저장소-설정과-main-보호.md)을 따른다.

| 비밀 정보 | 보관 위치 |
|---|---|
| 공공데이터포털 · DART · 서울 열린데이터 · juso | 각자 `.env`(적재는 로컬에서만 한다) |
| DB 접속 정보 · `CORS_ORIGINS` | Railway 환경 변수. 배포 API는 외부 API를 부르지 않아 API 키가 없다. 사람인은 쓰지 않는다 |
| 네이버 지도 Client ID | 공개 값. NCP 콘솔에 도메인 등록으로 보호. Secret은 쓰지 않는다 |

## 5. 아키텍처 검토: 발견한 문제점

| # | 심각도 | 문제 | 제안 |
|---|---|---|---|
| R1 | 중간 | **스케줄러가 둘이다.** SPEC 2장은 `pipeline/scheduler.py`(APScheduler), 10장은 Railway `pipeline` cron을 둔다. 둘 다 켜면 같은 적재가 겹쳐 돈다 | 운영은 Railway cron 하나(3장 확정 사항). 겹침 방지로 `ingestion_log`에 `running` 행이 있으면 시작하지 않는 잠금 추가. **2026-10-12: MVP는 cron 없이 로컬 적재 → 덤프 복원([runbook](./runbook.md) 4 · 6장). 10/15: 기간 안에는 cron을 두지 않기로 확정(Railway 비용). 스케줄러가 하나도 없어 겹침 문제는 생기지 않는다** |
| R2 | 중간 | **국민연금 월 파일 자동 수집이 정해지지 않았다.** 파일 데이터는 공공데이터포털에서 내려받는 방식일 수 있어 cron만으로 받을 수 있는지 불확실하다 | Phase 1에서 자동 다운로드 가능 여부 확인. 안 되면 runbook에 "월 1회 수동 다운로드 → 업로드 → 적재 명령" 절차를 적는다 |
| R3 | 일부 반영 | **mart 갱신 중 일관성.** q1 → q2를 한 트랜잭션으로 묶어도 q6(회사-역), 지도용 지오코딩은 별도 단계라, 갱신 사이에 API가 서로 다른 기준월의 데이터를 섞어 볼 수 있다 | `refresh_mart`가 q1 · q2 · q6를 한 트랜잭션에서 실행하고, 마지막에 `as_of`를 기록하는 `mart_meta(latest_ym, refreshed_at)` 한 행을 갱신. API의 `as_of`는 이 행에서 읽는다. **Phase 9: `refresh_mart`가 q1 → q2 → q6 → q5 → q5t를 한 트랜잭션으로 실행해 섞임을 막는다. `mart_meta`는 만들지 않았고 `as_of`는 mart의 최신 월에서 읽는다** |
| R4 | 반영 | **지오코딩 범위가 지도 기능을 제한한다.** juso 호출 한도 때문에 Phase 8은 일부 회사만 좌표를 얻는다. 지도 메인 화면에서는 좌표 없는 회사가 아예 안 보인다 | 좌표 없는 회사 수를 응답에 넣고 화면에 안내([05 문서](./05_api_spec.md) 3장). 백필은 가입자 많은 순, 담당자 1명이 여러 날 실행. **10/13: 도로 · 동 중심을 주소 파일로 계산해 서울 회사 100%에 좌표가 있다(decisions/004, docs/validation.md)** |
| R5 | 중간 | **화면 구조가 SPEC과 다르다.** 지도 메인 + 패널 구조(03 문서)는 SPEC 9장(검색 메인, `/map` 별도)과 다르고, API에도 bbox 같은 필드가 더 필요하다 | 팀장이 채택 여부를 정하고 `docs/decisions/NNN-지도-메인-화면.md`(번호는 기록할 때 다음 번호로)로 기록. 채택하면 SPEC 8 · 9장 수정 PR. **2026-10-12: Phase 6은 검색 메인(decisions/005). 2026-10-13: 지도 메인 채택(decisions/006), `rep_location` 추가** |
| R6 | 해당 없음 | **단일 DB에서 배치 쓰기와 API 읽기를 같이 한다.** 월 1회 대량 `LOAD DATA`와 mart 재계산 동안 API 응답이 느려질 수 있다 | MVP 규모에서는 허용. 적재는 새벽 시간대 cron. p95 300ms 목표는 locust로 적재 중에도 한 번 측정. **실제: 적재는 로컬 DB에서 하고 배포 DB에는 복원 · 업로드만 한다(복원 몇 분 동안은 API 오류 가능, runbook 4장)** |
| R7 | 반영 | **백업이 정해지지 않았다.** Railway 볼륨 하나에 모든 데이터가 있다 | 월 적재 후 `mariadb-dump`를 받아 보관하는 절차를 runbook에 추가. **runbook 5장: 월 갱신 덤프가 곧 백업, 공유 드라이브에 최근 3개(지금 `worth_joining_20261015_v2.zip`)** |

### 설계 문제점 요약 (03~06 문서 전체)

결정이 필요한 순서대로 정리했다.

| 우선 | 항목 | 담당 | 언제까지 | 상태 (2026-10-15) |
|---|---|---|---|---|
| 1 | D1 q2가 사라진 회사 요약을 지우지 않음 | T2 | Phase 3 (10/14) | 완료: refresh_mart가 비운 뒤 다시 넣음 |
| 2 | D2 `nps_rate` 범위 밖 달이 조용히 빠짐 | T1 · T2 | Phase 2 (10/13) | 완료: 품질 검사 `rate_covered` (#16) |
| 3 | A1 정렬과 맞지 않는 커서 | T3 | Phase 4 (10/15) | 완료: 키셋 커서 `[sort, 정렬값, company_id]` |
| 4 | A2 이름 검색이 앞부분 일치뿐 | T3 · T1 | Phase 4 (10/15) | 일부: 입력 정규화 반영, 부분 일치는 미정 |
| 5 | R2 국민연금 파일 자동 수집 가능 여부 | T1 | Phase 1 (10/08) | 결정: 수동 다운로드 → `extract_seoul` → `load`(runbook 4장) |
| 6 | R5 · A4 지도 메인 채택과 API 필드 추가 | 팀장 · T3 · T4 | Phase 8 전 (10/16) | 완료: 지도 메인(decisions/006) |
| 7 | D6 표본 부족 회사를 백분위에서 뺄지 | T2 | Phase 3 (10/14) | 완료: 빼고 백분위 NULL |
| 8 | D4 · D5 · R3 mart 갱신의 삭제 · 트랜잭션 정리 | T2 | Phase 3 (10/14) | 완료: q1 → q2 → q6 → q5 → q5t 한 트랜잭션(Phase 9). `mart_meta`는 만들지 않음 |
| 9 | D7 · A3 역 시세 기간을 6 · 12 · 24로 제한 | T2 · T3 | Phase 9 | 완료: 6 · 12 · 24만(decisions/007). 10/15 반경 500 · 750m 추가(decisions/009) |
| 10 | D3 상호 변경 시 회사 분리 | T1 | MVP 이후 | 미정: 한계로 둔다 |
