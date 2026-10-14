"use client";

// 지도 칸(docs/03 5장): 핀 · 범례 · 비교함 막대. 핀을 누르면 회사 상세 패널을 연다
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { NaverMap, type Bbox, type MapFocus, type MapMarker, type StationMarker } from "@/components/map/NaverMap";
import { useApi, type Schemas } from "@/lib/api";
import { MAX_COMPARE, useCompare } from "@/lib/compare";
import { formatPct, stationLabel } from "@/lib/format";
import { pointKey, useExplore, type Metric, type Pin } from "./ExploreContext";
import styles from "./explore.module.css";

const CITY_HALL = { lat: 37.5665, lon: 126.978 };
const STATION_ZOOM = 14; // 이보다 멀리 보면 역 이름이 회사 핀을 가려 숨긴다

export function pinLabel(value: number | null, metric: Metric) {
  if (value === null) return "–";
  if (metric === "salary") return `${Math.round(value / 10_000).toLocaleString("ko-KR")}만`;
  return formatPct(value, metric === "growth");
}

export function MapPane() {
  const router = useRouter();
  const { pins, metric, selected, hover, point, setHover, setPoint, setBbox } = useExplore();
  const stationState = useApi<Schemas["StationList"]>("/stations");
  const allStations = useMemo(() => (stationState.status === "ok" ? stationState.data.items : []), [stationState]);
  const [view, setView] = useState<{ bbox: Bbox; zoom: number } | null>(null);
  const stations: StationMarker[] = view && view.zoom >= STATION_ZOOM
    ? allStations
      .filter((s) => s.lon >= view.bbox.minLon && s.lon <= view.bbox.maxLon
        && s.lat >= view.bbox.minLat && s.lat <= view.bbox.maxLat)
      .map((s) => ({ key: String(s.station_id), name: stationLabel(s.name), lat: s.lat, lon: s.lon }))
    : [];

  // 같은 좌표(같은 건물, 동 · 도로 중심)의 회사는 핀 하나로 묶는다
  const groups = useMemo(() => {
    const byPoint = new Map<string, Pin[]>();
    for (const item of pins?.items ?? []) {
      const key = pointKey(item);
      byPoint.set(key, [...(byPoint.get(key) ?? []), item]);
    }
    return byPoint;
  }, [pins]);

  const markers: MapMarker[] = [...groups].map(([key, items]) => {
    const first = items[0];
    const many = items.length > 1;
    const label = many ? `${items.length}곳` : pinLabel(first.value, metric);
    const name = many ? `${first.name} 등` : first.name;
    return {
      key, lat: first.lat, lon: first.lon, label, name,
      title: `${name} ${label}`, // 펼쳤을 때 보이는 글자 그대로("○○ 등 6곳", WCAG 2.5.3)
      approx: items.every((i) => i.accuracy !== "building"),
      muted: !many && first.members < 10,
      selected: key === point || items.some((i) => i.company_id === selected?.id),
      highlighted: items.some((i) => i.company_id === hover),
    };
  });
  // 상세에서 연 회사가 지금 범위의 상위 200곳에 없어도 핀은 보인다
  if (selected && !markers.some((m) => m.selected)) {
    markers.push({
      key: `selected-${selected.id}`, lat: selected.lat, lon: selected.lon, label: "", name: selected.name,
      title: selected.name, approx: selected.approx, selected: true,
    });
  }

  const focus = useMemo<MapFocus | null>(
    () => (selected ? { lat: selected.lat, lon: selected.lon, zoom: 15 } : null), [selected]);

  function open(key: string) {
    const items = groups.get(key);
    if (!items) return; // 상세에서 연 회사 핀
    if (items.length === 1) {
      router.push(`/companies/${items[0].company_id}`);
    } else {
      setPoint(key);
      router.push("/");
    }
  }

  return (
    <div className={styles.mapPane}>
      <NaverMap markers={markers} center={CITY_HALL} zoom={15} focus={focus} onSelect={open}
        onHover={(key) => {
          const items = key ? groups.get(key) : undefined;
          setHover(items?.length === 1 ? items[0].company_id : null);
        }}
        stations={stations} onStationSelect={(key) => router.push(`/stations/${key}`)}
        onBoundsChange={(b, zoom) => {
          setBbox(b);
          setView({ bbox: b, zoom });
        }} />
      <StationSearch stations={allStations} />
      <div className={styles.legend} aria-hidden="true">
        <span><i className={styles.lgTag} />회사 (건물 위치)</span>
        <span><i className={`${styles.lgTag} ${styles.lgDash}`} />대략 위치</span>
        <span><i className={`${styles.lgTag} ${styles.lgDim}`} />가입자 10명 미만</span>
        <span><i className={styles.lgStation} />지하철역 (확대하면 표시)</span>
      </div>
      <CompareTray />
    </div>
  );
}

/** 지도 왼쪽 아래 비교함: 담은 회사 칩(×로 빼기)과 "비교하기"(2곳 이상) */
function CompareTray() {
  const { items, remove } = useCompare();
  const onCompare = usePathname() === "/compare";
  if (!items.length) return null;
  return (
    <div className={styles.tray} aria-label="비교함">
      <span className="muted">비교함 <span className="num">{items.length}/{MAX_COMPARE}</span></span>
      {items.map((i) => (
        <span key={i.id} className={styles.chip}>
          {i.name}
          <button type="button" aria-label={`${i.name} 비교에서 빼기`} onClick={() => remove(i.id)}>×</button>
        </span>
      ))}
      {items.length >= 2 && !onCompare && <Link className="button" href="/compare">비교하기</Link>}
    </div>
  );
}

/** 지도 검색창(FR-MAP-05): 역 이름으로 그 역 시세를 열고 지도를 옮긴다. 주소 검색(지오코딩)은 하지 않는다 */
function StationSearch({ stations }: { stations: Schemas["StationListItem"][] }) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [missing, setMissing] = useState(false);

  function go(event: React.FormEvent) {
    event.preventDefault();
    const typed = text.trim();
    const name = typed.replace(/역$/, "");
    // "서울역"처럼 이름 자체가 역으로 끝나는 역이 있어 붙인 이름 · 뗀 이름을 모두 맞춰 본다
    const found = stations.find((s) => s.name === typed || s.name === name)
      ?? stations.find((s) => s.name.startsWith(name));
    setMissing(!found);
    if (found && name) {
      setText("");
      router.push(`/stations/${found.station_id}`);
    }
  }

  return (
    <form className={styles.stationSearch} role="search" aria-label="역 찾기" onSubmit={go}>
      <label className="sr-only" htmlFor="station-q">역 이름으로 지도 이동</label>
      <input id="station-q" list="station-list" value={text} placeholder="역 이름으로 이동" autoComplete="off"
        maxLength={30} onChange={(e) => { setText(e.target.value); setMissing(false); }}
        aria-describedby={missing ? "station-missing" : undefined} />
      <datalist id="station-list">
        {stations.map((s) => <option key={s.station_id} value={stationLabel(s.name)} />)}
      </datalist>
      <button type="submit" className="button quiet">이동</button>
      {missing && <p id="station-missing" className="small" role="status">서울 역 목록에 없는 이름입니다.</p>}
    </form>
  );
}
