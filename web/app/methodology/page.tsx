import type { Metadata } from "next";
import { MethodologyBody } from "./MethodologyBody";

export const metadata: Metadata = { title: "계산 방법" };

export default function MethodologyPage() {
  return (
    <div className="page">
      <div className="prose">
        <h1>계산 방법과 한계</h1>
        <p className="muted">
          모든 지표는 국민연금 가입 사업장 공개 자료로 계산합니다. 회사가 직접 밝힌 숫자가 아닙니다.
        </p>
      </div>
      <MethodologyBody />
    </div>
  );
}
