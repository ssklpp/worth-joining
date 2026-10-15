"use client";

// "비교에 담기" ↔ "비교에서 빼기"(docs/03 9장). 비교함이 가득 차면 담을 수 없다고 알린다.
// 회사는 useCompare, 역은 useStationCompare를 box로 넘긴다
import { MAX_COMPARE, useCompare, type CompareBox } from "@/lib/compare";

export function CompareButton({ id, name, className = "button quiet", box, unit = "곳" }: {
  id: number; name: string; className?: string; box?: CompareBox; unit?: string;
}) {
  const fallback = useCompare();
  const compare = box ?? fallback;
  const inBox = compare.has(id);
  const blocked = !inBox && compare.full;

  return (
    <button type="button" className={className} aria-pressed={inBox} disabled={blocked}
      title={blocked ? `비교함에는 ${MAX_COMPARE}${unit}까지 담을 수 있습니다` : undefined}
      onClick={() => (inBox ? compare.remove(id) : compare.add({ id, name }))}>
      {inBox ? "비교에서 빼기" : blocked ? "비교함이 가득 찼습니다" : "비교에 담기"}
    </button>
  );
}
