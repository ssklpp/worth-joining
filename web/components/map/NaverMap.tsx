"use client";

// 네이버 지도 감싸개(SPEC Phase 8-4). 화면은 markers · onSelect · center 같은 공통 props만 쓰고
// react-naver-maps · naver.maps는 이 파일 밖으로 내보내지 않는다(지도 SDK 교체 대비).
// 키는 Client ID(ncpKeyId)만 쓴다. Client Secret이 필요한 REST API는 쓰지 않는다(SPEC 4장).
import { useEffect, useRef } from "react";
import {
  Container, CustomOverlay, NaverMap as Map, NavermapsProvider, useListener, useMap,
} from "react-naver-maps";
import styles from "./map.module.css";

export type LatLon = { lat: number; lon: number };
export type Bbox = { minLon: number; minLat: number; maxLon: number; maxLat: number };
export type MapMarker = LatLon & {
  key: string;
  label: string; // 핀 안의 글자(지표 값, 묶음이면 "N곳")
  name: string; // 강조 · 선택일 때 값 앞에 펼치는 회사 이름
  title: string; // 접근성 이름
  approx?: boolean; // 대략 위치: 점선 테두리
  muted?: boolean; // 가입자 10명 미만: 흐린 색
  selected?: boolean;
  highlighted?: boolean; // 목록 항목에 마우스를 올렸을 때
};

/** 지하철역 표시(decisions/007 9번). 회사 핀보다 아래에 깔고, 누르면 역 시세를 연다 */
export type StationMarker = LatLon & { key: string; name: string; selected?: boolean }; // selected: 역 비교함에 담김

/** 지도를 옮길 곳. 객체가 바뀔 때마다 이동한다(같은 회사를 다시 열어도).
 * exact면 그 확대로 맞추고(구 · 서울 전체로 넓게 보기), 아니면 지금보다 멀리 있을 때만 확대한다 */
export type MapFocus = LatLon & { zoom: number; exact?: boolean };

type Props = {
  markers: MapMarker[];
  stations?: StationMarker[];
  onStationSelect?: (key: string) => void;
  center: LatLon;
  zoom: number;
  focus?: MapFocus | null;
  onSelect: (key: string) => void;
  onHover?: (key: string | null) => void;
  onBoundsChange: (bbox: Bbox, zoom: number) => void;
};

const KEY_ID = process.env.NEXT_PUBLIC_NAVER_MAP_CLIENT_ID ?? "";

export function NaverMap(props: Props) {
  if (!KEY_ID) {
    return (
      <div className={styles.missing}>
        지도를 불러올 수 없습니다. 지도 키(NEXT_PUBLIC_NAVER_MAP_CLIENT_ID)가 없습니다.
      </div>
    );
  }
  const { markers, stations = [], onStationSelect, center, zoom, focus, onSelect, onHover, onBoundsChange } = props;
  return (
    <NavermapsProvider ncpKeyId={KEY_ID}>
      <Container className={styles.map}
        fallback={<div className={styles.loading} role="status">지도를 불러오는 중</div>}>
        <Map defaultCenter={{ lat: center.lat, lng: center.lon }} defaultZoom={zoom} minZoom={10}
          zoomControl>
          <BoundsReporter onChange={onBoundsChange} />
          <FocusMover focus={focus ?? null} />
          {stations.map((s) => (
            <CustomOverlay key={s.key} position={{ lat: s.lat, lng: s.lon }} zIndex={0}>
              <button type="button" className={`${styles.station} ${s.selected ? styles.stationSelected : ""}`}
                title={`${s.name} 시세 보기${s.selected ? " (비교함에 담음)" : ""}`}
                aria-label={`${s.name} 시세 보기${s.selected ? " (비교함에 담음)" : ""}`}
                onClick={() => onStationSelect?.(s.key)}>
                {s.name}
              </button>
            </CustomOverlay>
          ))}
          {markers.map((m) => (
            <CustomOverlay key={m.key} position={{ lat: m.lat, lng: m.lon }}
              zIndex={m.selected ? 10 : m.highlighted ? 9 : 1}>
              <button type="button" title={m.title} aria-label={m.title} aria-pressed={m.selected}
                className={[styles.pin, m.approx && styles.approx, m.muted && styles.muted,
                  m.highlighted && styles.highlighted, m.selected && styles.selected].filter(Boolean).join(" ")}
                onClick={() => onSelect(m.key)}
                onMouseEnter={() => onHover?.(m.key)} onMouseLeave={() => onHover?.(null)}>
                <span className={styles.name}>{m.name}</span>
                {m.label}
              </button>
            </CustomOverlay>
          ))}
        </Map>
      </Container>
    </NavermapsProvider>
  );
}

/** focus가 바뀌면 그 위치로 옮긴다(확대는 MapFocus 설명). 움직임을 줄이는 설정이면 바로 옮긴다 */
function FocusMover({ focus }: { focus: MapFocus | null }) {
  const map = useMap();
  useEffect(() => {
    if (!focus) return;
    const center = { lat: focus.lat, lng: focus.lon };
    const zoom = focus.exact ? focus.zoom : Math.max(map.getZoom(), focus.zoom);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      map.setCenter(center);
      map.setZoom(zoom);
    } else {
      map.morph(center, zoom);
    }
  }, [map, focus]);
  return null;
}

/** 처음 그려졌을 때와 지도를 옮기거나 확대한 뒤 멈출 때(idle) 보이는 범위를 알린다 */
function BoundsReporter({ onChange }: { onChange: Props["onBoundsChange"] }) {
  const map = useMap();
  const latest = useRef(onChange);
  useEffect(() => {
    latest.current = onChange;
  });

  const report = () => {
    const b = map.getBounds() as naver.maps.LatLngBounds;
    const sw = b.getSW(), ne = b.getNE();
    latest.current({ minLon: sw.lng(), minLat: sw.lat(), maxLon: ne.lng(), maxLat: ne.lat() },
      map.getZoom());
  };
  useEffect(report, [map]);
  useListener(map, "idle", report);
  return null;
}
