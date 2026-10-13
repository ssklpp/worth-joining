-- 회사 근처 역 (SPEC 7장 q6, decisions/007). refresh_mart가 company_station을 비운 뒤 실행한다.
-- 회사 좌표는 company_location(회사마다 대표 사업장 기준 좌표 하나)이다. 모든 사업장으로 순위를
-- 매기면 같은 역이 중복되어 1순위가 사라진다(검증된 버그). 최신 월에 있는 회사만 본다.
-- 1km 이내 역을 가까운 순 최대 3곳.
-- company_location의 좌표는 숫자 열이라 공간 인덱스가 없다. 그래서 역(309곳)을 바깥에 두고
-- 위도 ± 0.0091도, 경도 ± 0.0114도(서울 위도에서 약 1km) 상자로 먼저 거른 뒤 거리를 잰다.
-- 회사마다 ST_Buffer를 만들면 회사 × 역 전체를 비교해 몇 분이 걸린다(docs/explain.md).
INSERT INTO company_station (company_id, station_id, distance_m, rnk)
SELECT company_id, station_id, distance_m, rnk
FROM (
  SELECT l.company_id, s.station_id,
         ROUND(ST_Distance_Sphere(s.pt, POINT(l.lon, l.lat))) AS distance_m,
         ROW_NUMBER() OVER (PARTITION BY l.company_id
                            ORDER BY ST_Distance_Sphere(s.pt, POINT(l.lon, l.lat)), s.station_id) AS rnk
  FROM station s
  STRAIGHT_JOIN company_location l
    ON l.lat BETWEEN ST_Y(s.pt) - 0.0091 AND ST_Y(s.pt) + 0.0091
   AND l.lon BETWEEN ST_X(s.pt) - 0.0114 AND ST_X(s.pt) + 0.0114
   AND ST_Distance_Sphere(s.pt, POINT(l.lon, l.lat)) <= 1000
  JOIN mart_company_summary m ON m.company_id = l.company_id
) t
WHERE rnk <= 3
