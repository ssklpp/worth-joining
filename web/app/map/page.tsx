import type { Metadata } from "next";
import { MapExplorer } from "./MapExplorer";

export const metadata: Metadata = { title: "지도로 비교" };

export default function MapPage() {
  return (
    <div className="page">
      <div className="prose">
        <h1>지도로 비교</h1>
        <p className="muted">
          지도를 옮기거나 확대하면 그 범위의 회사가 가입자 많은 순으로 보입니다. 핀을 누르면 회사 정보가 나오고 비교에 담을 수
          있습니다.
        </p>
      </div>
      <MapExplorer />
    </div>
  );
}
