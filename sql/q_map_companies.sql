-- 지도 핀 (SPEC 7장 q_map_companies, Phase 8-5). 가입자 많은 순 최대 200곳.
-- 201번째 행이 있으면 API가 truncated를 켠다. 필터는 모두 선택이며 NULL이면 걸지 않는다.
-- region은 시도 2자리 또는 시군구 5자리 접두어, bbox는 경도 · 위도 범위(docs/05 3장).
-- 주석에는 콜론 + 이름을 쓰지 않는다(TS-020).
SELECT s.company_id, c.display_name AS name, s.members, s.growth_12m, s.quit_rate_12m,
       s.avg_salary_est, l.lon, l.lat, l.accuracy, l.basis
FROM mart_company_summary s
JOIN company c          ON c.company_id = s.company_id
JOIN company_location l ON l.company_id = s.company_id
WHERE (:industry IS NULL OR s.industry_code = :industry)
  AND (:region IS NULL OR s.region_code LIKE CONCAT(:region, '%'))
  AND (:min_lon IS NULL OR l.lon BETWEEN :min_lon AND :max_lon)
  AND (:min_lat IS NULL OR l.lat BETWEEN :min_lat AND :max_lat)
ORDER BY s.members DESC, s.company_id
LIMIT 201
