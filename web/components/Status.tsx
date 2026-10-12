// 데이터 영역의 로딩 · 오류 표시(docs/03 7장)
import type { ApiError } from "@/lib/api";
import styles from "./Status.module.css";

/** 구획 자리에 같은 높이의 빈 틀 */
export function Loading({ height = 120, label = "불러오는 중" }: { height?: number; label?: string }) {
  return (
    <div className={styles.skeleton} style={{ height }} role="status">
      <span className="sr-only">{label}</span>
    </div>
  );
}

/** 구획 자리에 안내와 다시 시도 버튼 */
export function ErrorBox({ error, retry }: { error: ApiError | Error; retry: () => void }) {
  return (
    <div className={styles.error} role="alert">
      <p>정보를 불러오지 못했습니다. 다시 시도해 주세요.</p>
      <p className="small muted">{error.message}</p>
      <button type="button" className="button quiet" onClick={retry}>다시 시도</button>
    </div>
  );
}
