import Link from "next/link";
import { Estimate } from "@/components/Estimate";
import type { Schemas } from "@/lib/api";
import { formatCount, formatPct, formatWon, industryLabel } from "@/lib/format";
import styles from "./search.module.css";

// 결과 행: 회사명 + 시 · 구 + 업종명으로 동명 회사를 구분한다(SPEC Phase 6-4)
export function CompanyItem({ company: c }: { company: Schemas["CompanyListItem"] }) {
  return (
    <Link href={`/companies/${c.company_id}`} className={styles.item}>
      <span className={styles.name}>{c.name}</span>
      <span className={styles.sub}>
        <span>{c.region.sigungu ?? "지역 정보 없음"}</span>
        <span>{industryLabel(c.industry)}</span>
      </span>
      <span className={styles.metrics}>
        <span><i>가입자</i>{formatCount(c.members)}</span>
        <span>
          <i>12개월 증감</i>
          {c.growth_12m === null ? "계산 안 함" : formatPct(c.growth_12m, true)}
        </span>
        <span><i>연간 퇴사율</i>{formatPct(c.quit_rate_12m)}</span>
        <span>
          <i>연봉 <Estimate /></i>
          {c.avg_salary_est === null ? "–" : `≥ ${formatWon(c.avg_salary_est)}`}
        </span>
      </span>
    </Link>
  );
}
