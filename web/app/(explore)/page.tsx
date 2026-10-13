import { Suspense } from "react";
import { Loading } from "@/components/Status";
import { ListPanel } from "./ListPanel";

// 첫 화면: 지도 + 목록 패널(decisions/006)
export default function Home() {
  return (
    <Suspense fallback={<Loading height={200} />}>
      <ListPanel />
    </Suspense>
  );
}
