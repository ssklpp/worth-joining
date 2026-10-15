import type { Metadata } from "next";
import { Suspense } from "react";
import { StationCompareView } from "@/components/compare/StationCompareView";
import { SharedStationIds } from "@/components/compare/SharedStationIds";
import { BackToList } from "../../Panel";

export const metadata: Metadata = { title: "역 비교" };

// 역 비교 패널. ?ids=1,2,3 으로 열면 그 역들을 역 비교함에 담는다(/stations/[id]보다 이 정적 경로가 먼저다)
export default function StationComparePage() {
  return (
    <>
      <BackToList />
      <div className="prose">
        <h1>역 비교</h1>
        <p className="muted small">역 비교함에 담은 역(최대 3개)의 원룸 시세와 24개월 추이를 나란히 봅니다.</p>
      </div>
      <Suspense fallback={null}>
        <SharedStationIds />
      </Suspense>
      <StationCompareView />
    </>
  );
}
