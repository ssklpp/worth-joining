"use client";

// 검색 화면(SPEC 9장). 검색 조건은 URL(?q=&industry=&sort=)에 둬서 뒤로 가기 · 공유가 된다
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
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

export function Search() {
  const router = useRouter();
  const params = useSearchParams();
  const q = params.get("q")?.trim() ?? "";
  const industry = params.get("industry") ?? "";
  const sort: Sort = params.get("sort") === "growth" ? "growth" : "name";
  const hasQuery = Boolean(q || industry);

  const industries = useApi<Schemas["IndustryList"]>("/industries");
  const industryList = industries.status === "ok" ? industries.data.items : [];
  const industryName = industryList.find((i) => i.code === industry)?.name ?? "";

  const [text, setText] = useState(q);
  const [industryText, setIndustryText] = useState("");
  useEffect(() => setText(q), [q]);
  useEffect(() => setIndustryText(industryName), [industryName]);

  function go(next: { q?: string; industry?: string; sort?: Sort }) {
    const merged = { q, industry, sort, ...next };
    const search = new URLSearchParams();
    if (merged.q) search.set("q", merged.q);
    if (merged.industry) search.set("industry", merged.industry);
    if (merged.sort !== "name") search.set("sort", merged.sort);
    router.push(search.size ? `/?${search}` : "/");
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const typed = industryText.trim();
    const picked = industryList.find((i) => i.name === typed);
    go({ q: text.trim(), industry: typed ? (picked?.code ?? industry) : "" });
  }

  return (
    <div className={styles.search}>
      <form className={styles.form} onSubmit={submit} role="search">
        <h1 className={styles.title}>어떤 회사가 궁금하세요?</h1>
        <label className="sr-only" htmlFor="q">회사명 또는 사업자번호 앞 6자리</label>
        <div className={styles.bar}>
          <input id="q" className={styles.input} value={text} onChange={(e) => setText(e.target.value)}
            placeholder="회사명 또는 사업자번호 앞 6자리" autoComplete="off" maxLength={100} />
          <button type="submit" className="button">검색</button>
        </div>
        <div className={styles.filters}>
          <label htmlFor="industry">업종</label>
          <input id="industry" list="industry-list" className={styles.industry} value={industryText}
            onChange={(e) => setIndustryText(e.target.value)} placeholder="업종 이름으로 찾기"
            autoComplete="off" />
          <datalist id="industry-list">
            {industryList.filter((i) => i.code !== "999999").map((i) => <option key={i.code} value={i.name} />)}
          </datalist>
          {industry && (
            <button type="button" className="button quiet" onClick={() => go({ industry: "" })}>
              업종 지우기
            </button>
          )}
        </div>
      </form>

      {hasQuery ? (
        <Results key={`${q}|${industry}|${sort}`} q={q} industry={industry} sort={sort}
          onSort={(s) => go({ sort: s })} />
      ) : (
        <p className="muted">
          서울특별시 사업장의 국민연금 공개 자료로 인원 추이, 퇴사율, 추정 연봉을 보여 줍니다.
        </p>
      )}
    </div>
  );
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
      </div>
    );
  }

  return (
    <section className={styles.results} aria-label="검색 결과">
      <div className={styles.head}>
        <h2>회사 <span className="num">{items.length}{cursor ? "+" : ""}</span>곳</h2>
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
    </section>
  );
}
