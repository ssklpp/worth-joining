# 10. 배포

| 항목 | 내용 |
|---|---|
| 대상 | 팀 전원 · 평가자. 지금 배포된 서비스가 무엇이고, 어떻게 배포 · 확인 · 되돌리는지 |
| 기준일 | 2026-10-21, `main`(#122 병합 뒤), 릴리스 `v1.4.0` |
| 절차 | 처음부터 다시 배포하는 절차 · 월 갱신 · 복원은 [runbook.md](./runbook.md). 이 문서는 현재 상태와 최종 확인 결과를 정리한다 |
| 관련 | [06_architecture.md](./06_architecture.md) 4장(배포 구성), [05_api_spec.md](./05_api_spec.md)(API 계약), [09_test_result.md](./09_test_result.md)(테스트 결과) |

---

## 1. 배포 현황

| 항목 | 값 |
|---|---|
| 웹 | https://web-chi-flax-46.vercel.app |
| API | https://api-production-30254.up.railway.app |
| API 문서 | https://api-production-30254.up.railway.app/docs (Swagger UI, `openapi.json` 버전 1.4.0) |
| 버전 | 릴리스 `v1.4.0`(2026-10-19). `app/main.py` · `pyproject.toml` · `web/package.json` 모두 1.4.0 |
| 데이터 기준월 | 국민연금 2026-08(13개월, 2025-08 ~), 전월세 2026-08(2024-09 ~) |
| 데이터 범위 | 서울 · 성남 회사 137,129곳, 역 326곳, 역세권 시세(반경 500 · 750m × 6 · 12 · 24개월) |
| 배포 DB 스키마 | Alembic `0011`(코드의 head와 같음) |
| 호스팅 | Vercel(웹), Railway us-west(API · MariaDB 11.4, Hobby 요금제) |
| 기준 덤프 | 팀 공유 드라이브 `worth_joining_20261019_v6.zip`(Alembic 0011). 복원하면 배포 DB가 읽는 표와 같은 상태 |

## 2. 구성

```
           ┌──────────── 로컬 (월 1회, 사람이 확인) ────────────┐
공공데이터 ─▶ pipeline/ (적재 · 품질 검사) ─▶ 로컬 MariaDB (raw → core → mart)
                                                     │ 덤프 · 필요한 표만 (TCP Proxy를 켤 때만)
                                                     ▼
브라우저 ──HTTPS──▶ Vercel  web (Next.js 15)          Railway mariadb (mariadb:11.4 + 볼륨)
    │                                                   ▲ 사설망 mariadb.railway.internal:3306
    └──────HTTPS GET (CORS)──▶ Railway api (FastAPI, Dockerfile) ┘
```

| 서비스 | 플랫폼 | 빌드 · 실행 | 배포 계기 |
|---|---|---|---|
| web | Vercel, Root Directory `web` | `next build` | `main`에 병합되면 자동 배포. PR마다 Preview 배포 |
| api | Railway, GitHub 저장소 연결 | `Dockerfile`(python:3.12-slim, uvicorn 1개 프로세스), 헬스 체크 `/health`(`railway.json`) | `main`의 `app/**` · `pipeline/**` · `pyproject.toml` · `Dockerfile`이 바뀌면 자동 배포(`watchPatterns`) |
| mariadb | Railway, Docker Image `mariadb:11.4` | 볼륨 `/var/lib/mysql` | 데이터는 로컬에서 만든 덤프 · 표를 복원할 때만 바뀐다 |

- API는 읽기 전용이다. 배포 DB에 쓰는 일은 데이터 복원과 마이그레이션 적용뿐이고, 둘 다 로컬에서 TCP Proxy를 잠깐 켜고 한다.
- 배포 DB에는 API가 읽는 mart · 역 · 조회 표만 있다. 전월세 raw · 계약 · 건물 같은 큰 표는 로컬에만 둔다(runbook 4장).
- Railway에서 적재 cron은 돌리지 않는다. 국민연금 월 파일을 자동으로 받을 수 없어 로컬에서 적재 · 검사한 뒤 결과만 올린다(runbook 6장, 08 문서 I-19).

## 3. 배포 흐름

| 바뀌는 것 | 흐름 | 확인 |
|---|---|---|
| 코드 | 브랜치 → PR → CI 3작업(`test` 필수 · `web` · `api-image`) → 리뷰 → Squash and merge → Vercel · Railway 자동 배포 | `main` CI 성공, `/health` `ok`, 웹 하단 기준월 |
| 스키마 | 마이그레이션 PR 병합 → 로컬에서 `DATABASE_URL_SYNC`를 TCP Proxy 주소로 바꿔 `alembic upgrade <목표 버전>`(TS-024) → 프록시 끄기 | `SELECT version_num FROM alembic_version` = `alembic heads` |
| 데이터 | 로컬 적재 · 품질 검사 → `refresh_mart` → 덤프(전체) 또는 표만 `mariadb-dump` → TCP Proxy로 넣기 → 프록시 끄기 → 공유 드라이브에 덤프 | `/health`의 `latest_nps_ym`, 회사 몇 곳의 값. 화면은 응답 캐시로 최대 1시간 늦게 바뀐다 |

CI 작업(`.github/workflows/ci.yml`):

| 작업 | 하는 일 | `main` 필수 검사 |
|---|---|---|
| `test` | ruff, MariaDB 11.4 컨테이너에서 pytest 234개(단위 · SQL 회귀 · API) | 예 |
| `web` | ESLint, 타입 검사, API 타입이 백엔드 `openapi.json`과 같은지, 빌드, 화면 smoke 8개(저장된 API 응답, CSP 위반 검사) | 아니오 |
| `api-image` | `Dockerfile` 빌드, DB 연결 없이 앱을 불러올 수 있는지 | 아니오 |

## 4. 환경 변수와 비밀

값은 Railway · Vercel 설정에만 있고 저장소와 문서에는 없다. 전체 목록과 넣는 법은 [runbook.md](./runbook.md) 3장.

| 서비스 | 변수 | 비밀 |
|---|---|---|
| mariadb | `MARIADB_ROOT_PASSWORD`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`, `MARIADB_USER` | 비밀번호 2개 |
| api | `DATABASE_URL`, `DATABASE_URL_SYNC`(Railway 참조 변수로 mariadb 값을 가져옴), `DB_SSL_VERIFY=false`, `CORS_ORIGINS`, `PORT` | DB 주소 2개 |
| web | `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_NAVER_MAP_CLIENT_ID` | 없음(공개 값) |

- 공공데이터 API 키(OpenDART · 공공데이터포털 · 주소정보누리집)는 배포 서비스에 넣지 않는다. 수집은 로컬에서만 한다.
- 네이버 지도는 Client ID만 쓰고, NCP 콘솔에 등록한 도메인(웹 주소 · localhost)에서만 동작한다. Client Secret은 쓰지 않는다.

## 5. 보안 설정

| 항목 | 설정 | 2026-10-21 확인 |
|---|---|---|
| 웹 보안 헤더 | CSP(허용 목록 밖 스크립트 · 연결 차단), HSTS, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`(`web/next.config.ts`) | 배포 응답 헤더에 모두 있음 |
| CORS | 웹 도메인 · localhost의 GET만 | `CORS_ORIGINS` |
| 입력 검증 | 길이 · 범위 · 허용 값 밖이면 422, 없는 id는 404 | 아래 6장 26개 점검에 포함 |
| SQL | 값은 모두 바인딩 파라미터, 정렬 열은 정해 둔 목록에서만 | 코드 리뷰(09 문서 7장) |
| DB | 사설망으로만 연결, 공개 포트 없음(복원할 때만 TCP Proxy를 켰다 끔) | Railway Networking에서 TCP Proxy 꺼짐 |
| 비밀 | `.env`는 `.gitignore`, 배포 비밀은 플랫폼 변수에만 | 저장소에 키 없음 |

## 6. 최종 기능 확인 (2026-10-21)

### 6.1 배포 API 자동 점검

국내에서 배포 API에 26개 요청을 한 번씩 보냈다(새 TLS 연결 포함). **26 / 26 통과**, 응답 시간 중앙값 약 0.24초(대부분 미국 서부 왕복, 08 문서 I-15).

| 묶음 | 요청 | 기대 | 결과 |
|---|---|---|---|
| 상태 | `/health` | 200, `db: ok`, `latest_nps_ym: 202608`, `latest_rent_ym: 202608`, `match_rate: 0.7926`, `geocode_success_rate: 1.0` | 통과 |
| 검색 | 이름 · 사업자번호 6자리 · 성장순, 너무 긴 `q` · 범위 밖 `limit` | 200 · 200 · 200, 422 · 422 | 통과 |
| 회사 | 상세(서울 · 성남) · 없는 회사, 추이, 재무, 주거비 · 기간 오류 | 200 · 200 · 404, 200, 200, 200 · 422 | 통과 |
| 업종 | 목록, 분포 | 200, 200 | 통과 |
| 비교 | 3곳, 4곳 | 200, 422 | 통과 |
| 지도 | 서울 · 성남 범위 핀 | 200 | 통과 |
| 역 | 목록, 시세 500m · 750m, 반경 오류, 원룸 없는 역, 없는 역 | 200, 200 · 200, 422, 200, 404 | 통과 |
| 계산 방법 | `/meta/methodology` | 200(약 0.22초, 0011 월 인덱스 뒤) | 통과 |

### 6.2 웹 · 배포 상태

| 항목 | 결과 |
|---|---|
| 웹 주요 주소 `/` · `/companies/183674` · `/compare` · `/stations/317` · `/methodology` | 모두 200 |
| 없는 주소 `/no-such-page` | 404(한국어 안내 화면) |
| `main` 최신 커밋(#122) CI | 성공 |
| 화면 흐름(검색 → 상세 → 채용 바로가기, 비교, 역 시세 · 반경, 성남) | CI 화면 smoke 8개 통과, 시연 순서 [demo.md](./demo.md) 2장 |
| 업종 분류 없는 회사(우아한형제들) | 업종 비교 판정 없이 "업종 분류가 없어 비교하지 않았습니다"(I-01 해결 반영) |
| 배포 DB 스키마 | `0011` = 코드 head |

### 6.3 배포 승인 점검표

발표 전에 아래가 모두 맞으면 현재 배포본(`v1.4.0`)을 최종본으로 한다.

- [x] `main` CI 성공, 열린 PR 없음
- [x] 배포 API 26 / 26 통과, `/health` 기준월 2026-08
- [x] 배포 DB 스키마 `0011` = 코드 head, 배포 DB가 덤프 v6과 같은 상태
- [x] 웹 보안 헤더 · 404 화면 확인
- [x] Railway TCP Proxy 꺼짐
- [ ] 시연용 시크릿 창에서 [demo.md](./demo.md) 2장 순서를 처음부터 끝까지 한 번 따라 함
- [ ] 비상용 녹화 영상 · 슬라이드 PDF 준비(demo.md 1장)

## 7. 릴리스 이력

| 태그 | 날짜 | 내용 |
|---|---|---|
| `v1.0.0` | 2026-10-15 | 첫 정식 버전: 회사 검색 · 상세 · 추이 · DART 재무, 지도 메인 + 패널, 회사 비교, 역세권 시세 · 회사 근처 주거비, 역 시세 · 비교 |
| `v1.1.0` | 2026-10-15 | 역세권 반경 500m · 750m(decisions/009) |
| `v1.2.0` | 2026-10-16 | 성남시 회사 추가(decisions/010), 화면 테스트 · CSP · 글꼴 개선 |
| `v1.3.0` | 2026-10-16 | 성남 역 18곳 · 전월세 시세, 시도별 전환율(0010) |
| `v1.4.0` | 2026-10-19 | 목록 10 · 20곳씩 · 상태 유지, 원룸 없는 역 안내, 업종 분류 없는 회사 업종 비교 제외(I-01), 월 인덱스(0011, I-02), 마곡 · 이촌 역 좌표 수정 |

데이터 덤프 이력(공유 드라이브): v2(성남 전) → v3(성남 회사) → v4(성남 역 · 전월세) → v5(역 좌표 수정, TS-033) → **v6(업종 백분위 수정 · 0011, TS-034)**. 되돌릴 때 쓰도록 v2와 v6을 보관한다.

## 8. API 문서

자세한 계약은 [05_api_spec.md](./05_api_spec.md) 2장과 배포 API의 `/docs`. 모든 엔드포인트는 GET이고 읽기 전용이다.

| 엔드포인트 | 하는 일 | 주요 파라미터 |
|---|---|---|
| `/health` | DB 상태, 기준월, 매칭률 · 좌표 성공률 | — |
| `/companies` | 회사 검색(키셋 커서) | `q`, `biz_no6`, `industry`, `region`, `sort`, `limit`, `cursor` |
| `/companies/{id}` | 회사 상세: 기본 정보 · 지표 · 업종 백분위 · flags · 대표 위치 | — |
| `/companies/{id}/trend` | 월별 가입 · 입퇴사 · 비율 · 추정 연봉 | `from_ym`, `to_ym` |
| `/companies/{id}/financials` | DART 연도별 재무 | `years` |
| `/companies/{id}/housing` | 회사 근처 역(1km, 최대 3곳)의 원룸 시세 · 월급 대비 부담률 | `months`(6 · 12 · 24) |
| `/industries`, `/industries/{code}/distribution` | 업종 목록, 업종 안 지표 분포 | `q`, `metric` |
| `/compare` | 회사 1 ~ 3곳 요약 지표 · 가입자 지수 | `ids` |
| `/map/companies` | 지도 범위 안 회사 핀(최대 200곳) | `bbox`, `metric`, `industry`, `region` |
| `/stations`, `/stations/{id}/rent` | 역 목록, 역세권 시세 · 24개월 추이 | `q`, `months`, `radius`(500 · 750) |
| `/meta/methodology` | 계산식 · 한계 · 기준월 · 출처 | — |

공통 규칙:
- 모든 응답에 기준월 `as_of`가 있다.
- 추정치가 들어간 응답에는 `flags`(`small_sample`, `short_history`, `salary_is_lower_bound`, `approx_location`, `name_matched`, `stale`, `period_extended_to_24m`)가 있다.
- 잘못된 입력은 422, 없는 id는 404를 돌려준다.
- 성공한 GET 응답(`/health` 제외)에는 `Cache-Control: public, max-age=3600`과 ETag가 붙고, 같은 ETag로 다시 요청하면 304를 돌려준다.

## 9. 운영 · 비용 · 발표 뒤

| 항목 | 내용 |
|---|---|
| 비용 | Railway Hobby(월 $5, 사용량 $5 포함). 2026-10-19 기준 사용량의 88%가 mariadb 메모리(평균 약 0.43GB), 하루 약 $0.17. 11/7까지 켜 두면 약 $2 초과 청구가 예상된다. Vercel은 무료 요금제 |
| 발표 뒤 | 계속 공개할 필요가 없으면 Railway api · mariadb를 정지하거나 Serverless(App Sleeping)로 바꾼다. 다시 열 때는 덤프 v6으로 복원한다(runbook 2.2) |
| 월 갱신 | 2026-11 둘째 주에 2026-09 국민연금 자료를 확인하고 runbook 4장 절차로 갱신 |
| 백업 | 월 갱신 때 만든 덤프가 백업. 공유 드라이브에 최근 덤프를 둔다(runbook 5장) |

## 10. 되돌리기

| 문제 | 되돌리는 법 |
|---|---|
| 새 웹 배포가 잘못됨 | Vercel Deployments에서 이전 배포를 Promote to Production |
| 새 API 배포가 잘못됨 | Railway api의 Deployments에서 이전 배포를 Redeploy. 또는 문제 PR을 되돌리는 PR을 병합 |
| 데이터가 잘못 올라감 | 직전 덤프(v6)를 runbook 2.2대로 복원. 일부 표만 올렸다면 그 표만 로컬 main 기준으로 다시 올린다(09 문서 8장: 2026-10-19 한 번 바로잡은 기록) |
| 스키마가 코드보다 낮아 특정 API만 500 | `alembic upgrade <목표 버전>`을 배포 DB에 적용(runbook 4장 5단계) |
| 그 밖의 장애 | [runbook.md](./runbook.md) 7장, 발표 중이면 [demo.md](./demo.md) 3장 비상 계획 |
