-- 역세권 원룸 시세의 최근 24개월 추이 (FR-HOUS-04, decisions/007 9번). grain 하나를 한 번에 넣는다.
-- refresh_mart가 q5와 같은 임시 테이블 station_building을 쓰고 month · quarter로 두 번 실행한다.
-- 조건은 q5와 같다. 기준월 이하이고 기준월 - 24개월보다 뒤(>)인 33㎡ 이하 계약, 역에서 500m 이내 건물.
-- month 구간은 계약 달, quarter 구간은 기준월부터 3개월씩 거꾸로 묶고 구간의 마지막 달을 ym으로 쓴다.
-- 월세(monthly_man > 0)는 환산 월세(원) 분포, 전세(monthly_man = 0)는 보증금(만원) 중앙값이다.
-- PERCENTILE_CONT는 윈도 함수라 DISTINCT와 쓰고, 월세 · 전세를 파티션으로 나눈 뒤 한 행으로 모은다.
-- 주석에는 콜론 + 이름을 쓰지 않는다(TS-020).
INSERT INTO mart_station_rent_trend
  (station_id, period_end_ym, grain, ym, n_monthly, monthly_p25, monthly_median, monthly_p75,
   n_jeonse, jeonse_median_man)
WITH near AS (
  SELECT st.station_id,
         CASE WHEN :grain = 'month' THEN r.contract_ym
              ELSE PERIOD_ADD(:end_ym, -3 * FLOOR(PERIOD_DIFF(:end_ym, r.contract_ym) / 3)) END AS ym,
         r.monthly_man = 0 AS is_jeonse,
         CASE WHEN r.monthly_man = 0 THEN r.deposit_man
              ELSE (r.monthly_man + r.deposit_man * (
                      SELECT cr.rate_year FROM conversion_rate cr
                      WHERE cr.ym <= r.contract_ym ORDER BY cr.ym DESC LIMIT 1) / 12) * 10000
         END AS amount
  FROM station_building st
  JOIN rent_contract r ON r.building_id = st.building_id
  WHERE r.contract_ym <= :end_ym
    AND r.contract_ym > PERIOD_ADD(:end_ym, -24)
    AND r.area_m2 <= 33
),
pct AS (
  SELECT DISTINCT station_id, ym, is_jeonse,
         COUNT(*) OVER (PARTITION BY station_id, ym, is_jeonse) AS n,
         PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY amount)
           OVER (PARTITION BY station_id, ym, is_jeonse) AS p25,
         PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY amount)
           OVER (PARTITION BY station_id, ym, is_jeonse) AS p50,
         PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY amount)
           OVER (PARTITION BY station_id, ym, is_jeonse) AS p75
  FROM near
)
SELECT station_id, :end_ym, :grain, ym,
       COALESCE(MAX(CASE WHEN is_jeonse = 0 THEN n END), 0),
       ROUND(MAX(CASE WHEN is_jeonse = 0 THEN p25 END)),
       ROUND(MAX(CASE WHEN is_jeonse = 0 THEN p50 END)),
       ROUND(MAX(CASE WHEN is_jeonse = 0 THEN p75 END)),
       COALESCE(MAX(CASE WHEN is_jeonse = 1 THEN n END), 0),
       ROUND(MAX(CASE WHEN is_jeonse = 1 THEN p50 END))
FROM pct
GROUP BY station_id, ym
