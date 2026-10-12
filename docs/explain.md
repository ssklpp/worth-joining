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

T2-07(검색 · 상세 인덱스)에서 실제 API 쿼리로 채운다.
