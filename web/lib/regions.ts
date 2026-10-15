// 서울 자치구(법정동코드 앞 5자리, region 테이블과 같다)와 지도를 옮길 중심점.
// 중심점은 주소정보누리집 서울 건물 출입구 좌표(data/raw/juso)의 구별 중앙값이다(2026-10 파일, 구마다 1.1만 ~ 3.2만 건물).
// 구 경계가 바뀌지 않는 한 다시 계산할 필요가 없다
export type Gu = { code: string; name: string; lat: number; lon: number };

export const GU: Gu[] = [
  { code: "11110", name: "종로구", lat: 37.5782, lon: 126.9907 },
  { code: "11140", name: "중구", lat: 37.5627, lon: 127.0045 },
  { code: "11170", name: "용산구", lat: 37.5375, lon: 126.9806 },
  { code: "11200", name: "성동구", lat: 37.5523, lon: 127.0438 },
  { code: "11215", name: "광진구", lat: 37.5488, lon: 127.0817 },
  { code: "11230", name: "동대문구", lat: 37.5811, lon: 127.0537 },
  { code: "11260", name: "중랑구", lat: 37.5929, lon: 127.0858 },
  { code: "11290", name: "성북구", lat: 37.6047, lon: 127.0224 },
  { code: "11305", name: "강북구", lat: 37.6317, lon: 127.0222 },
  { code: "11320", name: "도봉구", lat: 37.6572, lon: 127.038 },
  { code: "11350", name: "노원구", lat: 37.6584, lon: 127.073 },
  { code: "11380", name: "은평구", lat: 37.6073, lon: 126.9185 },
  { code: "11410", name: "서대문구", lat: 37.5765, lon: 126.9351 },
  { code: "11440", name: "마포구", lat: 37.5545, lon: 126.9217 },
  { code: "11470", name: "양천구", lat: 37.5291, lon: 126.853 },
  { code: "11500", name: "강서구", lat: 37.5464, lon: 126.843 },
  { code: "11530", name: "구로구", lat: 37.4944, lon: 126.8766 },
  { code: "11545", name: "금천구", lat: 37.4635, lon: 126.9035 },
  { code: "11560", name: "영등포구", lat: 37.5107, lon: 126.904 },
  { code: "11590", name: "동작구", lat: 37.4975, lon: 126.9455 },
  { code: "11620", name: "관악구", lat: 37.4798, lon: 126.9343 },
  { code: "11650", name: "서초구", lat: 37.4855, lon: 127.0146 },
  { code: "11680", name: "강남구", lat: 37.5067, lon: 127.0419 },
  { code: "11710", name: "송파구", lat: 37.5025, lon: 127.1188 },
  { code: "11740", name: "강동구", lat: 37.5428, lon: 127.1351 },
];

export const CITY_HALL = { lat: 37.5665, lon: 126.978 };
export const GU_ZOOM = 14; // 13은 도심 구에서 화면 안 역(자동완성)이 너무 많아 한 단계 더 확대한다
export const CITY_ZOOM = 11; // "서울 전체"를 고르면 서울이 한눈에 들어오게
