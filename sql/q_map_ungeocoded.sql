-- 지도 필터(업종 · 지역)에 맞지만 좌표가 없어 지도에 빠진 회사 수(docs/05 3장 ungeocoded_count).
-- bbox는 좌표가 있어야 걸 수 있으므로 여기서는 쓰지 않는다.
SELECT COUNT(*)
FROM mart_company_summary s
LEFT JOIN company_location l ON l.company_id = s.company_id
WHERE l.company_id IS NULL
  AND (:industry IS NULL OR s.industry_code = :industry)
  AND (:region IS NULL OR s.region_code LIKE CONCAT(:region, '%'))
