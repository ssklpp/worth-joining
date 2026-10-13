"use client";

// 지도 메인 화면(decisions/006)의 공유 상태. 레이아웃이 지도와 패널을 함께 감싸므로
// 패널(목록 · 상세 · 비교)이 바뀌어도 지도와 이 상태는 그대로 남는다
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Bbox } from "@/components/map/NaverMap";
import { useApi, type ApiState, type Schemas } from "@/lib/api";

export type Metric = "growth" | "quit" | "salary";
export type Pin = Schemas["MapCompany"];
/** 상세에서 연 회사. 지도는 이 위치로 옮기고 핀을 채운다 */
export type Selected = { id: number; name: string; lat: number; lon: number; approx: boolean; seq: number };

type Explore = {
  metric: Metric;
  setMetric: (m: Metric) => void;
  region: string;
  setRegion: (r: string) => void;
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
  /** "목록으로"가 돌아갈 주소(검색어 포함) */
  listUrl: string;
  setListUrl: (url: string) => void;
};

const Ctx = createContext<Explore | null>(null);

export const pointKey = (p: { lat: number; lon: number }) => `${p.lat.toFixed(5)},${p.lon.toFixed(5)}`;

export function ExploreProvider({ children }: { children: React.ReactNode }) {
  const [metric, setMetric] = useState<Metric>("growth");
  const [region, setRegion] = useState("");
  const [industry, setIndustry] = useState("");
  const [bbox, setBbox] = useState<Bbox | null>(null);
  const [hover, setHover] = useState<number | null>(null);
  const [selected, setSelected] = useState<Selected | null>(null);
  const [point, setPoint] = useState<string | null>(null);
  const [listUrl, setListUrl] = useState("/");

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
    metric, setMetric, region, setRegion, industry, setIndustry, setBbox,
    pinPath, pinState, pins, hover, setHover, point, setPoint, listUrl, setListUrl,
    selected, select,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useExplore() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useExplore는 ExploreProvider 안에서만 쓴다");
  return v;
}
