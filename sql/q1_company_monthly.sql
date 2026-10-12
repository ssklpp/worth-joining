-- 회사 × 월 지표 (SPEC 7장 q1). refresh_mart가 mart_company_monthly를 비운 뒤 같은 트랜잭션에서 실행한다(docs/04 D4).
-- 직전 달 자료가 없으면 비율은 NULL (LAG만 믿지 않고 prev_ym = PERIOD_ADD(snapshot_ym, -1) 확인).
-- 추정 연봉 = 고지금액 ÷ 가입자 ÷ 보험료율 × 12 (소득 상한 때문에 하한 추정치).
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
