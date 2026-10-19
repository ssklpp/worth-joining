-- 회사 요약 · 업종 백분위 (SPEC 7장 q2).
-- refresh_mart가 mart_company_summary를 비운 뒤 같은 트랜잭션에서 실행한다. 그래서 최신 월에 없는
-- 회사는 행이 남지 않는다(docs/04 D1, REPLACE 대신 INSERT).
-- 백분위: 서울 · 성남 사업장 중 대표 업종 안에서. 지표가 NULL이거나 표본 부족(가입자 10명 미만)인 회사,
-- 업종 분류가 없는 회사(999999, 원본의 "BIZ_NO미존재사업장". 서로 다른 업종이 섞여 있다)는
-- 별도 파티션으로 빼서 분포에 넣지 않고 백분위를 NULL로 둔다(docs/04 D6, docs/08 I-01).
INSERT INTO mart_company_summary
  (company_id, industry_code, region_code, rep_addr_key, workplace_count, latest_ym, members,
   growth_12m, quit_rate_12m, avg_salary_est, pct_growth, pct_stability, pct_salary,
   small_sample, short_history)
SELECT company_id, industry_code, region_code, rep_addr_key, workplace_count, latest_ym, members,
       growth_12m, quit_rate_12m, avg_salary_est,
       CASE WHEN growth_12m IS NOT NULL AND NOT excluded THEN ROUND(100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, growth_12m IS NULL OR excluded ORDER BY growth_12m)) END,
       CASE WHEN quit_rate_12m IS NOT NULL AND NOT excluded THEN ROUND(100 - 100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, quit_rate_12m IS NULL OR excluded ORDER BY quit_rate_12m)) END,
       CASE WHEN avg_salary_est IS NOT NULL AND NOT excluded THEN ROUND(100 * PERCENT_RANK() OVER (
            PARTITION BY industry_code, avg_salary_est IS NULL OR excluded ORDER BY avg_salary_est)) END,
       small,
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
  cur_wp AS (   -- 최신 월에 존재하는 사업장. 대표 사업장 = 최신 월 가입자 최대(동률은 workplace_id 작은 쪽)
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
         w.avg_salary_est,
         w.members < 10 AS small,
         w.members < 10 OR r.industry_code = '999999' AS excluded   -- 백분위에서 뺄 회사
  FROM win w JOIN cur_wp r ON r.company_id = w.company_id AND r.rn = 1
  -- 최신 월에 없는 회사(최근 자료 없음)와 최신 월 가입자가 0명인 회사(이번 달 전부 탈퇴, 0명 등록)는
  -- summary에 넣지 않는다. API는 이들을 stale로 보여 준다. 월별 이력(q1)에는 남는다.
  WHERE w.members > 0
) s
