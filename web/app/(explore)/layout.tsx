import { Suspense } from "react";
import { ExploreProvider } from "./ExploreContext";
import { MapPane } from "./MapPane";
import { Panel } from "./Panel";
import { Toolbar } from "./Toolbar";
import styles from "./explore.module.css";

// 지도 메인 화면(decisions/006, docs/03 5장). 이 레이아웃은 /, /companies/[id], /compare 사이를
// 옮겨도 다시 그려지지 않으므로 지도는 한 번만 불러오고, 각 page는 왼쪽 패널 내용만 그린다
export default function ExploreLayout({ children }: { children: React.ReactNode }) {
  return (
    <ExploreProvider>
      <div className={styles.app}>
        <Suspense fallback={<div className={styles.toolbar} />}>
          <Toolbar />
        </Suspense>
        <div className={styles.body}>
          <Panel>{children}</Panel>
          <MapPane />
        </div>
      </div>
    </ExploreProvider>
  );
}
