import type { Metadata } from "next";
import { Suspense } from "react";
import { CompareView } from "@/components/compare/CompareView";
import { SharedIds } from "@/components/compare/SharedIds";

export const metadata: Metadata = { title: "회사 비교" };

// 지도 화면(Phase 8)이 생기기 전까지 비교는 이 화면에서 한다. 지도의 비교 패널도 CompareView를 쓴다
export default function ComparePage() {
  return (
    <div className="page">
      <div className="prose">
        <h1>회사 비교</h1>
        <p className="muted">비교함에 담은 회사(최대 3곳)의 가입자 흐름과 지표를 나란히 봅니다.</p>
      </div>
      <Suspense fallback={null}>
        <SharedIds />
      </Suspense>
      <CompareView />
    </div>
  );
}
