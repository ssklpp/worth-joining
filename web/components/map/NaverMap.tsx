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
  title: string; // 접근성 이름
  approx?: boolean; // 대략 위치: 점선 테두리
  muted?: boolean; // 가입자 10명 미만: 흐린 색
  selected?: boolean;
};

type Props = {
  markers: MapMarker[];
  center: LatLon;
  zoom: number;
  onSelect: (key: string) => void;
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
  const { markers, center, zoom, onSelect, onBoundsChange } = props;
  return (
    <NavermapsProvider ncpKeyId={KEY_ID}>
      <Container className={styles.map}
        fallback={<div className={styles.loading} role="status">지도를 불러오는 중</div>}>
        <Map defaultCenter={{ lat: center.lat, lng: center.lon }} defaultZoom={zoom} minZoom={10}
          zoomControl>
          <BoundsReporter onChange={onBoundsChange} />
          {markers.map((m) => (
            <CustomOverlay key={m.key} position={{ lat: m.lat, lng: m.lon }}
              zIndex={m.selected ? 10 : 1}>
              <button type="button" title={m.title} aria-label={m.title} aria-pressed={m.selected}
                className={[styles.pin, m.approx && styles.approx, m.muted && styles.muted,
                  m.selected && styles.selected].filter(Boolean).join(" ")}
                onClick={() => onSelect(m.key)}>
                {m.label}
              </button>
            </CustomOverlay>
          ))}
        </Map>
      </Container>
    </NavermapsProvider>
  );
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
