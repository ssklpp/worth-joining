# EXPLAIN 기록

| 항목 | 내용 |
|---|---|
| 대상 | T2 · T3. SQL을 바꾸거나 인덱스를 추가할 때 이 기록과 비교한다 |
| 기준 | SPEC Phase 3-5, T2-07. **MariaDB 11.4 결과를 기준으로 삼는다**(비용 기반 옵티마이저라 10.11과 계획이 다를 수 있다) |
| 환경 | 로컬 MariaDB 11.4.13, 서울 13개월(2025-08 ~ 2026-08). `workplace_monthly` 165만 행, `workplace` 17만 행 |
| 상태 | 1차 · 2026-10-12. mart 갱신 SQL만. 검색 · 상세 API 조회는 T2-07에서 추가 |

---

## 1. mart 갱신 (`python -m pipeline.refresh_mart`)

| 단계 | 결과 행 | DELETE | INSERT … SELECT |
|---|---|---|---|
| q1 `mart_company_monthly` | 1,650,181 | 3.0초 | 16.7초 |
| q2 `mart_company_summary` | 126,408 | 0.6초 | 4.8초 |
| 전체 (한 트랜잭션, `ingestion_log` 기록 포함) | | | 약 23초 |

월 1회 배치라 이 시간이면 충분하다. 행이 늘어 1분을 넘기면 아래 "개선 여지"를 본다.

### q1 `sql/q1_company_monthly.sql`

```
id | select_type | table      | type  | key     | rows    | Extra
1  | PRIMARY     | r(nps_rate)| ALL   |         | 4       |
1  | PRIMARY     | <derived3> | ALL   |         | 169713  | Using where; Using join buffer (flat, BNL join)
3  | DERIVED     | <derived2> | ALL   |         | 169713  | Using temporary
2  | DERIVED     | w          | index | uk_wp   | 169713  | Using index; Using temporary; Using filesort
2  | DERIVED     | m          | ref   | PRIMARY | 1       |
```

- `workplace`를 커버링 인덱스(`uk_wp`)로 훑고 `workplace_monthly`를 PK로 찾는다. 회사 × 월 집계(`agg`) → `LAG` 윈도(`with_prev`) 순서로 임시 테이블을 만든다.
- `nps_rate`(4행)와의 기간 조인은 BNL 조인이지만 기준표가 작아 문제없다.

### q2 `sql/q2_company_summary.sql`

```
id | select_type | table                | type | key     | rows    | Extra
1  | PRIMARY     | <derived4>(cur_wp)   | ALL  |         | 1697134 | Using where; Using temporary
1  | PRIMARY     | <derived3>(win)      | ref  | key0    | 27      | Using where
3  | DERIVED     | <derived2>(latest)   | ALL  |         | 1644064 | Using temporary; Using filesort
3  | DERIVED     | m(mart_company_monthly) | ALL |       | 1644064 | Using where; Using join buffer (flat, BNL join)
2  | DERIVED     | mart_company_monthly | ALL  |         | 1644064 |
4  | DERIVED     | w(workplace)         | ALL  |         | 169713  | Using temporary
4  | DERIVED     | m(workplace_monthly) | ref  | PRIMARY | 1       |
4  | DERIVED     | <derived7>(latest)   | ref  | key0    | 10      |
7  | DERIVED     | mart_company_monthly | ALL  |         | 1644064 |
```

- `latest`(`MAX(snapshot_ym)`)가 `mart_company_monthly`를 두 번 전체 스캔한다. PK가 `(company_id, snapshot_ym)`이라 월 단독 조건에는 인덱스를 못 쓴다.
- `win`의 `WHERE snapshot_ym >= 최신월 - 12`도 같은 이유로 전체 스캔이다. 지금은 13개월이 전부라 걸러지는 행이 거의 없어 손해가 없다.
- 대표 사업장(`cur_wp`)은 `ROW_NUMBER()`로 회사별 1위를 고른 뒤 `win`과 자동 생성 키(`key0`)로 조인한다.

### 개선 여지 (지금은 하지 않음)

| 조건 | 방법 |
|---|---|
| 보관 기간이 13개월보다 길어져 q2가 느려짐 | `mart_company_monthly`에 `KEY ix_ym (snapshot_ym)`. `latest`와 `win`의 월 조건이 범위 스캔이 된다 |
| q1이 1분을 넘김 | 전체 재계산 대신 최근 2개월만 지우고 다시 넣기(전월 비율 계산에 직전 달이 필요) |

## 2. 검색 · 상세 API 조회

MariaDB 11.4.13 로컬, 서울 13개월 실데이터(`mart_company_summary` 126,408행, `mart_company_monthly` 1,650,181행, `company` 159,048행). 시간은 같은 쿼리 3회 중 최솟값, SQL은 `app/repositories/`.

| 쿼리 | 실행 계획(구동 테이블) | 시간 |
|---|---|---|
| 검색 `sort=name` | `company` `index` `ix_name_prefix` → summary `eq_ref` | 0ms |
| 검색 `sort=name` + `q` | `company` `range` `ix_name_prefix`(Using index condition) | 0ms |
| 검색 `sort=name` + `q` + 커서 | 같음, 커서 조건도 range 안에서 처리 | 0ms |
| 검색 `sort=name` + `region` | `company` `index` 순서로 읽고 summary에서 거름 | 1ms |
| 검색 `biz_no6` | `company` `ref` `uk_company` + filesort(최대 수백 행) | 0ms |
| 검색 `sort=growth` | summary `ALL` + filesort(124,449행) | 45ms |
| 검색 `sort=growth` + `industry` | summary `ref` `ix_ind_region` + filesort | 8ms |
| 상세(summary + 대표 형태) | 모두 `const`, `workplace` `ref` `uk_wp` | 0ms |
| stale `last_seen_ym` · 추이 | `mart_company_monthly` PK `(company_id, snapshot_ym)` | 0ms |
| 업종 목록 | `industry` `ALL`(1,428행) + summary `ix_ind_salary` 커버링 | 23ms |
| 업종 분포(salary · quit) | summary `ref` `ix_ind_region` + 임시 테이블 | 7ms |
| `/meta/methodology` 시작월 `MIN(snapshot_ym)` | `mart_company_monthly` `ALL`(165만 행) | 133ms |
| 비교 `/compare`(3곳, `sql/q_compare.sql`) | `mart_company_monthly` PK `range` · `ref`, 기준월은 summary `LIMIT 1` | 9ms (기준월을 `MAX(snapshot_ym)`으로 구하면 275 ~ 378ms) |

### name 정렬 조인 순서 고정

처음에는 모든 검색이 `mart_company_summary`부터 읽었다. `sort=name`(필터 없음)은 summary 12만 행을 모두 조인한 뒤 `name_norm`으로 정렬해 **372ms**였다(목표 300ms 초과). `FROM company c STRAIGHT_JOIN mart_company_summary s`로 순서를 고정하면 `ix_name_prefix(name_norm)` 인덱스 순서(InnoDB 보조 인덱스는 PK `company_id`를 포함하므로 `(name_norm, company_id)` 순서)대로 읽다가 LIMIT에서 멈춰 **2ms**가 된다. 동점 키도 `c.company_id`로 맞췄다. 거의 없는 업종으로 거르면 company 인덱스를 끝까지 읽을 수 있지만 최악이 약 20ms였다.

### 부하 측정 (locust, `tests/perf/locustfile.py`)

uvicorn 1 프로세스, 20명, 60초, 대상 `127.0.0.1:8000`. 상세 ID는 `sort=growth` 검색 10페이지(500개)에서 고른다.

| 요청 | 요청 수 | p50 | p95 | p99 | 최대 |
|---|---|---|---|---|---|
| `/companies/{id}` | 1,542 | 3ms | **6ms** | 17ms | 38ms |
| `/companies/{id}/trend` | 913 | 3ms | 7ms | 21ms | 33ms |
| `/companies?q=` | 925 | 3ms | 6ms | 19ms | 32ms |
| `/companies?sort=growth` | 291 | 48ms | 54ms | 66ms | 75ms |

실패 0건. 상세 p95 300ms 이하(SPEC Phase 4, NFR-PERF-01)와 검색 p95 500ms 이하(NFR-PERF-02)를 만족한다. `localhost`로 측정하면 최대가 약 2초로 튄다(TS-015).

### 개선 여지 (지금은 하지 않음)

| 조건 | 방법 |
|---|---|
| `sort=growth` 전체 조회가 느려짐(현재 45ms) | summary에 `KEY ix_growth (growth_12m, company_id)`. NULL을 맨 뒤로 보내는 `COALESCE` 식 대신 생성 컬럼으로 정렬 |
| `/meta/methodology`가 자주 호출됨 | 시작월을 `mart_company_summary`에 함께 두거나 응답 캐시 |
