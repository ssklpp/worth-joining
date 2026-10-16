"use client";

// 목록 패널(docs/03 5장). 검색어가 있으면 전체 회사 검색 결과(위치 없는 회사도 나온다),
// 없으면 지금 지도 범위 안의 회사. 지도를 옮기거나 확대하면 바로 바뀐다.
// 지도 안의 회사는 10곳 또는 20곳씩 페이지로 나누고, 지도도 그 페이지의 회사 핀만 그린다
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef } from "react";
import { Estimate } from "@/components/Estimate";
import { ErrorBox, Loading } from "@/components/Status";
import { formatCount, formatPct, formatWon } from "@/lib/format";
import { PAGE_SIZES, pointKey, useExplore, type ListSort, type PageSize, type Pin } from "./ExploreContext";
import { SearchResults } from "./SearchResults";
import styles from "./explore.module.css";

const SORTS: Record<ListSort, { label: string; fn: (a: Pin, b: Pin) => number }> = {
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
  const { pins, pinPath, pinState, point, setPoint, hover, setHover, setPageIds,
    listSort: sort, setListSort, listSize: size, setListSize, listPage, setListPage } = useExplore();
  const top = useRef<HTMLDivElement>(null);
  // 정렬 · 페이지 크기 · 페이지는 공유 상태라 상세에 갔다 돌아와도 남는다. 페이지는 그때와 같은
  // 핀 결과 · 같은 위치 보기일 때만 쓰고, 지도를 옮겼거나 정렬 · 크기를 바꾸면 1페이지
  const page = listPage.pins === pins && listPage.point === point ? listPage.page : 1;

  const items = useMemo(() => {
    if (!pins) return [];
    const atPoint = point ? pins.items.filter((p) => pointKey(p) === point) : [];
    return [...(atPoint.length ? atPoint : pins.items)].sort(SORTS[sort].fn);
  }, [pins, point, sort]);
  const pages = Math.max(1, Math.ceil(items.length / size));
  const current = Math.min(page, pages);
  const shown = items.slice((current - 1) * size, current * size);

  // 지도를 옮겨 같은 위치 회사가 범위 밖으로 나가면 위치 보기를 푼다
  useEffect(() => {
    if (pins && point && !pins.items.some((p) => pointKey(p) === point)) setPoint(null);
  }, [pins, point, setPoint]);
  // 지도는 이 페이지의 회사만. 목록을 떠나면(상세 · 비교 · 검색) 다시 모든 핀
  const shownKey = shown.map((p) => p.company_id).join(",");
  useEffect(() => {
    setPageIds(pins ? new Set(shownKey ? shownKey.split(",").map(Number) : []) : null);
  }, [pins, shownKey, setPageIds]);
  useEffect(() => () => setPageIds(null), [setPageIds]);

  function go(n: number) {
    setListPage({ page: n, pins, point });
    top.current?.scrollIntoView({ block: "nearest" });
  }
  function reset() {
    setListPage({ page: 1, pins, point });
  }

  if (!pins) {
    if (pinState.status === "error") return <ErrorBox error={pinState.error} retry={pinState.retry} />;
    return pinPath ? <Loading height={320} label="지도 안의 회사를 불러오는 중" /> : null;
  }

  const atPoint = point ? pins.items.filter((p) => pointKey(p) === point) : [];

  return (
    <>
      <div className={styles.listHead} ref={top}>
        <h2>
          {atPoint.length ? "같은 위치의 회사" : "지도 안의 회사"} <span className="num">{items.length}</span>곳
        </h2>
        <div className={styles.listOpts}>
          <label>
            <span className="sr-only">정렬</span>
            <select value={sort} onChange={(e) => { setListSort(e.target.value as ListSort); reset(); }}>
              {(Object.keys(SORTS) as ListSort[]).map((k) => <option key={k} value={k}>{SORTS[k].label}</option>)}
            </select>
          </label>
          <label>
            <span className="sr-only">한 페이지에 보일 회사 수</span>
            <select value={size} onChange={(e) => { setListSize(Number(e.target.value) as PageSize); reset(); }}>
              {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}곳씩</option>)}
            </select>
          </label>
        </div>
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
          {shown.map((p) => (
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
      {pages > 1 && <Pager page={current} pages={pages} size={size} onGo={go} total={items.length} />}
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

/** 페이지 번호: 처음 · 끝과 지금 페이지 앞뒤 2개, 사이가 비면 "…" */
function Pager({ page, pages, size, total, onGo }: {
  page: number; pages: number; size: number; total: number; onGo: (n: number) => void;
}) {
  const nums = [...new Set([1, page - 2, page - 1, page, page + 1, page + 2, pages])]
    .filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
  const from = (page - 1) * size + 1, to = Math.min(page * size, total);
  return (
    <nav className={styles.pager} aria-label="목록 페이지">
      <span className="small muted num">{from}–{to} / {total}</span>
      <div>
        <button type="button" onClick={() => onGo(page - 1)} disabled={page === 1} aria-label="이전 페이지">‹</button>
        {nums.map((n, i) => (
          <span key={n}>
            {i > 0 && n - nums[i - 1] > 1 && <span className="muted" aria-hidden="true">…</span>}
            <button type="button" onClick={() => onGo(n)} aria-current={n === page ? "page" : undefined}
              aria-label={`${n}페이지`}>{n}</button>
          </span>
        ))}
        <button type="button" onClick={() => onGo(page + 1)} disabled={page === pages} aria-label="다음 페이지">›</button>
      </div>
    </nav>
  );
}
