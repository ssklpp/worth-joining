"use client";

// 목록 패널(docs/03 5장). 검색어가 있으면 전체 회사 검색 결과(위치 없는 회사도 나온다),
// 없으면 지금 지도 범위 안의 회사. 지도를 옮기거나 확대하면 바로 바뀐다
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Estimate } from "@/components/Estimate";
import { ErrorBox, Loading } from "@/components/Status";
import { formatCount, formatPct, formatWon } from "@/lib/format";
import { pointKey, useExplore, type Pin } from "./ExploreContext";
import { SearchResults } from "./SearchResults";
import styles from "./explore.module.css";

type Sort = "members" | "growth" | "quit" | "salary";

const SORTS: Record<Sort, { label: string; fn: (a: Pin, b: Pin) => number }> = {
  members: { label: "가입자 많은 순", fn: (a, b) => b.members - a.members },
  growth: { label: "12개월 증감 높은 순", fn: (a, b) => (b.growth_12m ?? -9) - (a.growth_12m ?? -9) },
  quit: { label: "퇴사율 낮은 순", fn: (a, b) => (a.quit_rate_12m ?? 9) - (b.quit_rate_12m ?? 9) },
  salary: { label: "추정 연봉 높은 순", fn: (a, b) => (b.avg_salary_est ?? 0) - (a.avg_salary_est ?? 0) },
};

export function ListPanel() {
  const q = useSearchParams().get("q")?.trim() ?? "";
  const { industry, setListUrl } = useExplore();
  useEffect(() => setListUrl(q ? `/?${new URLSearchParams({ q })}` : "/"), [q, setListUrl]);

  return q ? <SearchResults key={`${q}|${industry}`} q={q} industry={industry} /> : <PinList />;
}

function PinList() {
  const { pins, pinPath, pinState, point, setPoint, hover, setHover } = useExplore();
  const [sort, setSort] = useState<Sort>("members");

  if (!pins) {
    if (pinState.status === "error") return <ErrorBox error={pinState.error} retry={pinState.retry} />;
    return pinPath ? <Loading height={320} label="지도 안의 회사를 불러오는 중" /> : null;
  }

  const atPoint = point ? pins.items.filter((p) => pointKey(p) === point) : [];
  const items = [...(atPoint.length ? atPoint : pins.items)].sort(SORTS[sort].fn);

  return (
    <>
      <div className={styles.listHead}>
        <h2>
          {atPoint.length ? "같은 위치의 회사" : "지도 안의 회사"} <span className="num">{items.length}</span>곳
        </h2>
        <label>
          <span className="sr-only">정렬</span>
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
            {(Object.keys(SORTS) as Sort[]).map((k) => <option key={k} value={k}>{SORTS[k].label}</option>)}
          </select>
        </label>
      </div>
      {atPoint.length > 0 && (
        <button type="button" className={styles.back} onClick={() => setPoint(null)}>지도 안의 회사 모두 보기</button>
      )}
      {pinState.status === "error" && <ErrorBox error={pinState.error} retry={pinState.retry} />}
      {!atPoint.length && pins.truncated && (
        <p className="note">
          조건에 맞는 회사가 200곳이 넘어 가입자 많은 200곳만 보입니다. 지도를 확대하거나 지역 · 업종을 골라 주세요.
        </p>
      )}
      {items.length ? (
        <ul className={styles.items}>
          {items.map((p) => (
            <li key={p.company_id}>
              <Link href={`/companies/${p.company_id}`}
                className={`${styles.item} ${hover === p.company_id ? styles.on : ""}`}
                onMouseEnter={() => setHover(p.company_id)} onMouseLeave={() => setHover(null)}
                onFocus={() => setHover(p.company_id)} onBlur={() => setHover(null)}>
                <span className={styles.itName}>{p.name}</span>
                <span className={styles.itSub}>
                  가입자 {formatCount(p.members)}{p.accuracy !== "building" && ", 대략 위치"}
                </span>
                <span className={styles.itMetrics}>
                  <span><i>12개월 증감</i>{p.growth_12m == null ? "계산 안 함" : formatPct(p.growth_12m, true)}</span>
                  <span><i>연간 퇴사율</i>{formatPct(p.quit_rate_12m)}</span>
                  <span>
                    <i>연봉 <Estimate /></i>{p.avg_salary_est == null ? "–" : `≥ ${formatWon(p.avg_salary_est)}`}
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p>이 범위에는 조건에 맞는 회사가 없습니다. 지도를 넓히거나 업종 · 지역 필터를 줄여 보세요.</p>
      )}
      {pins.ungeocoded_count > 0 && (
        <p className="small muted">
          조건에 맞는 회사 중 {pins.ungeocoded_count.toLocaleString("ko-KR")}곳은 위치 정보가 없어 지도에 없습니다.
          회사 이름으로 검색하면 찾을 수 있습니다.
        </p>
      )}
      <p className="small muted">지도를 움직이거나 확대하면 목록이 바뀝니다. 회사를 누르면 상세가 열립니다.</p>
    </>
  );
}
