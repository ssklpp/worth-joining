"use client";

// 재무 표(FR-COMP-08). DART와 연결된 회사만 표가 있고 연결 방식을 함께 쓴다
import { ErrorBox, Loading } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { formatAmount, formatPct } from "@/lib/format";
import styles from "./company.module.css";

function linkText(f: Schemas["CompanyFinancials"]) {
  if (f.flags.includes("name_matched")) return "회사 이름으로 연결했습니다. 다른 회사일 수 있습니다.";
  if (f.dart?.match_type === "fuzzy") return "회사 이름(영문 표기 포함)이 일치해 연결했습니다.";
  return "사업자번호와 회사 이름이 모두 일치해 연결했습니다.";
}

export function FinancialSection({ id }: { id: number }) {
  const state = useApi<Schemas["CompanyFinancials"]>(`/companies/${id}/financials`);

  return (
    <section className={styles.block} aria-labelledby="fin-title">
      <h2 id="fin-title">재무</h2>
      {state.status === "loading" && <Loading height={160} />}
      {state.status === "error" && <ErrorBox error={state.error} retry={state.retry} />}
      {state.status === "ok" && <FinancialBody f={state.data} />}
    </section>
  );
}

function FinancialBody({ f }: { f: Schemas["CompanyFinancials"] }) {
  if (!f.dart) {
    return <p className="small muted">DART 공시 대상이 아니거나 연결된 공시가 없어 재무 정보가 없습니다.</p>;
  }
  const matched = f.flags.includes("name_matched");
  return (
    <>
      <p className="small muted">
        DART {f.dart.corp_name} 사업보고서 기준입니다(연결재무제표, 없으면 별도).{" "}
        {!matched && linkText(f)}
      </p>
      {matched && <p className="note">{linkText(f)}</p>}
      {f.rows.length ? (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">연도</th><th scope="col">매출</th><th scope="col">영업이익</th>
                <th scope="col">순이익</th><th scope="col">부채비율</th>
              </tr>
            </thead>
            <tbody>
              {f.rows.map((r) => (
                <tr key={r.year}>
                  <td>{r.year}</td>
                  <td>{formatAmount(r.revenue)}</td>
                  <td>{formatAmount(r.operating_income)}</td>
                  <td>{formatAmount(r.net_income)}</td>
                  <td>{r.debt_ratio === null ? "–" : formatPct(r.debt_ratio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="small muted">연결된 회사이지만 DART에 사업보고서 주요계정이 없습니다.</p>
      )}
    </>
  );
}
