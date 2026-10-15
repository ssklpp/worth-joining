"use client";

// 역 시세(SPEC 9장, FR-HOUS-01 · 02 · 04, decisions/007 9번): 기간 버튼 → 월세 · 전세 분포 → 최근 24개월 추이.
// 지도는 역 위치로 옮긴다(회사 id와 겹치지 않게 음수 id로 select)
import Link from "next/link";
import { useEffect, useState } from "react";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { eok, man } from "@/components/company/HousingSection";
import styles from "@/components/company/company.module.css";
import { CompareButton } from "@/components/CompareButton";
import { ErrorBox, Loading } from "@/components/Status";
import { ApiError, useApi, type Schemas } from "@/lib/api";
import { useStationCompare } from "@/lib/compare";
import { formatPct, formatYm, stationLabel } from "@/lib/format";
import { useExplore } from "../../ExploreContext";

type Months = 6 | 12 | 24;
type Detail = Schemas["StationDetail"];

const label = (ym: number) => `${String(Math.floor(ym / 100)).slice(2)}.${String(ym % 100).padStart(2, "0")}`;
const back = (ym: number, n: number) => {
  const total = Math.floor(ym / 100) * 12 + (ym % 100) - 1 - n;
  return Math.floor(total / 12) * 100 + (total % 12) + 1;
};

export function StationPage({ id }: { id: number | null }) {
  const [months, setMonths] = useState<Months>(12);
  const state = useApi<Detail>(id ? `/stations/${id}/rent?months=${months}` : null);
  // 기간을 바꾸는 동안에도 앞 결과를 보여 줘 화면과 지도가 흔들리지 않게 한다
  const [kept, setKept] = useState<Detail | null>(null);
  useEffect(() => {
    if (state.status === "ok") setKept(state.data);
  }, [state]);
  const d = kept?.station_id === id ? kept : null;

  const { select } = useExplore();
  const stationBox = useStationCompare();
  const name = d?.name, lat = d?.lat, lon = d?.lon;
  useEffect(() => {
    if (!id || !name || lat === undefined || lon === undefined) return;
    document.title = `${stationLabel(name)} 시세 | 다닐만한가`;
    select({ id: -id, name: stationLabel(name), lat, lon, approx: false });
    return () => select(null);
  }, [id, name, lat, lon, select]);

  if (id === null) return <NotFound />;
  if (state.status === "error") {
    if (state.error instanceof ApiError && (state.error.status === 404 || state.error.status === 422)) {
      return <NotFound />;
    }
    return <ErrorBox error={state.error} retry={state.retry} />;
  }

  return (
    <>
      <section className={styles.block}>
        <h1>{d ? stationLabel(d.name) : "역 시세"}</h1>
        {d && <p className="small muted">{d.lines.join(", ")}</p>}
        {d && id && (
          <div className={styles.actions}>
            <CompareButton id={id} name={stationLabel(d.name)} box={stationBox} unit="개 역" />
          </div>
        )}
        <p className="small muted">
          역에서 500m 안, 전용 33㎡ 이하 연립다세대와 오피스텔의 신고된 계약입니다
          {d && <>({formatYm(d.as_of)}까지)</>}. 지금 매물 가격과 다를 수 있습니다.
        </p>
      </section>
      <section className={styles.block} aria-labelledby="dist-title">
        <div className={styles.head}>
          <h2 id="dist-title">원룸 시세</h2>
        </div>
        <div className={styles.seg} role="radiogroup" aria-label="계약 기간">
          {([6, 12, 24] as Months[]).map((m) => (
            <button key={m} type="button" role="radio" aria-checked={months === m} onClick={() => setMonths(m)}>
              최근 {m}개월
            </button>
          ))}
        </div>
        {d ? <Distribution d={d} months={months} /> : <Loading height={160} />}
      </section>
      <section className={styles.block} aria-labelledby="st-trend-title">
        <div className={styles.head}>
          <h2 id="st-trend-title">최근 24개월 추이</h2>
          <p className="small muted">환산 월세 중간값(선)과 하위 25% ~ 상위 25%(띠)입니다. 기간 버튼과 관계없이 24개월입니다.</p>
        </div>
        {d ? <TrendChart d={d} /> : <Loading height={240} />}
      </section>
    </>
  );
}

function Distribution({ d, months }: { d: Detail; months: Months }) {
  const r = d.rent;
  if (!r) return <p className="small">역 500m 안 원룸 계약이 없습니다.</p>;
  return (
    <>
      <dl className={styles.facts}>
        <div>
          <dt>환산 월세 중간값</dt>
          <dd className="num">{r.monthly_median === null ? "–" : `월 ${man(r.monthly_median)} 원`}</dd>
        </div>
        <div><dt>하위 25% ~ 상위 25%</dt><dd className="num">{man(r.monthly_p25)} ~ {man(r.monthly_p75)}</dd></div>
        <div>
          <dt>보증금 · 월세 중간값</dt>
          <dd className="num">{eok(r.deposit_median_man)} / {r.rent_median_man ?? "–"}만</dd>
        </div>
        <div><dt>월세 계약</dt><dd className="num">{r.n_monthly.toLocaleString("ko-KR")}건</dd></div>
        <div><dt>전세 중간값</dt><dd className="num">{eok(r.jeonse_median_man)}</dd></div>
        <div>
          <dt>전세 하위 25% ~ 상위 25%</dt>
          <dd className="num">{eok(r.jeonse_p25_man)} ~ {eok(r.jeonse_p75_man)}</dd>
        </div>
        <div><dt>전세 계약</dt><dd className="num">{r.n_jeonse.toLocaleString("ko-KR")}건</dd></div>
        <div><dt>전세 비중</dt><dd className="num">{formatPct(d.jeonse_share)}</dd></div>
      </dl>
      {d.flags.includes("period_extended_to_24m") && (
        <p className="note">최근 {months}개월 계약이 20건보다 적어 최근 24개월로 넓혀 계산했습니다.</p>
      )}
      {d.flags.includes("small_sample") && (
        <p className="note">24개월 계약도 20건보다 적어 시세가 크게 흔들릴 수 있습니다.</p>
      )}
      <p className="small muted">
        환산 월세는 월세에 보증금을 전월세전환율(한국부동산원, 서울 연립다세대)로 바꾼 금액을 더한 값입니다.
      </p>
    </>
  );
}

/** 구간(월 24개 · 분기 8개)을 모두 만들고 계약이 없는 구간은 null로 둬 선을 끊는다 */
function TrendChart({ d }: { d: Detail }) {
  if (!d.trend_grain || !d.as_of) return <p className="small muted">추이를 그릴 계약이 없습니다.</p>;
  const quarter = d.trend_grain === "quarter";
  const step = quarter ? 3 : 1;
  const byYm = new Map(d.trend.map((p) => [p.ym, p]));
  const data = Array.from({ length: 24 / step }, (_, i) => back(d.as_of!, (24 / step - 1 - i) * step)).map((ym) => {
    const p = byYm.get(ym);
    const ok = p && p.n_monthly > 0 && p.monthly_median !== null;
    return {
      ym: label(ym),
      median: ok ? p.monthly_median! / 10_000 : null,
      band: ok && p.monthly_p25 !== null && p.monthly_p75 !== null
        ? [p.monthly_p25 / 10_000, p.monthly_p75 / 10_000] : null,
      n: p?.n_monthly ?? 0,
    };
  });
  const shown = data.filter((x) => x.median !== null);
  const first = shown[0], last = shown.at(-1);

  return (
    <>
      {quarter && (
        <p className="note">계약이 적은 역이라 3개월씩 묶었습니다. 가로축은 각 구간의 마지막 달입니다.</p>
      )}
      <div className={styles.chart}>
        <div className={styles.chartInner} role="img"
          aria-label={first && last
            ? `${stationLabel(d.name)} 환산 월세 중간값 추이: ${first.ym} ${Math.round(first.median!)}만 원에서 ${last.ym} ${Math.round(last.median!)}만 원`
            : `${stationLabel(d.name)} 환산 월세 추이`}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 12, right: 24, bottom: 4, left: 4 }}>
              <CartesianGrid vertical={false} stroke="var(--rule)" />
              <XAxis dataKey="ym" tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false}
                axisLine={{ stroke: "var(--rule)" }} />
              <YAxis tick={{ fill: "var(--muted)", fontSize: 11 }} tickLine={false} axisLine={false} width={44}
                domain={["auto", "auto"]} tickFormatter={(v: number) => `${Math.round(v)}만`} />
              <Tooltip
                formatter={(v, key) => key === "band" && Array.isArray(v)
                  ? [`${Math.round(Number(v[0]))}만 ~ ${Math.round(Number(v[1]))}만 원`, "하위 25% ~ 상위 25%"]
                  : [`${Math.round(Number(v))}만 원`, "중간값"]}
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--rule)", fontSize: 12 }} />
              <Area type="linear" dataKey="band" stroke="none" fill="var(--pen-soft)" connectNulls={false}
                isAnimationActive={false} />
              <Line type="linear" dataKey="median" stroke="var(--pen)" strokeWidth={2.5} dot={quarter}
                connectNulls={false} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
      {data.some((x) => x.median === null) && (
        <p className="small muted">계약이 없는 {quarter ? "구간" : "달"}은 선을 끊어 표시합니다.</p>
      )}
    </>
  );
}

function NotFound() {
  return (
    <section className={styles.block}>
      <h1>역을 찾을 수 없습니다</h1>
      <p>주소가 잘못되었거나 서울 역 목록에 없는 역입니다.</p>
      <p><Link href="/">지도로 돌아가기</Link></p>
    </section>
  );
}
