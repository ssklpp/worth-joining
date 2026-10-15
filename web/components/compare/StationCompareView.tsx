"use client";

// 역 비교(역 비교함 최대 3개): 원룸 시세 표 + 24개월 환산 월세 중간값 추이를 겹쳐 그린다.
// API는 바꾸지 않고 역마다 /stations/{id}/rent를 부른다(최대 3번)
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { eok, man } from "@/components/company/HousingSection";
import { ErrorBox, Loading } from "@/components/Status";
import { getJson, type Schemas } from "@/lib/api";
import { useStationCompare } from "@/lib/compare";
import { formatPct, formatYm, stationLabel } from "@/lib/format";
import companyStyles from "@/components/company/company.module.css";
import styles from "./compare.module.css";

type Detail = Schemas["StationDetail"];
type Months = 6 | 12 | 24;

// 색만으로 구분하지 않게 선 모양을 함께 쓴다(회사 비교와 같은 규칙, docs/03 8장)
const LINES = [
  { stroke: "var(--pen)", dash: undefined, label: "실선" },
  { stroke: "var(--ink)", dash: "8 4", label: "긴 점선" },
  { stroke: "var(--muted)", dash: "2 3", label: "짧은 점선" },
];

const label = (ym: number) => `${String(Math.floor(ym / 100)).slice(2)}.${String(ym % 100).padStart(2, "0")}`;
const back = (ym: number, n: number) => {
  const total = Math.floor(ym / 100) * 12 + (ym % 100) - 1 - n;
  return Math.floor(total / 12) * 100 + (total % 12) + 1;
};

type State = { status: "loading" } | { status: "error"; error: Error } | { status: "ok"; data: Detail[] };

/** 담은 역들의 시세를 한꺼번에 부른다. 하나라도 실패하면 오류(다시 시도) */
function useStationDetails(ids: number[], months: Months) {
  const key = ids.join(",");
  const [state, setState] = useState<State>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);

  useEffect(() => {
    if (!key) return;
    const controller = new AbortController();
    setState({ status: "loading" });
    Promise.all(key.split(",").map((id) =>
      getJson<Detail>(`/stations/${id}/rent?months=${months}`, controller.signal)))
      .then((data) => setState({ status: "ok", data }))
      .catch((error) => {
        if (!controller.signal.aborted) setState({ status: "error", error });
      });
    return () => controller.abort();
  }, [key, months, attempt]);

  return { state, retry };
}

export function StationCompareView() {
  const box = useStationCompare();
  const [months, setMonths] = useState<Months>(12);
  const { state, retry } = useStationDetails(box.items.map((i) => i.id), months);

  if (!box.items.length) {
    return (
      <p>
        비교하려면 역을 2개 이상 담아 주세요. 지도에서 역을 누르거나 회사 상세의 근처 역을 연 뒤
        &ldquo;비교에 담기&rdquo;를 누르면 됩니다.
      </p>
    );
  }
  if (state.status === "loading") return <Loading height={420} />;
  if (state.status === "error") {
    return (
      <div className={styles.block}>
        <ErrorBox error={state.error} retry={retry} />
        <button type="button" className="button quiet" onClick={box.clear}>역 비교함 비우기</button>
      </div>
    );
  }

  const data = state.data;
  return (
    <div className={styles.block}>
      {data.length < 2 && <p className="note">한 곳만 담겨 있습니다. 비교하려면 역을 하나 더 담아 주세요.</p>}
      <div className={companyStyles.seg} role="radiogroup" aria-label="계약 기간">
        {([6, 12, 24] as Months[]).map((m) => (
          <button key={m} type="button" role="radio" aria-checked={months === m} onClick={() => setMonths(m)}>
            최근 {m}개월
          </button>
        ))}
      </div>
      <RentTable data={data} months={months} onRemove={box.remove} />
      <TrendChart data={data} />
      <p className="small muted">
        역에서 500m 안, 전용 33㎡ 이하 연립다세대 · 오피스텔의 신고된 계약입니다({formatYm(data[0].as_of)}까지).
        환산 월세는 보증금을 전월세전환율로 바꿔 월세에 더한 값입니다.
      </p>
    </div>
  );
}

function RentTable({ data, months, onRemove }: { data: Detail[]; months: Months; onRemove: (id: number) => void }) {
  const rows: [string, (d: Detail) => React.ReactNode][] = [
    ["노선", (d) => d.lines.join(", ")],
    ["환산 월세 중간값", (d) => (d.rent?.monthly_median == null ? "–" : `월 ${man(d.rent.monthly_median)} 원`)],
    ["하위 25% ~ 상위 25%", (d) => (d.rent ? `${man(d.rent.monthly_p25)} ~ ${man(d.rent.monthly_p75)}` : "–")],
    ["보증금 · 월세 중간값", (d) => (d.rent ? `${eok(d.rent.deposit_median_man)} / ${d.rent.rent_median_man ?? "–"}만` : "–")],
    ["월세 계약", (d) => (d.rent ? `${d.rent.n_monthly.toLocaleString("ko-KR")}건` : "–")],
    ["전세 중간값", (d) => (d.rent ? eok(d.rent.jeonse_median_man) : "–")],
    ["전세 비중", (d) => formatPct(d.jeonse_share)],
  ];
  const note = (d: Detail) =>
    d.flags.includes("small_sample") ? "24개월 계약도 20건 미만"
      : d.flags.includes("period_extended_to_24m") ? `${months}개월 계약이 적어 24개월로 넓힘` : null;

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col"><span className="sr-only">항목</span></th>
            {data.map((d, n) => (
              <th scope="col" key={d.station_id}>
                <Link href={`/stations/${d.station_id}`}>{stationLabel(d.name)}</Link>
                <span className={styles.lineKey}>{LINES[n].label}</span>
                {note(d) && <span className={styles.lineKey}>{note(d)}</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(([name, fn]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              {data.map((d) => <td key={d.station_id}>{fn(d)}</td>)}
            </tr>
          ))}
          <tr>
            <th scope="row"><span className="sr-only">빼기</span></th>
            {data.map((d) => (
              <td key={d.station_id}>
                <button type="button" className="button quiet" onClick={() => onRemove(d.station_id)}>
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

/** 24개월 가로축에 역마다 중간값 선. 분기 단위 역은 분기 끝 달에만 점이 있어 점끼리 잇는다 */
function TrendChart({ data }: { data: Detail[] }) {
  const end = Math.max(...data.map((d) => d.as_of ?? 0));
  if (!end) return null;
  const yms = Array.from({ length: 24 }, (_, i) => back(end, 23 - i));
  const byStation = data.map((d) => new Map(d.trend.map((p) => [p.ym, p])));
  const rows = yms.map((ym) => {
    const row: Record<string, string | number | null> = { ym: label(ym) };
    data.forEach((d, n) => {
      const p = byStation[n].get(ym);
      row[`s${d.station_id}`] = p && p.n_monthly > 0 && p.monthly_median !== null ? p.monthly_median / 10_000 : null;
    });
    return row;
  });

  return (
    <section className={styles.block} aria-labelledby="st-cmp-trend">
      <h2 id="st-cmp-trend">최근 24개월 환산 월세 중간값</h2>
      {data.some((d) => d.trend_grain === "quarter") && (
        <p className="small muted">
          계약이 적은 역({data.filter((d) => d.trend_grain === "quarter").map((d) => stationLabel(d.name)).join(", ")})은
          3개월씩 묶은 값이라 분기 끝 달에만 점이 있습니다.
        </p>
      )}
      <div className={styles.chart}>
        <div className={styles.chartInner} role="img"
          aria-label={`역별 환산 월세 중간값 추이: ${data.map((d) => {
            const last = d.trend.filter((p) => p.monthly_median !== null).at(-1);
            return `${stationLabel(d.name)} ${last ? `${Math.round(last.monthly_median! / 10_000)}만 원` : "자료 없음"}`;
          }).join(", ")}`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 12, right: 24, bottom: 4, left: 4 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="ym" tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false}
                axisLine={{ stroke: "var(--rule)" }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} width={44}
                domain={["auto", "auto"]} tickFormatter={(v: number) => `${Math.round(v)}만`} />
              <Tooltip formatter={(v) => `${Math.round(Number(v))}만 원`}
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--rule)", fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {data.map((d, n) => (
                <Line key={d.station_id} type="linear" dataKey={`s${d.station_id}`} name={stationLabel(d.name)}
                  stroke={LINES[n].stroke} strokeDasharray={LINES[n].dash} strokeWidth={2.5}
                  dot={d.trend_grain === "quarter"} connectNulls={d.trend_grain === "quarter"}
                  isAnimationActive={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
