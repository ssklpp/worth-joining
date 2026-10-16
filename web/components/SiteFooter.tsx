"use client";

// 모든 화면 하단: 데이터 기준월 · 출처 · 면책 문구(SPEC 9장 공통)
import Link from "next/link";
import { useApi, type Schemas } from "@/lib/api";
import { formatYm } from "@/lib/format";
import styles from "./SiteFooter.module.css";

export function SiteFooter() {
  const health = useApi<Schemas["Health"]>("/health");
  const asOf = health.status === "ok" ? formatYm(health.data.latest_nps_ym) : "확인 중";

  return (
    <footer className={styles.footer}>
      <p>
        데이터 기준월 <span className="num">{health.status === "error" ? "확인하지 못함" : asOf}</span>
      </p>
      <p>
        출처: 국민연금공단 국민연금 가입 사업장 내역(공공데이터포털), 금융감독원 OpenDART, 서울특별시 부동산 전월세가
        정보, 국토교통부 실거래가 공개시스템, 한국부동산원 전월세전환율, 주소정보누리집.{" "}
        <Link href="/methodology">계산 방법과 한계</Link>
      </p>
      <p>
        공개 자료로 계산한 추정치이며 회사의 실제 인원 · 연봉과 다를 수 있습니다. 입사 결정의 유일한 근거로 쓰지 마세요.
      </p>
    </footer>
  );
}
