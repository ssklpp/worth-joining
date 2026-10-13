import type { Metadata } from "next";
import { BackToList } from "../../Panel";
import { StationPage } from "./StationPage";

export const metadata: Metadata = { title: "역 시세" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <BackToList />
      <StationPage id={/^\d+$/.test(id) ? Number(id) : null} />
    </>
  );
}
