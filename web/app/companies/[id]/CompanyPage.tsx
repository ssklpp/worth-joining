"use client";

// 회사 상세(SPEC 9장, docs/03 6장): 기본 정보 → 결과표 → 가입자 추이 → 월별 입퇴사 → 재무 → 읽는 법
import Link from "next/link";
import { useEffect } from "react";
import { FinancialSection } from "@/components/company/FinancialSection";
import { HealthSheet } from "@/components/company/HealthSheet";
import { TrendSection } from "@/components/company/TrendSection";
import styles from "@/components/company/company.module.css";
import { CompareButton } from "@/components/CompareButton";
import { ErrorBox, Loading } from "@/components/Status";
import { ApiError, useApi, type Schemas } from "@/lib/api";
import { formatCount, formatYm, industryLabel } from "@/lib/format";

const saraminUrl = (name: string) =>
  `https://www.saramin.co.kr/zf_user/search?searchword=${encodeURIComponent(name)}`;

export function CompanyPage({ id }: { id: number | null }) {
  const state = useApi<Schemas["CompanyDetail"]>(id ? `/companies/${id}` : null);
  const name = state.status === "ok" ? state.data.name : null;
  useEffect(() => {
    if (name) document.title = `${name} | 다닐만한가`;
  }, [name]);

  if (id === null) return <NotFound />;
  if (state.status === "loading") return <Loading height={480} />;
  if (state.status === "error") {
    if (state.error instanceof ApiError && (state.error.status === 404 || state.error.status === 422)) {
      return <NotFound />;
    }
    return <ErrorBox error={state.error} retry={state.retry} />;
  }

  const c = state.data;
  if (c.status === "stale") {
    return (
      <section className={styles.block}>
        <h1>{c.name}</h1>
        <p className="note">
          {formatYm(c.last_seen_ym)} 이후 국민연금 자료에 없는 회사입니다. 폐업했거나 국민연금 사업장에서 탈퇴했을 수
          있습니다.
        </p>
        <p><Link href="/">다른 회사 검색하기</Link></p>
      </section>
    );
  }

  return (
    <>
      <section className={styles.block}>
        <h1>{c.name}</h1>
        <dl className={styles.facts}>
          <div><dt>지역</dt><dd>{[c.region?.sido, c.region?.sigungu].filter(Boolean).join(" ") || "정보 없음"}</dd></div>
          <div><dt>업종</dt><dd>{c.industry ? industryLabel(c.industry) : "업종 분류 없음"}</dd></div>
          <div>
            <dt>형태</dt>
            <dd>{c.form_type === "individual" ? "개인사업장" : "법인"}, 사업장 {c.workplace_count ?? 1}곳</dd>
          </div>
          <div><dt>국민연금 가입자</dt><dd className="num">{formatCount(c.members)}</dd></div>
        </dl>
        <div className={styles.actions}>
          <a className="button" href={saraminUrl(c.name)} target="_blank" rel="noopener noreferrer">
            사람인에서 채용공고 보기
          </a>
          <CompareButton id={c.company_id} name={c.name} />
        </div>
      </section>

      <HealthSheet c={c} />
      <TrendSection id={c.company_id} name={c.name} asOf={c.as_of ?? null} />
      <FinancialSection id={c.company_id} />

      <section className={styles.block}>
        <h2>이 숫자를 읽을 때</h2>
        <p className="small">
          가입자, 입사, 퇴사는 국민연금 가입 기준이라 실제 직원 수와 다를 수 있습니다. 팀 분위기나 업무 강도처럼
          통계에 나오지 않는 정보는 알 수 없습니다. <Link href="/methodology">계산 방법 자세히 보기</Link>
        </p>
      </section>
    </>
  );
}

function NotFound() {
  return (
    <section className={styles.block}>
      <h1>회사를 찾을 수 없습니다</h1>
      <p>주소가 잘못되었거나 더 이상 제공하지 않는 회사입니다.</p>
      <p><Link href="/">회사 검색으로 돌아가기</Link></p>
    </section>
  );
}
