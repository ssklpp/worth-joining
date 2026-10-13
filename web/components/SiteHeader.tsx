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
