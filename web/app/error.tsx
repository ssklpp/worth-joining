"use client";

// 화면을 그리다 난 오류(SPEC 9장 공통: 오류 · 다시 시도). API 오류는 각 구획의 ErrorBox가 먼저 받는다
import Link from "next/link";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="prose" role="alert">
      <h1>화면을 표시하지 못했습니다</h1>
      <p>잠시 후 다시 시도해 주세요. 계속되면 지도 화면에서 다시 시작해 주세요.</p>
      <p>
        <button type="button" className="button" onClick={reset}>다시 시도</button>{" "}
        <Link className="button quiet" href="/">지도로 돌아가기</Link>
      </p>
    </div>
  );
}
