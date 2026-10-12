-- 비교 지수: 12개월 전 = 100 (SPEC 7장 q_compare, Phase 8-6)
-- ids 파라미터는 회사 ID 목록(최대 3, expanding)이다. 주석에는 콜론 + 이름을 쓰지 않는다(TS-020).
-- 12개월 전 자료가 없거나 0명이면 idx는 NULL이고 API가 short_history flag를 붙인다.
-- 기준월은 summary의 latest_ym(refresh_mart가 같은 값으로 채움)에서 읽는다. MAX(snapshot_ym)은 165만 행을 훑는다
WITH latest AS (SELECT latest_ym AS ym FROM mart_company_summary LIMIT 1),
base AS (
  SELECT m.company_id, m.members AS base_members
  FROM mart_company_monthly m JOIN latest l ON m.snapshot_ym = PERIOD_ADD(l.ym, -12)
  WHERE m.company_id IN :ids
)
SELECT m.company_id, m.snapshot_ym AS ym, m.members,
       ROUND(100 * m.members / NULLIF(b.base_members, 0), 1) AS idx
FROM mart_company_monthly m
JOIN latest l ON m.snapshot_ym >= PERIOD_ADD(l.ym, -12)
LEFT JOIN base b ON b.company_id = m.company_id
WHERE m.company_id IN :ids
ORDER BY m.company_id, m.snapshot_ym
