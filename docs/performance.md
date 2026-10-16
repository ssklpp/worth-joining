# 성능 기록

| 항목 | 내용 |
|---|---|
| 대상 | T2 · T3. API · SQL을 바꿀 때 이 숫자와 비교한다. 쿼리별 실행 계획은 [explain.md](./explain.md) |
| 기준 | SPEC Phase 11-1, NFR-PERF-01 ~ 04, Task T2-10 |
| 환경 | 로컬: Windows 11, MariaDB 11.4.13, uvicorn 1 프로세스. 데이터: 서울 회사 126,407곳 · 월별 165만 행 · 회사 좌표 126,407 · 역 309 · 전월세 계약 44만 |
| 상태 | 2026-10-13 |

---

## 1. 목표와 결과

| 요구사항 | 목표 | 결과 (로컬 부하 측정 p95) | 판정 |
|---|---|---|---|
| NFR-PERF-01 회사 상세 | p95 300ms 이하 | 8ms | 통과 |
| NFR-PERF-02 검색 | p95 500ms 이하 | `q` 6ms, `sort=growth` 64ms, 지도 핀 270ms | 통과 |
| NFR-PERF-03 요청 시 무거운 집계 없음 | mart만 조회 | 모든 API가 `mart_*` · 작은 조회 조인만 읽는다. 역세권 시세 · 회사 근처 역도 `refresh_mart`에서 미리 만든다 | 통과 |
| NFR-PERF-04 반경 검색은 공간 인덱스 | EXPLAIN에 `ALL` 스캔 없음 | 역-건물 쌍(q5a)이 `Range checked for each record`로 건물 공간 인덱스를 쓴다(테스트로 확인). 회사-역(q6)은 숫자 좌표라 위도 · 경도 범위로 거른다 | 통과(q6는 대체 방법, explain.md 3장) |

## 2. 부하 측정 (locust)

`tests/perf/locustfile.py`, 20명 · 초당 5명씩 늘림 · 60초, 대상 `127.0.0.1:8000`(TS-015). 상세 · 주거비 · 비교 회사는 `sort=growth` 검색 10페이지(500곳)에서 고르고, 지도는 서울 안 약 3km × 2.4km 범위를 무작위로 옮긴다.

| 요청 | 요청 수 | p50 | p95 | p99 | 최대 | 실패 |
|---|---|---|---|---|---|---|
| `/companies/{id}` | 910 | 4ms | 8ms | 14ms | 26ms | 0 |
| `/companies/{id}/trend` | 530 | 4ms | 8ms | 11ms | 17ms | 0 |
| `/companies/{id}/housing` | 366 | 4ms | 9ms | 12ms | 29ms | 0 |
| `/companies?q=` | 571 | 3ms | 6ms | 10ms | 22ms | 0 |
| `/companies?sort=growth` | 178 | 51ms | 64ms | 86ms | 100ms | 0 |
| `/compare?ids=`(3곳) | 198 | 4ms | 8ms | 13ms | 22ms | 0 |
| `/map/companies?bbox=` | 537 | 100ms | 270ms | 320ms | 490ms | 0 |
| `/stations` | 173 | 5ms | 12ms | 22ms | 27ms | 0 |
| 전체 | 3,463 | 4ms | 120ms | 270ms | 490ms | 0 |

### 배포 환경 (참고)

Railway(api · mariadb 사설망), 국내에서 `curl` 한 번씩(새 TLS 연결 포함). 대부분 네트워크 왕복 시간이다.

| 요청 | 시간 |
|---|---|
| `/companies/{id}` | 388ms |
| `/companies/{id}/housing` | 246ms |
| `/map/companies?bbox=` | 489ms |
| `/stations` | 276ms |

배포 환경에 부하를 걸지는 않았다(무료 · 체험 요금제의 다른 서비스에 영향을 주지 않기 위해).

## 3. 개선 전후

| 대상 | 문제 | 바꾼 것 | 전 | 후 | 기록 |
|---|---|---|---|---|---|
| 검색 `sort=name` | summary 12만 행을 조인 후 이름 정렬 | `company STRAIGHT_JOIN summary`로 이름 인덱스 순서대로 읽고 LIMIT에서 멈춤 | 372ms | 2ms | explain.md 2장 |
| 비교 `/compare` 기준월 | `MAX(snapshot_ym)`이 월별 165만 행 스캔 | summary의 `latest_ym` 한 행 | 275 ~ 378ms | 9ms | explain.md 2장 |
| 지도 핀 `ungeocoded_count` | 지도를 옮길 때마다 summary 전체를 셈 | 업종 · 지역별로 10분 기억(`app/repositories/map_pins.py`) | 부하 p50 230 · p95 430ms | p50 100 · p95 270ms | 이 문서 |
| q5 역세권 시세 | 윈도 함수 안 공간 조인이 공간 인덱스를 안 씀 | 역-건물 쌍을 먼저 만듦(q5a) | 기간 하나 150 ~ 320초 | 0.9초 | explain.md 3장, TS-025 |
| q6 회사 근처 역 | 숫자 좌표에 회사마다 버퍼 계산 | 역을 바깥에 두고 위도 · 경도 범위로 거름 | 284초 | 5.6초 | explain.md 3장, TS-025 |
| `refresh_mart` 전체 | 위 두 가지 | | 5분 이상 | 35초 | explain.md 1 · 3장 |
| 회사 좌표 3 · 4단계 | 표본 건물 좌표 API 2.6만 회(분당 약 95회) | 주소정보누리집 출입구 파일로 계산 | 약 4.5시간 예상 | 16초 | validation.md 1장 |
| 전월세 건물 좌표 | 지번 → 검색 → 좌표 API | 지번 → 도로명주소 파일 → 출입구 좌표, 부속 지번만 검색 | 약 5시간 예상 | 수 분(부속 지번 검색 약 1,200회, 실패 캐시를 지우고 한 번 더 돌린 것 포함) | validation.md 2장 |
| 웹 첫 화면 글꼴(2026-10-16, #92) | `next/font`가 한글 글꼴 조각 280개(굵기 4종)를 모두 `<link rel=preload>`로 받음. 배포 HTML 77KB의 대부분이 이 링크 | `preload: false`로 화면에 쓰인 글자 조각만 받음 | Lighthouse(모바일 · 느린 4G) 첫 화면 65점 · LCP 20.6초 · 전송 4.0MB, 상세 53점 · LCP 16.9초 · CLS 0.231 | 첫 화면 67 ~ 72점 · LCP 8.2초 · 1.5MB, 상세 81점 · LCP 4.8초 · CLS 0 ~ 0.001. 글꼴 2.6MB → 234 ~ 334KB | 이 문서 |

## 4. 개선 여지 (지금은 하지 않음)

| 조건 | 방법 |
|---|---|
| 지도 핀이 더 느려짐(지금 단독 39ms, summary `ALL` + filesort) | `company_location`에 `(lat, lon)` 인덱스를 두고 bbox가 있으면 좌표 범위부터 읽기 |
| `sort=growth` 전체 조회(51ms) | summary에 `(growth_12m, company_id)` 인덱스(explain.md 2장) |
| 배포 응답의 네트워크 시간(2026-10-16: 운영 API 모든 응답 약 250ms, 그중 약 140ms가 Railway 엣지 → 앱 구간. 로컬 서버 처리는 2 ~ 60ms) | Railway 리전을 사용자와 가까운 곳으로, 또는 Vercel에서 서버 쪽 캐시 |
| 첫 화면 LCP 8초(가장 큰 요소가 네이버 지도 타일 이미지) | 지도 · API 미리 연결(`preconnect`)은 넣었다. 그 이상은 지도 SDK 쪽이라 어렵다 |
