"use client";

// 비교: 12개월 전 = 100 가입자 지수 그래프 + 회사별 표(SPEC 9장 비교 패널, docs/03 8장).
// /compare 화면과 나중의 지도 비교 패널이 같이 쓴다.
import Link from "next/link";
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Estimate } from "@/components/Estimate";
import { ErrorBox, Loading } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { useCompare } from "@/lib/compare";
import { formatCount, formatPct, formatWon, formatYm, industryLabel } from "@/lib/format";
import styles from "./compare.module.css";

type Item = Schemas["CompareItem"];

// 색만으로 구분하지 않게 선 모양을 함께 쓴다(docs/03 8장)
const LINES = [
  { stroke: "var(--pen)", dash: undefined, label: "실선" },
  { stroke: "var(--ink)", dash: "8 4", label: "긴 점선" },
  { stroke: "var(--muted)", dash: "2 3", label: "짧은 점선" },
];

const label = (ym: number) => `${String(Math.floor(ym / 100)).slice(2)}.${String(ym % 100).padStart(2, "0")}`;

export function CompareView() {
  const compare = useCompare();
  const ids = compare.items.map((i) => i.id).join(",");
  const state = useApi<Schemas["CompareResult"]>(ids ? `/compare?ids=${ids}` : null);

  if (!compare.items.length) {
    return (
      <p>
        비교하려면 회사를 2곳 이상 담아 주세요. 검색 결과나 회사 상세에서 &ldquo;비교에 담기&rdquo;를 누르면 됩니다.{" "}
        <Link href="/">회사 검색하기</Link>
      </p>
    );
  }
  if (state.status === "loading") return <Loading height={420} />;
  if (state.status === "error") {
    // 저장해 둔 회사가 더는 없으면(404) 비교함을 비우도록 안내한다
    return (
      <div className={styles.block}>
        <ErrorBox error={state.error} retry={state.retry} />
        <button type="button" className="button quiet" onClick={compare.clear}>비교함 비우기</button>
      </div>
    );
  }

  const items = state.data.items;
  return (
    <div className={styles.block}>
      {items.length < 2 && <p className="note">한 곳만 담겨 있습니다. 비교하려면 한 곳 이상 더 담아 주세요.</p>}
      <IndexChart items={items} />
      <CompareTable items={items} onRemove={compare.remove} />
      <p className="small muted">
        지수는 12개월 전 가입자를 100으로 둔 값입니다. {formatYm(state.data.as_of)} 국민연금 자료 기준입니다.
      </p>
    </div>
  );
}

function IndexChart({ items }: { items: Item[] }) {
  const months = [...new Set(items.flatMap((i) => i.index_series.map((p) => p.ym)))].sort((a, b) => a - b);
  const data = months.map((ym) => {
    const row: Record<string, number | string | null> = { ym: label(ym) };
    items.forEach((it) => { row[`c${it.company_id}`] = it.index_series.find((p) => p.ym === ym)?.idx ?? null; });
    return row;
  });
  const noIndex = items.filter((i) => i.index_series.every((p) => p.idx === null));

  return (
    <section className={styles.block} aria-labelledby="idx-title">
      <h2 id="idx-title">가입자 지수</h2>
      <div className={styles.chart}>
        <div className={styles.chartInner} role="img"
          aria-label={`12개월 전 = 100 가입자 지수: ${items.map((i) => {
            const last = i.index_series.at(-1)?.idx;
            return `${i.name} ${last ?? "계산 안 함"}`;
          }).join(", ")}`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 12, right: 24, bottom: 4, left: 4 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="ym" tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false}
                axisLine={{ stroke: "var(--rule)" }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} width={40}
                domain={["auto", "auto"]} />
              <ReferenceLine y={100} stroke="var(--muted)" strokeDasharray="3 3" />
              <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--rule)", fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {items.map((it, n) => (
                <Line key={it.company_id} type="linear" dataKey={`c${it.company_id}`} name={it.name}
                  stroke={LINES[n].stroke} strokeDasharray={LINES[n].dash} strokeWidth={2.5}
                  dot={false} connectNulls={false} isAnimationActive={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
      {noIndex.length > 0 && (
        <p className="note">
          {noIndex.map((i) => i.name).join(", ")}: 12개월 전 자료가 없어 지수를 계산하지 않았습니다.
        </p>
      )}
    </section>
  );
}

function CompareTable({ items, onRemove }: { items: Item[]; onRemove: (id: number) => void }) {
  const cell = (it: Item, fn: (i: Item) => React.ReactNode) =>
    it.status === "stale" ? <span className="muted">최근 자료 없음</span> : fn(it);
  const rows: [string, (i: Item) => React.ReactNode][] = [
    ["지역", (i) => i.region?.sigungu ?? "–"],
    ["업종", (i) => (i.industry ? industryLabel(i.industry) : "–")],
    ["가입자", (i) => formatCount(i.members)],
    ["12개월 증감", (i) => (i.growth_12m == null ? "계산 안 함" : formatPct(i.growth_12m, true))],
    ["연간 퇴사율", (i) => formatPct(i.quit_rate_12m)],
    ["연봉", (i) => (i.avg_salary_est == null ? "–" : `≥ ${formatWon(i.avg_salary_est)}`)],
  ];

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">항목</span></th>
            {items.map((it, n) => (
              <th scope="col" key={it.company_id}>
                <Link href={`/companies/${it.company_id}`}>{it.name}</Link>
                <span className={styles.lineKey}>{LINES[n].label}</span>
                {it.flags.includes("small_sample") && <span className={styles.lineKey}>가입자 10명 미만</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, fn]) => (
            <tr key={name}>
              <th scope="row">{name}{name === "연봉" && <> <Estimate /></>}</th>
              {items.map((it) => <td key={it.company_id}>{cell(it, fn)}</td>)}
            </tr>
          ))}
          <tr>
            <th scope="row"><span className="sr-only">빼기</span></th>
            {items.map((it) => (
              <td key={it.company_id}>
                <button type="button" className="button quiet" onClick={() => onRemove(it.company_id)}>
                  비교에서 빼기
                </button>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
