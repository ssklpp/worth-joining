// 모든 화면 위쪽 머리글(SPEC 9장 공통): 서비스 이름 → 지도, 계산 방법, 비교함에 담은 수
import Link from "next/link";
import { CompareCount } from "./CompareCount";
import styles from "./SiteHeader.module.css";

export function SiteHeader() {
  return (
    <header className={styles.header}>
      <Link href="/" className={styles.brand}>다닐만한가</Link>
      <nav className={styles.nav} aria-label="주요 메뉴">
        <Link href="/methodology">계산 방법</Link>
        <CompareCount />
      </nav>
    </header>
  );
}
