import type { Metadata } from "next";
import { BackToList } from "../../Panel";
import { CompanyPage } from "./CompanyPage";

export const metadata: Metadata = { title: "회사 상세" };

// 숫자가 아닌 ID(예: /companies/abc)는 null로 넘겨 패널이 "회사를 찾을 수 없습니다"를 보여 준다
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <BackToList />
      <CompanyPage id={/^\d+$/.test(id) ? Number(id) : null} />
    </>
  );
}
