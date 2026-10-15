import type { Metadata } from "next";
import { BackToList } from "../../Panel";
import { StationPage } from "./StationPage";

export const metadata: Metadata = { title: "역 시세" };

// 숫자가 아닌 ID(예: /stations/abc)는 null로 넘겨 패널이 "역을 찾을 수 없습니다"를 보여 준다
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <BackToList />
      <StationPage id={/^\d+$/.test(id) ? Number(id) : null} />
    </>
  );
}
