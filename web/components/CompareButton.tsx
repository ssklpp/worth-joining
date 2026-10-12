"use client";

// "비교에 담기" ↔ "비교에서 빼기"(docs/03 9장). 비교함이 가득 차면 담을 수 없다고 알린다
import { MAX_COMPARE, useCompare } from "@/lib/compare";

export function CompareButton({ id, name, className = "button quiet" }:
  { id: number; name: string; className?: string }) {
  const compare = useCompare();
  const inBox = compare.has(id);
  const blocked = !inBox && compare.full;

  return (
    <button type="button" className={className} aria-pressed={inBox} disabled={blocked}
      title={blocked ? `비교함에는 ${MAX_COMPARE}곳까지 담을 수 있습니다` : undefined}
      onClick={() => (inBox ? compare.remove(id) : compare.add({ id, name }))}>
      {inBox ? "비교에서 빼기" : blocked ? "비교함이 가득 찼습니다" : "비교에 담기"}
    </button>
  );
}
