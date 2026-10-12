"use client";

// 머리글의 "비교함 N/3"(SPEC 9장 공통: 화면 상단에 담은 수 표시)
import Link from "next/link";
import { MAX_COMPARE, useCompare } from "@/lib/compare";

export function CompareCount() {
  const { items } = useCompare();
  return (
    <Link href="/compare" aria-label={`비교함, ${items.length}곳 담음`}>
      비교함 <span className="num">{items.length}/{MAX_COMPARE}</span>
    </Link>
  );
}
