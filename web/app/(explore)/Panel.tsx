"use client";

// 왼쪽 패널 틀: 목록 360px, 상세 · 비교 460px(docs/03 5장). 패널이 바뀌면 맨 위로 올리고,
// 좁은 화면에서는 패널로 스크롤한다. 상세 · 비교에서 Esc를 누르면 목록으로 돌아간다
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { useExplore } from "./ExploreContext";
import styles from "./explore.module.css";

export function Panel({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { listUrl } = useExplore();
  const ref = useRef<HTMLElement>(null);
  const isList = pathname === "/";

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = 0;
    if (!isList && window.matchMedia("(max-width: 760px)").matches) el.scrollIntoView();
  }, [pathname, isList]);

  useEffect(() => {
    if (isList) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !(e.target instanceof HTMLInputElement)) router.push(listUrl);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isList, listUrl, router]);

  return (
    <aside ref={ref} className={`${styles.panel} ${isList ? "" : styles.wide}`}
      aria-label={isList ? "회사 목록" : pathname.startsWith("/stations") ? "역 정보" : "회사 정보"}>
      <div className={styles.pane}>{children}</div>
    </aside>
  );
}

/** 상세 · 비교 패널 위의 "목록으로"(검색어가 있었으면 그 검색 결과로) */
export function BackToList() {
  const { listUrl } = useExplore();
  const router = useRouter();
  return (
    <button type="button" className={styles.back} onClick={() => router.push(listUrl)}>
      목록으로
    </button>
  );
}
