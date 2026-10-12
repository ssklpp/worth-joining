// 기준 범위 막대(docs/03 4장): 업종 p25 ~ p75 띠, 중간값 눈금, 회사 점을 같은 선형 축에 그린다
import styles from "./company.module.css";

type Band = { p25: number | null; p50: number | null; p75: number | null };

function pos(value: number, lo: number, hi: number) {
  return Math.min(100, Math.max(0, ((value - lo) / (hi - lo)) * 100)); // 축 밖은 끝에 붙인다
}

export function RangeBar({ lo, hi, labels, band, value, hollow = false, tail = false, label }: {
  lo: number;
  hi: number;
  labels: [string, string];
  band?: Band | null;
  value: number | null;
  hollow?: boolean; // 가입자 10명 미만: 속이 빈 점
  tail?: boolean; // 하한 추정: 점에서 오른쪽으로 점선
  label: string; // aria-label: 범위와 회사 값을 글로
}) {
  const hasBand = band && band.p25 !== null && band.p75 !== null;
  return (
    <div className={styles.pos} role="img" aria-label={label}>
      <div className={styles.track}>
        <i className={styles.base} />
        {hasBand && (
          <i className={styles.band} style={{
            left: `${pos(band.p25!, lo, hi)}%`,
            width: `${pos(band.p75!, lo, hi) - pos(band.p25!, lo, hi)}%`,
          }} />
        )}
        {band && band.p50 !== null && <i className={styles.median} style={{ left: `${pos(band.p50, lo, hi)}%` }} />}
        {value !== null && tail && (
          <i className={styles.tail} style={{ left: `${pos(value, lo, hi)}%`, width: `${Math.min(10, 100 - pos(value, lo, hi))}%` }} />
        )}
        {value !== null && (
          <i className={hollow ? `${styles.marker} ${styles.hollow}` : styles.marker}
            style={{ left: `${pos(value, lo, hi)}%` }} />
        )}
      </div>
      <div className={styles.axis}><span>{labels[0]}</span><span>{labels[1]}</span></div>
    </div>
  );
}
