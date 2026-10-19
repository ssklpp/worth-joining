"use client";

// 결과표 3행: 성장 · 안정 · 연봉(decisions/005, docs/03 4 · 7장)
import { useApi, type Schemas } from "@/lib/api";
import { formatPct, formatWon } from "@/lib/format";
import { RangeBar } from "./RangeBar";
import styles from "./company.module.css";

type Detail = Schemas["CompanyDetail"];
type Dist = Schemas["Distribution"];

// 축 범위는 지표별로 고정한다(docs/03 4장). 축 밖의 값은 끝에 붙고 측정값 글자로 실제 값을 보인다
const AXES = {
  growth: { lo: -0.3, hi: 0.4, labels: ["-30%", "+40%"] as [string, string] },
  quit: { lo: 0, hi: 0.6, labels: ["0% (적게 떠남)", "60%"] as [string, string] },
  salary: { lo: 20_000_000, hi: 80_000_000, labels: ["2,000만", "8,000만"] as [string, string] },
};

function top(pct: number | null | undefined) {
  return pct === null || pct === undefined ? "" : `상위 ${Math.max(1, Math.round(100 - pct))}%`;
}

function growthVerdict(g: number) {
  if (g > 0.1) return "빠르게 늘고 있음";
  if (g > 0.02) return "늘고 있음";
  if (g > -0.02) return "거의 그대로";
  return "줄고 있음";
}

function rankVerdict(pct: number, high: string, mid: string, low: string) {
  return pct >= 60 ? high : pct >= 40 ? mid : low;
}

function bandText(d: Dist | null, fmt: (v: number) => string) {
  return d && d.p25 !== null && d.p75 !== null ? `업종 중간 50%는 ${fmt(d.p25)}에서 ${fmt(d.p75)}` : "업종 비교 없음";
}

function useDist(code: string | null, metric: "growth" | "quit" | "salary") {
  const state = useApi<Dist>(code ? `/industries/${code}/distribution?metric=${metric}` : null);
  return state.status === "ok" ? state.data : null;
}

export function HealthSheet({ c }: { c: Detail }) {
  const code = c.industry?.code && c.industry.code !== "999999" ? c.industry.code : null;
  const dGrowth = useDist(code, "growth");
  const dQuit = useDist(code, "quit");
  const dSalary = useDist(code, "salary");

  const small = c.flags.includes("small_sample");
  const lowerBound = c.flags.includes("salary_is_lower_bound");
  const p = c.percentiles;
  const n = dSalary?.n ?? dQuit?.n;
  const pct = (v: number) => formatPct(v, true);

  return (
    <section className={styles.sheet} aria-labelledby="sheet-title">
      <div className={styles.head}>
        <h2 id="sheet-title">회사 체력</h2>
        <p className="small muted">
          {code
            ? `같은 업종${n ? ` ${n.toLocaleString("ko-KR")}곳` : ""}과 비교했습니다. 가입자 10명 미만 회사는 업종 비교에서 뺍니다.`
            : "업종 분류가 없어 업종과 비교하지 않았습니다."}
        </p>
      </div>
      <div className={styles.legend} aria-hidden="true">
        {code && <span><i className={styles.swBand} />업종 중간 50%</span>}
        {code && <span><i className={styles.swMedian} />업종 중간값</span>}
        <span><i className={styles.swPen} />이 회사</span>
        {lowerBound && <span><i className={styles.swTail} />더 높을 수 있음</span>}
      </div>
      {small && (
        <p className="note">가입자가 10명 미만이라 비율이 크게 흔들릴 수 있습니다. 판정은 참고용으로만 보세요.</p>
      )}

      <div className={styles.row}>
        <span className={styles.name}>성장</span>
        <div className={styles.value}>
          <strong>{c.growth_12m === null || c.growth_12m === undefined ? "계산 안 함" : pct(c.growth_12m)}</strong>
          <span>12개월 전보다 가입자 증감</span>
        </div>
        {c.growth_12m !== null && c.growth_12m !== undefined ? (
          <RangeBar {...AXES.growth} band={dGrowth} value={c.growth_12m} hollow={small}
            label={`${bandText(dGrowth, pct)}, 이 회사 ${pct(c.growth_12m)}`} />
        ) : <div className={styles.pos} />}
        <div className={styles.verdict}>
          {c.growth_12m !== null && c.growth_12m !== undefined && <b>{growthVerdict(c.growth_12m)}</b>}
          <span>{small ? "참고용" : top(p?.growth)}</span>
        </div>
        {c.flags.includes("short_history") && (
          <p className="note">12개월 전 자료가 없어 성장률을 계산하지 않았습니다.</p>
        )}
      </div>

      <div className={styles.row}>
        <span className={styles.name}>안정</span>
        <div className={styles.value}>
          <strong>{formatPct(c.quit_rate_12m)}</strong>
          <span>최근 12개월 퇴사율</span>
        </div>
        <RangeBar {...AXES.quit} band={dQuit} value={c.quit_rate_12m ?? null} hollow={small}
          label={`${bandText(dQuit, (v) => formatPct(v))}, 이 회사 ${formatPct(c.quit_rate_12m)}`} />
        <div className={styles.verdict}>
          {!small && p?.stability !== null && p?.stability !== undefined && (
            <b>{rankVerdict(p.stability, "퇴사가 적은 편", "업종 평균 수준", "퇴사가 많은 편")}</b>
          )}
          <span>{small ? "참고용" : p?.stability != null ? `퇴사 적은 순 ${top(p.stability)}` : ""}</span>
        </div>
      </div>

      <div className={styles.row}>
        <span className={styles.name}>연봉</span>
        <div className={styles.value}>
          <strong>{c.avg_salary_est == null ? "–" : `≥ ${formatWon(c.avg_salary_est)}`}</strong>
          <span>추정 평균 연봉, 세전</span>
        </div>
        <RangeBar {...AXES.salary} band={dSalary} value={c.avg_salary_est ?? null} hollow={small} tail={lowerBound}
          label={`${bandText(dSalary, formatWon)}, 이 회사 ${formatWon(c.avg_salary_est)} 이상`} />
        <div className={styles.verdict}>
          {!small && p?.salary !== null && p?.salary !== undefined && (
            <b>{rankVerdict(p.salary, "업종 중간보다 높음", "업종 중간 수준", "업종 중간보다 낮음")}</b>
          )}
          <span>{small ? "참고용" : top(p?.salary)}</span>
        </div>
        {lowerBound && (
          <p className="note">
            국민연금 소득 상한 때문에 실제보다 낮게 나올 수 있습니다. 회사 전체 평균이며 개인이나 직무별 연봉이 아닙니다.
          </p>
        )}
      </div>
    </section>
  );
}
