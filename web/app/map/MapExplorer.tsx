"use client";

// 지도로 비교(SPEC 9장 /map, docs/03 5 · 7장): 필터 → 지도 핀 → 선택한 회사 카드 → 비교 패널
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CompareView } from "@/components/compare/CompareView";
import { CompareButton } from "@/components/CompareButton";
import { Estimate } from "@/components/Estimate";
import { NaverMap, type Bbox, type MapMarker } from "@/components/map/NaverMap";
import { ErrorBox } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { formatCount, formatPct, formatWon } from "@/lib/format";
import styles from "./map.module.css";

type Metric = "growth" | "quit" | "salary";
type Pin = Schemas["MapCompany"];

const METRICS: { key: Metric; label: string }[] = [
  { key: "growth", label: "12개월 증감" },
  { key: "quit", label: "연간 퇴사율" },
  { key: "salary", label: "추정 연봉" },
];

// 서울 자치구(법정동코드 앞 5자리). region 테이블과 같다
const GU: [string, string][] = [
  ["11110", "종로구"], ["11140", "중구"], ["11170", "용산구"], ["11200", "성동구"], ["11215", "광진구"],
  ["11230", "동대문구"], ["11260", "중랑구"], ["11290", "성북구"], ["11305", "강북구"], ["11320", "도봉구"],
  ["11350", "노원구"], ["11380", "은평구"], ["11410", "서대문구"], ["11440", "마포구"], ["11470", "양천구"],
  ["11500", "강서구"], ["11530", "구로구"], ["11545", "금천구"], ["11560", "영등포구"], ["11590", "동작구"],
  ["11620", "관악구"], ["11650", "서초구"], ["11680", "강남구"], ["11710", "송파구"], ["11740", "강동구"],
];

const BASIS: Record<Pin["basis"], string> = {
  dart_hq: "본사 주소 기준 위치입니다.",
  name_search: "회사 이름과 도로명으로 찾은 건물 위치입니다.",
  road: "도로 중심으로 표시한 대략적인 위치입니다.",
  dong: "동 중심으로 표시한 대략적인 위치입니다.",
};

const CITY_HALL = { lat: 37.5665, lon: 126.978 };

function pinLabel(p: Pin, metric: Metric) {
  if (p.value === null) return "–";
  if (metric === "salary") return `${Math.round(p.value / 10_000).toLocaleString("ko-KR")}만`;
  return formatPct(p.value, metric === "growth");
}

export function MapExplorer() {
  const [metric, setMetric] = useState<Metric>("growth");
  const [region, setRegion] = useState("");
  const [industryText, setIndustryText] = useState("");
  const [industry, setIndustry] = useState("");
  const [bbox, setBbox] = useState<Bbox | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  const industries = useApi<Schemas["IndustryList"]>("/industries");
  const industryList = industries.status === "ok" ? industries.data.items.filter((i) => i.code !== "999999") : [];

  const path = useMemo(() => {
    if (!bbox) return null; // 지도가 범위를 알려 줄 때까지 기다린다
    const p = new URLSearchParams({ metric });
    if (region) p.set("region", region);
    if (industry) p.set("industry", industry);
    p.set("bbox", [bbox.minLon, bbox.minLat, bbox.maxLon, bbox.maxLat].map((v) => v.toFixed(5)).join(","));
    return `/map/companies?${p}`;
  }, [metric, region, industry, bbox]);
  const state = useApi<Schemas["MapCompanies"]>(path);

  // 새로 부르는 동안에도 앞 결과의 핀을 지우지 않는다
  const [data, setData] = useState<Schemas["MapCompanies"] | null>(null);
  useEffect(() => {
    if (state.status === "ok") setData(state.data);
  }, [state]);

  // 같은 좌표(동 · 도로 중심 등)의 회사는 핀 하나로 묶는다
  const groups = useMemo(() => {
    const byPoint = new Map<string, Pin[]>();
    for (const item of data?.items ?? []) {
      const key = `${item.lat.toFixed(5)},${item.lon.toFixed(5)}`;
      byPoint.set(key, [...(byPoint.get(key) ?? []), item]);
    }
    return byPoint;
  }, [data]);

  const markers: MapMarker[] = [...groups].map(([key, items]) => {
    const first = items[0];
    return {
      key, lat: first.lat, lon: first.lon,
      label: items.length > 1 ? `${items.length}곳` : pinLabel(first, metric),
      title: items.length > 1 ? `${first.name} 외 ${items.length - 1}곳` : first.name,
      approx: items.every((i) => i.accuracy !== "building"),
      muted: items.length === 1 && first.members < 10,
      selected: key === selected,
    };
  });
  const picked = selected ? groups.get(selected) ?? [] : [];

  function pickIndustry(text: string) {
    setIndustryText(text);
    const found = industryList.find((i) => i.name === text.trim());
    if (found || !text.trim()) setIndustry(found?.code ?? "");
  }

  return (
    <div className={styles.layout}>
      <div className={styles.filters} role="group" aria-label="지도 필터">
        <label>
          지역
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">서울 전체</option>
            {GU.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
        </label>
        <label>
          업종
          <input list="map-industries" value={industryText} placeholder="업종 이름으로 찾기"
            onChange={(e) => pickIndustry(e.target.value)} />
          <datalist id="map-industries">
            {industryList.map((i) => <option key={i.code} value={i.name} />)}
          </datalist>
        </label>
        <div className={styles.seg} role="radiogroup" aria-label="핀에 표시할 지표">
          {METRICS.map((m) => (
            <button key={m.key} type="button" role="radio" aria-checked={metric === m.key}
              onClick={() => setMetric(m.key)}>{m.label}</button>
          ))}
        </div>
      </div>

      <NaverMap markers={markers} center={CITY_HALL} zoom={15}
        onSelect={(key) => setSelected((s) => (s === key ? null : key))}
        onBoundsChange={(b) => setBbox(b)} />

      <div className={styles.status} role="status">
        {state.status === "error" ? null : data ? (
          <>
            <span>지도 안의 회사 <b className="num">{data.items.length}</b>곳(가입자 많은 순)</span>
            {data.truncated && <span>200곳이 넘어 일부만 보입니다. 지도를 확대하거나 지역 · 업종을 골라 범위를 좁혀 주세요.</span>}
            {data.ungeocoded_count > 0 && (
              <span className="muted">
                조건에 맞는 회사 중 {data.ungeocoded_count.toLocaleString("ko-KR")}곳은 위치 정보가 없어 지도에 없습니다.
              </span>
            )}
          </>
        ) : <span className="muted">지도를 불러오는 중</span>}
      </div>
      {state.status === "error" && <ErrorBox error={state.error} retry={state.retry} />}

      {picked.length > 0 && <Picked items={picked} metric={metric} />}

      <section className={styles.compare} aria-labelledby="map-compare">
        <h2 id="map-compare">비교</h2>
        <CompareView />
      </section>
    </div>
  );
}

function Picked({ items, metric }: { items: Pin[]; metric: Metric }) {
  return (
    <section className={styles.picked} aria-label="선택한 회사">
      {items.length > 1 && <p className="small muted">같은 위치에 {items.length}곳이 있습니다.</p>}
      {items.map((p) => (
        <article key={p.company_id} className={styles.card}>
          <h3><Link href={`/companies/${p.company_id}`}>{p.name}</Link></h3>
          <dl className={styles.facts}>
            <div><dt>가입자</dt><dd className="num">{formatCount(p.members)}</dd></div>
            <div><dt>12개월 증감</dt><dd className="num">{p.growth_12m == null ? "계산 안 함" : formatPct(p.growth_12m, true)}</dd></div>
            <div><dt>연간 퇴사율</dt><dd className="num">{formatPct(p.quit_rate_12m)}</dd></div>
            <div><dt>연봉 <Estimate /></dt><dd className="num">{p.avg_salary_est == null ? "–" : `≥ ${formatWon(p.avg_salary_est)}`}</dd></div>
          </dl>
          <p className={p.accuracy === "building" ? "small muted" : "note"}>{BASIS[p.basis]}</p>
          {p.members < 10 && <p className="note">가입자가 10명 미만이라 비율이 크게 흔들릴 수 있습니다.</p>}
          <div className={styles.actions}>
            <Link className="button quiet" href={`/companies/${p.company_id}`}>상세 보기</Link>
            <CompareButton id={p.company_id} name={p.name} />
          </div>
          <span className="sr-only">핀 값: {pinLabel(p, metric)}</span>
        </article>
      ))}
    </section>
  );
}
