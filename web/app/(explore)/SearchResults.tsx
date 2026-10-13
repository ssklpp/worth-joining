"use client";

// 검색 결과 패널(SPEC 9장 검색). 지도와 관계없이 전체 회사에서 찾으므로 위치 정보가 없는 회사도 나온다.
// 검색어는 URL(?q=), 업종은 위쪽 막대의 필터를 따른다
import Link from "next/link";
import { useState } from "react";
import { ErrorBox, Loading } from "@/components/Status";
import { getJson, useApi, type Schemas } from "@/lib/api";
import { CompanyItem } from "./CompanyItem";
import styles from "./search.module.css";

type Sort = "name" | "growth";
type Page = Schemas["CompanyList"];

function searchPath(q: string, industry: string, sort: Sort, cursor?: string) {
  const params = new URLSearchParams({ sort, limit: "20" });
  if (/^\d{6}$/.test(q)) params.set("biz_no6", q); // 숫자 6자리는 사업자번호 앞자리로 찾는다
  else if (q) params.set("q", q);
  if (industry) params.set("industry", industry);
  if (cursor) params.set("cursor", cursor);
  return `/companies?${params}`;
}

export function SearchResults({ q, industry }: { q: string; industry: string }) {
  const [sort, setSort] = useState<Sort>("name");
  return <Results key={sort} q={q} industry={industry} sort={sort} onSort={setSort} />;
}

function Results({ q, industry, sort, onSort }: {
  q: string; industry: string; sort: Sort; onSort: (s: Sort) => void;
}) {
  const first = useApi<Page>(searchPath(q, industry, sort));
  const [more, setMore] = useState<Page[]>([]);
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState(false);

  if (first.status === "loading") return <Loading height={320} label="검색 중" />;
  if (first.status === "error") return <ErrorBox error={first.error} retry={first.retry} />;

  const pages = [first.data, ...more];
  const items = pages.flatMap((p) => p.items);
  const cursor = pages[pages.length - 1].next_cursor;

  async function loadMore() {
    if (!cursor) return;
    setLoadingMore(true);
    setMoreError(false);
    try {
      const page = await getJson<Page>(searchPath(q, industry, sort, cursor));
      setMore((m) => [...m, page]);
    } catch {
      setMoreError(true);
    } finally {
      setLoadingMore(false);
    }
  }

  if (!items.length) {
    return (
      <div className={styles.empty} role="status">
        <p>&ldquo;{q || "선택한 업종"}&rdquo;와 일치하는 회사가 없습니다.</p>
        <p className="small muted">
          가입자 3명 미만 법인이나 10명 미만 개인사업장은 공개되지 않습니다. 사업자번호 앞 6자리로도
          찾아보세요.
        </p>
        <Link href="/" className="small">검색 지우고 지도 안의 회사 보기</Link>
      </div>
    );
  }

  return (
    <section className={styles.results} aria-label="검색 결과">
      <div className={styles.head}>
        <h2>검색 결과 <span className="num">{items.length}{cursor ? "+" : ""}</span>곳</h2>
        <label className="small">
          <span className="sr-only">정렬</span>
          <select className={styles.sort} value={sort} onChange={(e) => onSort(e.target.value as Sort)}>
            <option value="name">이름순</option>
            <option value="growth">12개월 증감 큰 순</option>
          </select>
        </label>
      </div>
      <ul className={styles.items}>
        {items.map((c) => <li key={c.company_id}><CompanyItem company={c} /></li>)}
      </ul>
      {moreError && <p className="small" role="alert">더 불러오지 못했습니다. 다시 시도해 주세요.</p>}
      {cursor && (
        <button type="button" className="button quiet" onClick={loadMore} disabled={loadingMore}>
          {loadingMore ? "불러오는 중" : "더 보기"}
        </button>
      )}
      <Link href="/" className="small">검색 지우고 지도 안의 회사 보기</Link>
    </section>
  );
}
