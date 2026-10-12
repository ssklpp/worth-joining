// 숫자 · 날짜 표기. 비율은 소수(0.183 = 18.3%), 연봉은 원으로 온다(docs/05 1장)

/** 202608 → "2026년 8월" */
export function formatYm(ym: number | null | undefined): string {
  if (!ym) return "확인 중";
  return `${Math.floor(ym / 100)}년 ${ym % 100}월`;
}

/** 0.183 → "18.3%", signed면 "+18.3%" */
export function formatPct(value: number | null | undefined, signed = false): string {
  if (value === null || value === undefined) return "–";
  const text = `${(value * 100).toFixed(1)}%`;
  return signed && value > 0 ? `+${text}` : text;
}

/** 41_200_000 → "4,120만 원" */
export function formatWon(value: number | null | undefined): string {
  if (value === null || value === undefined) return "–";
  return `${Math.round(value / 10_000).toLocaleString("ko-KR")}만 원`;
}

/** 큰 금액(재무): 1_200_000_000 → "12억 원", 333_605_938_000_000 → "333조 6,059억 원" */
export function formatAmount(value: number | null | undefined): string {
  if (value === null || value === undefined) return "–";
  const sign = value < 0 ? "−" : "";
  const eok = Math.round(Math.abs(value) / 1e8);
  const jo = Math.floor(eok / 10_000);
  const rest = eok % 10_000;
  const parts = [jo ? `${jo.toLocaleString("ko-KR")}조` : "", rest || !jo ? `${rest.toLocaleString("ko-KR")}억` : ""];
  return `${sign}${parts.filter(Boolean).join(" ")} 원`;
}

export function formatCount(value: number | null | undefined, unit = "명"): string {
  if (value === null || value === undefined) return "–";
  return `${value.toLocaleString("ko-KR")}${unit}`;
}

/** 국민연금 원본의 업종 코드 999999는 분류가 없다는 뜻이다("BIZ_NO미존재사업장") */
export function industryLabel(industry: { code: string | null; name: string | null }): string {
  if (!industry.code || industry.code === "999999") return "업종 분류 없음";
  return industry.name ?? "업종 분류 없음";
}
