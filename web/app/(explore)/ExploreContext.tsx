"use client";

// 지도 메인 화면(decisions/006)의 공유 상태. 레이아웃이 지도와 패널을 함께 감싸므로
// 패널(목록 · 상세 · 비교)이 바뀌어도 지도와 이 상태는 그대로 남는다
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Bbox, MapFocus } from "@/components/map/NaverMap";
import { useApi, type ApiState, type Schemas } from "@/lib/api";
import { CITY_HALL, CITY_ZOOM, GU, GU_ZOOM } from "@/lib/regions";

export type Metric = "growth" | "quit" | "salary";
export type Pin = Schemas["MapCompany"];
/** 상세에서 연 회사. 지도는 이 위치로 옮기고 핀을 채운다 */
export type Selected = { id: number; name: string; lat: number; lon: number; approx: boolean; seq: number };
/** 역세권 반경(m, decisions/009) */
export const RADII = [500, 750] as const;
export type Radius = (typeof RADII)[number];

type Explore = {
  metric: Metric;
  setMetric: (m: Metric) => void;
  region: string;
  /** 지역 필터를 바꾸고 지도를 그 구(빈 값이면 서울 전체)로 옮긴다 */
  setRegion: (r: string) => void;
  /** 지역을 고를 때 옮길 곳. 회사 · 역 선택과 함께 MapPane이 마지막 것을 따른다 */
  regionFocus: MapFocus | null;
  industry: string;
  setIndustry: (code: string) => void;
  setBbox: (b: Bbox) => void;
  pinPath: string | null;
  pinState: ApiState<Schemas["MapCompanies"]>;
  pins: Schemas["MapCompanies"] | null;
  hover: number | null;
  setHover: (id: number | null) => void;
  selected: Selected | null;
  select: (s: Omit<Selected, "seq"> | null) => void;
  /** 같은 좌표 핀을 눌렀을 때 목록을 그 건물 회사로 좁힌다 */
  point: string | null;
  setPoint: (key: string | null) => void;
  /** 목록 패널의 지금 페이지 회사. 값이 있으면 지도는 이 회사들의 핀만 그린다(목록이 닫히면 null) */
  pageIds: Set<number> | null;
  setPageIds: (ids: Set<number> | null) => void;
  /** 역 시세 화면에서 고른 반경. 지도는 연 역에 반경 원을 그린다. 다른 역으로 옮겨도 유지한다 */
  radius: Radius;
  setRadius: (r: Radius) => void;
  /** "목록으로"가 돌아갈 주소(검색어 포함) */
  listUrl: string;
  setListUrl: (url: string) => void;
};

const Ctx = createContext<Explore | null>(null);

/** 지도에 한 번에 그리는 회사 핀 수이자 목록 한 페이지의 회사 수 */
export const PIN_LIMIT = 10;

export const pointKey = (p: { lat: number; lon: number }) => `${p.lat.toFixed(5)},${p.lon.toFixed(5)}`;

export function ExploreProvider({ children }: { children: React.ReactNode }) {
  const [metric, setMetric] = useState<Metric>("growth");
  const [region, setRegionCode] = useState("");
  const [regionFocus, setRegionFocus] = useState<MapFocus | null>(null);
  const setRegion = useCallback((code: string) => {
    setRegionCode(code);
    const gu = GU.find((g) => g.code === code);
    setRegionFocus(gu ? { lat: gu.lat, lon: gu.lon, zoom: GU_ZOOM, exact: true }
      : { ...CITY_HALL, zoom: CITY_ZOOM, exact: true });
  }, []);
  const [industry, setIndustry] = useState("");
  const [bbox, setBbox] = useState<Bbox | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [selected, setSelected] = useState<Selected | null>(null);
  const [point, setPoint] = useState<string | null>(null);
  const [listUrl, setListUrl] = useState("/");
  const [pageIds, setPageIds] = useState<Set<number> | null>(null);
  const [radius, setRadius] = useState<Radius>(500);

  const pinPath = useMemo(() => {
    if (!bbox) return null; // 지도가 범위를 알려 줄 때까지 기다린다
    const p = new URLSearchParams({ metric });
    if (region) p.set("region", region);
    if (industry) p.set("industry", industry);
    p.set("bbox", [bbox.minLon, bbox.minLat, bbox.maxLon, bbox.maxLat].map((v) => v.toFixed(5)).join(","));
    return `/map/companies?${p}`;
  }, [metric, region, industry, bbox]);
  const pinState = useApi<Schemas["MapCompanies"]>(pinPath);

  // 새로 부르는 동안에도 앞 결과의 핀과 목록을 지우지 않는다
  const [pins, setPins] = useState<Schemas["MapCompanies"] | null>(null);
  useEffect(() => {
    if (pinState.status === "ok") setPins(pinState.data);
  }, [pinState]);

  const select = useCallback((s: Omit<Selected, "seq"> | null) => {
    setSelected((prev) => (s ? { ...s, seq: (prev?.seq ?? 0) + 1 } : null));
  }, []);

  const value: Explore = {
    metric, setMetric, region, setRegion, regionFocus, industry, setIndustry, setBbox,
    pinPath, pinState, pins, hover, setHover, point, setPoint, listUrl, setListUrl, pageIds, setPageIds,
    radius, setRadius, selected, select,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useExplore() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useExplore는 ExploreProvider 안에서만 쓴다");
  return v;
}
