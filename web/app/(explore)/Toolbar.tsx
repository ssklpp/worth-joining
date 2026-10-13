"use client";

// 지도 메인 화면의 위쪽 막대(docs/03 5장): 회사 검색 · 업종 · 지역 · 핀에 표시할 지표.
// 검색어는 URL(?q=)에 둬서 뒤로 가기 · 공유가 되고, 업종 · 지역은 지도 핀과 목록에 함께 걸린다
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useApi, type Schemas } from "@/lib/api";
import { useExplore, type Metric } from "./ExploreContext";
import styles from "./explore.module.css";

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

export function Toolbar() {
  const router = useRouter();
  const q = useSearchParams().get("q")?.trim() ?? "";
  const { metric, setMetric, region, setRegion, setIndustry, setPoint } = useExplore();

  const industries = useApi<Schemas["IndustryList"]>("/industries");
  const industryList = industries.status === "ok" ? industries.data.items.filter((i) => i.code !== "999999") : [];

  const [text, setText] = useState(q);
  const [industryText, setIndustryText] = useState("");
  useEffect(() => setText(q), [q]);

  function search(event: React.FormEvent) {
    event.preventDefault();
    const typed = text.trim();
    setPoint(null);
    router.push(typed ? `/?${new URLSearchParams({ q: typed })}` : "/");
  }

  function pickIndustry(value: string) {
    setIndustryText(value);
    const found = industryList.find((i) => i.name === value.trim());
    if (found || !value.trim()) setIndustry(found?.code ?? "");
  }

  return (
    <div className={styles.toolbar}>
      <form className={styles.search} role="search" onSubmit={search}>
        <label className="sr-only" htmlFor="q">회사명 또는 사업자번호 앞 6자리</label>
        <input id="q" type="search" value={text} onChange={(e) => setText(e.target.value)}
          placeholder="회사명 또는 사업자번호 앞 6자리" autoComplete="off" maxLength={100} />
        <button type="submit" className="button">검색</button>
      </form>
      <div className={styles.filters} role="group" aria-label="지도와 목록 필터">
        <label>
          업종
          <input list="industry-list" value={industryText} placeholder="업종 이름으로 찾기" autoComplete="off"
            onChange={(e) => pickIndustry(e.target.value)} />
          <datalist id="industry-list">
            {industryList.map((i) => <option key={i.code} value={i.name} />)}
          </datalist>
        </label>
        <label>
          지역
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">서울 전체</option>
            {GU.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
        </label>
        <div className={styles.seg} role="radiogroup" aria-label="지도 핀에 표시할 값">
          {METRICS.map((m) => (
            <button key={m.key} type="button" role="radio" aria-checked={metric === m.key}
              onClick={() => setMetric(m.key)}>{m.label}</button>
          ))}
        </div>
      </div>
    </div>
  );
}
