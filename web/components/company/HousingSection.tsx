"use client";

// 회사 근처 주거비(docs/03 6장 확장 구획, SPEC 9장, decisions/007): 기간 버튼 → 역 행(최대 3) → 부담률 막대.
// 부담률 = 역 원룸 환산 월세 ÷ 추정 월급. 추정 월급이 하한이라 부담률은 실제보다 높게 나올 수 있다
import { useState } from "react";
import { ErrorBox, Loading } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { formatPct, formatYm } from "@/lib/format";
import styles from "./company.module.css";

type Months = 6 | 12 | 24;
type Station = Schemas["NearStation"];

const AXIS_MAX = 0.5; // 부담률 막대 축: 0% ~ 월급의 50%

const man = (won: number | null | undefined) =>
  won === null || won === undefined ? "–" : `${Math.round(won / 10_000).toLocaleString("ko-KR")}만`;

/** 만원 단위 → "1억 8,000만" */
function eok(manwon: number | null | undefined) {
  if (manwon === null || manwon === undefined) return "–";
  const e = Math.floor(manwon / 10_000), r = manwon % 10_000;
  return [e ? `${e}억` : "", r ? `${r.toLocaleString("ko-KR")}만` : ""].filter(Boolean).join(" ") || "0";
}

const pos = (v: number) => Math.min(100, Math.max(0, (v / AXIS_MAX) * 100));

export function HousingSection({ id }: { id: number }) {
  const [months, setMonths] = useState<Months>(12);
  const state = useApi<Schemas["CompanyHousing"]>(`/companies/${id}/housing?months=${months}`);

  return (
    <section className={styles.block} aria-labelledby="housing-title">
      <div className={styles.head}>
        <h2 id="housing-title">회사 근처 주거비</h2>
        <p className="small muted">
          회사에서 1km 안의 역입니다. 역에서 500m 안, 전용 33㎡ 이하 연립다세대와 오피스텔의 신고된 계약만 셉니다.
        </p>
      </div>
      <div className={styles.seg} role="radiogroup" aria-label="계약 기간">
        {([6, 12, 24] as Months[]).map((m) => (
          <button key={m} type="button" role="radio" aria-checked={months === m} onClick={() => setMonths(m)}>
            최근 {m}개월
          </button>
        ))}
      </div>
      {state.status === "loading" && <Loading height={220} />}
      {state.status === "error" && <ErrorBox error={state.error} retry={state.retry} />}
      {state.status === "ok" && <HousingBody h={state.data} months={months} />}
    </section>
  );
}

function HousingBody({ h, months }: { h: Schemas["CompanyHousing"]; months: Months }) {
  const approx = h.flags.includes("approx_location");
  return (
    <>
      {approx && (
        <p className="note">회사 위치가 도로나 동 중심으로 표시한 대략적인 위치라 근처 역과 거리는 참고용입니다.</p>
      )}
      {h.monthly_pay_est ? (
        <p className="small">
          추정 월급(세전) <b className="num">{man(h.monthly_pay_est)} 원 이상</b>으로 나눈 부담률입니다. 실제 월급이 더
          높으면 부담률은 낮아집니다.
        </p>
      ) : (
        <p className="small muted">추정 연봉이 없어 부담률은 계산하지 않았습니다.</p>
      )}
      {h.stations.length ? (
        <>
          <div className={styles.legend} aria-hidden="true">
            <span><i className={styles.swSoft} />시세 하위 25% ~ 상위 25%</span>
            <span><i className={styles.swPen} />중간값</span>
          </div>
          <ul className={styles.stations}>
            {h.stations.map((s) => <StationRow key={s.station_id} s={s} months={months} />)}
          </ul>
        </>
      ) : (
        <p className="small">회사에서 1km 안에 지하철역이 없습니다.</p>
      )}
      <p className="small muted">
        환산 월세는 월세에 보증금을 전월세전환율(한국부동산원, 서울 연립다세대)로 바꾼 금액을 더한 값입니다. 신고된 계약
        기준({formatYm(h.rent_as_of)}까지)이라 지금 매물 가격과 다를 수 있습니다.
      </p>
    </>
  );
}

function StationRow({ s, months }: { s: Station; months: Months }) {
  const r = s.rent;
  const b = s.burden;
  return (
    <li className={styles.st}>
      <div className={styles.stName}>
        <b>{s.name}</b>
        <span>{s.lines.join(", ")}, 회사에서 {s.distance_m.toLocaleString("ko-KR")}m</span>
      </div>
      {r && r.monthly_median !== null ? (
        <div className={styles.stRent}>
          <strong className="num">월 {man(r.monthly_median)} 원</strong>
          <span className="num">{man(r.monthly_p25)} ~ {man(r.monthly_p75)}, 계약 {r.n_monthly.toLocaleString("ko-KR")}건</span>
          <span className="num">
            보증금 {eok(r.deposit_median_man)}, 월세 {r.rent_median_man ?? "–"}만
            {r.jeonse_median_man !== null && `, 전세 ${eok(r.jeonse_median_man)}`}
          </span>
        </div>
      ) : (
        <div className={styles.stRent}><span>역 500m 안 원룸 월세 계약이 없습니다</span></div>
      )}
      {b && b.low !== null && b.mid !== null && b.high !== null && (
        <div className={styles.stBurden} role="img"
          aria-label={`주거비 부담률 ${formatPct(b.low)}에서 ${formatPct(b.high)}, 중간 ${formatPct(b.mid)}`}>
          <p>월급의 <b>{Math.round(b.low * 100)} ~ {Math.round(b.high * 100)}%</b> (중간 {Math.round(b.mid * 100)}%)</p>
          <div className={styles.track}>
            <i className={styles.base} />
            <i className={styles.soft} style={{ left: `${pos(b.low)}%`, width: `${pos(b.high) - pos(b.low)}%` }} />
            <i className={styles.marker} style={{ left: `${pos(b.mid)}%` }} />
          </div>
          <div className={styles.axis}><span>0%</span><span>월급의 50%</span></div>
        </div>
      )}
      {s.flags.includes("period_extended_to_24m") && (
        <p className="note">최근 {months}개월 계약이 20건보다 적어 최근 24개월로 넓혀 계산했습니다.</p>
      )}
      {s.flags.includes("small_sample") && (
        <p className="note">24개월 계약도 20건보다 적어 시세가 크게 흔들릴 수 있습니다.</p>
      )}
    </li>
  );
}
