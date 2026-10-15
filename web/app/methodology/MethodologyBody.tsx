"use client";

// 계산식 · 한계 · 출처 · 데이터 기간. 문구는 API(app/services/methodology.py)에만 두고 화면은 그리기만 한다
import { ErrorBox, Loading } from "@/components/Status";
import { useApi, type Schemas } from "@/lib/api";
import { formatYm } from "@/lib/format";
import styles from "./methodology.module.css";

export function MethodologyBody() {
  const state = useApi<Schemas["Methodology"]>("/meta/methodology");
  if (state.status === "loading") return <Loading height={480} />;
  if (state.status === "error") return <ErrorBox error={state.error} retry={state.retry} />;
  const m = state.data;

  return (
    <div className="prose">
      <p>
        자료 기간: <span className="num">{formatYm(m.period_from)}</span> ~{" "}
        <span className="num">{formatYm(m.as_of)}</span>
      </p>

      <section className={styles.section}>
        <h2>계산식</h2>
        <dl className={styles.formulas}>
          {m.formulas.map((f) => (
            <div key={f.metric}>
              <dt>{f.metric}</dt>
              <dd>
                <p>{f.formula}</p>
                {f.note && <p className="small muted">{f.note}</p>}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className={styles.section}>
        <h2>한계</h2>
        <ul>
          {m.limitations.map((text) => <li key={text}>{text}</li>)}
        </ul>
      </section>

      <section className={styles.section}>
        <h2>출처</h2>
        <ul>
          {m.sources.map((s) => (
            <li key={s.name}>
              <a href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</a>{" "}
              <span className="muted">({s.provider})</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
