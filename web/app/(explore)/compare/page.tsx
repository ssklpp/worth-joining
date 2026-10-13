import type { Metadata } from "next";
import { Suspense } from "react";
import { CompareView } from "@/components/compare/CompareView";
import { SharedIds } from "@/components/compare/SharedIds";
import { BackToList } from "../Panel";

export const metadata: Metadata = { title: "회사 비교" };

// 비교 패널(docs/03 5장). ?ids=1,2,3 으로 열면 그 회사들을 담는다
export default function ComparePage() {
  return (
    <>
      <BackToList />
      <div className="prose">
        <h1>회사 비교</h1>
        <p className="muted small">비교함에 담은 회사(최대 3곳)의 가입자 흐름과 지표를 나란히 봅니다.</p>
      </div>
      <Suspense fallback={null}>
        <SharedIds />
      </Suspense>
      <CompareView />
    </>
  );
}
