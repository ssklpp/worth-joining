"use client";

// 가입자 추이 그래프와 월별 입퇴사 표(docs/03 8장)
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorBox, Loading } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { formatCount, formatPct } from "@/lib/format";
import styles from "./company.module.css";

type Point = Schemas["TrendPoint"];

function nextYm(ym: number) {
  return ym % 100 === 12 ? (Math.floor(ym / 100) + 1) * 100 + 1 : ym + 1;
}

/** API는 자료가 있는 달만 준다. 기간 안의 모든 달을 채우고 없는 달은 null로 둬 선을 끊는다 */
export function fillMonths(points: Point[], lastYm: number | null): { ym: number; point: Point | null }[] {
  if (!points.length) return [];
  const byYm = new Map(points.map((p) => [p.ym, p]));
  const end = Math.max(lastYm ?? 0, points[points.length - 1].ym);
  const rows = [];
  for (let ym = points[0].ym; ym <= end; ym = nextYm(ym)) rows.push({ ym, point: byYm.get(ym) ?? null });
  return rows;
}

const label = (ym: number) => `${String(Math.floor(ym / 100)).slice(2)}.${String(ym % 100).padStart(2, "0")}`;

export function TrendSection({ id, name, asOf }: { id: number; name: string; asOf: number | null }) {
  const state = useApi<Schemas["CompanyTrend"]>(`/companies/${id}/trend`);

  return (
    <section className={styles.block} aria-labelledby="trend-title">
      <div className={styles.head}>
        <h2 id="trend-title">가입자 추이</h2>
        <p className="small muted">국민연금 가입자 수입니다. 자료가 없는 달은 선을 끊어 표시합니다.</p>
      </div>
      {state.status === "loading" && <Loading height={360} />}
      {state.status === "error" && <ErrorBox error={state.error} retry={state.retry} />}
      {state.status === "ok" && <TrendBody months={fillMonths(state.data.points, asOf)} name={name} />}
    </section>
  );
}

function TrendBody({ months, name }: { months: { ym: number; point: Point | null }[]; name: string }) {
  if (!months.length) return <p className="small muted">표시할 자료가 없습니다.</p>;
  const data = months.map(({ ym, point }) => ({ ym: label(ym), members: point?.members ?? null }));
  const lastIndex = data.findLastIndex((d) => d.members !== null);

  return (
    <>
      <div className={styles.chart}>
        <div className={styles.chartInner} role="img"
          aria-label={`${name} 가입자 추이, ${data[0].ym}부터 ${data[data.length - 1].ym}까지`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 24, right: 72, bottom: 4, left: 4 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="ym" tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false}
                axisLine={{ stroke: "var(--rule)" }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} width={56}
                allowDecimals={false} domain={["auto", "auto"]}
                tickFormatter={(v: number) => v.toLocaleString("ko-KR")} />
              <Tooltip formatter={(v) => [`${Number(v).toLocaleString("ko-KR")}명`, "가입자"]}
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--rule)", fontSize: 12 }} />
              <Line type="linear" dataKey="members" stroke="var(--pen)" strokeWidth={2.5} connectNulls={false}
                isAnimationActive={false}
                dot={(props) => {
                  const { cx, cy, index } = props as { cx: number; cy: number; index: number };
                  if (index !== lastIndex) return <g key={index} />;
                  return (
                    <g key={index}>
                      <circle cx={cx} cy={cy} r={5} fill="var(--pen)" />
                      <text x={cx + 8} y={cy - 8} fill="var(--ink)" fontSize={12} fontWeight={600}>
                        {data[index].members?.toLocaleString("ko-KR")}명
                      </text>
                    </g>
                  );
                }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h3>월별 입사와 퇴사</h3>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">월</th><th scope="col">가입자</th><th scope="col">입사</th>
              <th scope="col">퇴사</th><th scope="col">입사율</th><th scope="col">퇴사율</th>
            </tr>
          </thead>
          <tbody>
            {[...months].reverse().map(({ ym, point }) => (
              <tr key={ym}>
                <td>{`${Math.floor(ym / 100)}년 ${ym % 100}월`}</td>
                {point ? (
                  <>
                    <td>{formatCount(point.members)}</td>
                    <td>{formatCount(point.new)}</td>
                    <td>{formatCount(point.lost)}</td>
                    <td>{point.hire_rate === null ? "—" : formatPct(point.hire_rate)}</td>
                    <td>{point.quit_rate === null ? "—" : formatPct(point.quit_rate)}</td>
                  </>
                ) : (
                  <td className={styles.missing} colSpan={5}>이 달의 국민연금 자료가 없습니다</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small muted">
        입사율과 퇴사율은 전달 가입자 수로 나눈 값입니다. 전달 자료가 없으면 계산하지 않습니다(—).
      </p>
    </>
  );
}
