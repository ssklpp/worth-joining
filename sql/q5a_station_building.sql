-- 역세권 건물 (SPEC 7장 q5의 공간 조인, decisions/007). refresh_mart가 임시 테이블 station_building에
-- 넣은 뒤 q5_station_rent.sql이 기간별로 읽는다. 역에서 500m 이내 건물 쌍이다.
-- 공간 조인은 MBRContains(ST_Buffer)로 후보를 먼저 줄인다(0.006도는 약 500m).
-- 이 단순 조인에서는 건물 공간 인덱스를 역마다 다시 쓰는 계획(Range checked for each record)이 나와
-- 1초 안에 끝난다. 시세 계산(윈도 함수)과 한 쿼리로 합치면 옵티마이저가 역 × 건물 전체를 비교해
-- 기간 하나에 몇 분이 걸린다(docs/explain.md). 그래서 두 단계로 나눈다.
INSERT INTO station_building (station_id, building_id)
SELECT st.station_id, b.building_id
FROM station st
STRAIGHT_JOIN building b
  ON MBRContains(ST_Buffer(st.pt, 0.006), b.pt)
 AND ST_Distance_Sphere(st.pt, b.pt) <= 500
