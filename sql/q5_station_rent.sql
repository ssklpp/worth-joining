-- 역세권 원룸 시세 (SPEC 7장 q5, decisions/007 · 009). 반경 하나 · 기간 하나를 한 번에 넣는다.
-- refresh_mart가 mart_station_rent를 비운 뒤 반경 500 · 750m × 6 · 12 · 24개월로 여섯 번 실행한다.
-- 기간은 기준월 이하이고 기준월 - N개월보다 뒤(>, >= 아님)인 계약. 기준월은 신고가 끝난 달이다.
-- 원룸은 전용 33㎡ 이하 연립다세대 · 오피스텔, 역세권은 역에서 반경(radius) 이내 건물이다.
-- 역-건물 쌍과 거리는 q5a_station_building.sql이 임시 테이블 station_building에 먼저 넣는다.
-- 환산 월세(원) = (월세 + 보증금 × 전환율 ÷ 12) × 10000. 전환율은 계약 달 값이고,
-- 발표 전이라 없으면 가장 가까운 이전 달 값을 쓴다(docs/profiling.md 13장).
-- 월세는 monthly_man > 0, 전세는 monthly_man = 0. PERCENTILE_CONT는 윈도 함수라 DISTINCT와 쓴다.
-- 주석에는 콜론 + 이름을 쓰지 않는다(TS-020).
INSERT INTO mart_station_rent
  (station_id, period_end_ym, radius_m, window_months, n_monthly, n_jeonse,
   monthly_p25, monthly_median, monthly_p75, deposit_median_man, rent_median_man,
   jeonse_p25_man, jeonse_median_man, jeonse_p75_man)
SELECT s.station_id, :end_ym, :radius, :n,
       COALESCE(m.n, 0), COALESCE(j.n, 0),
       ROUND(m.p25), ROUND(m.p50), ROUND(m.p75), ROUND(m.deposit_p50), ROUND(m.rent_p50),
       ROUND(j.p25), ROUND(j.p50), ROUND(j.p75)
FROM station s
LEFT JOIN (
  WITH near AS (
    SELECT st.station_id, r.deposit_man, r.monthly_man,
           (r.monthly_man + r.deposit_man * (
              SELECT cr.rate_year FROM conversion_rate cr
              WHERE cr.ym <= r.contract_ym ORDER BY cr.ym DESC LIMIT 1) / 12) * 10000 AS conv_rent
    FROM station_building st
    JOIN rent_contract r ON r.building_id = st.building_id
    WHERE st.dist_m <= :radius
      AND r.contract_ym <= :end_ym
      AND r.contract_ym > PERIOD_ADD(:end_ym, 0 - :n)
      AND r.area_m2 <= 33
      AND r.monthly_man > 0
  )
  SELECT DISTINCT station_id,
         COUNT(*) OVER (PARTITION BY station_id) AS n,
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY conv_rent) OVER (PARTITION BY station_id) AS p25,
         PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY conv_rent) OVER (PARTITION BY station_id) AS p50,
         PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY conv_rent) OVER (PARTITION BY station_id) AS p75,
         PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY deposit_man) OVER (PARTITION BY station_id)
           AS deposit_p50,
         PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY monthly_man) OVER (PARTITION BY station_id)
           AS rent_p50
  FROM near
) m ON m.station_id = s.station_id
LEFT JOIN (
  WITH near AS (
    SELECT st.station_id, r.deposit_man
    FROM station_building st
    JOIN rent_contract r ON r.building_id = st.building_id
    WHERE st.dist_m <= :radius
      AND r.contract_ym <= :end_ym
      AND r.contract_ym > PERIOD_ADD(:end_ym, 0 - :n)
      AND r.area_m2 <= 33
      AND r.monthly_man = 0
  )
  SELECT DISTINCT station_id,
         COUNT(*) OVER (PARTITION BY station_id) AS n,
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY deposit_man) OVER (PARTITION BY station_id) AS p25,
         PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY deposit_man) OVER (PARTITION BY station_id) AS p50,
         PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY deposit_man) OVER (PARTITION BY station_id) AS p75
  FROM near
) j ON j.station_id = s.station_id
WHERE m.n IS NOT NULL OR j.n IS NOT NULL
