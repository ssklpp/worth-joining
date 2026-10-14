import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "페이지를 찾을 수 없음" };

// 없는 주소(SPEC 9장 공통). 회사 · 역 상세의 없는 ID는 각 패널이 따로 안내한다
export default function NotFound() {
  return (
    <div className="prose">
      <h1>페이지를 찾을 수 없습니다</h1>
      <p>주소가 잘못되었거나 더 이상 제공하지 않는 페이지입니다.</p>
      <p><Link className="button" href="/">지도로 돌아가기</Link></p>
    </div>
  );
}
