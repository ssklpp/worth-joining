import type { Metadata } from "next";
import { BackToList } from "../../Panel";
import { CompanyPage } from "./CompanyPage";

export const metadata: Metadata = { title: "회사 상세" };

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <>
      <BackToList />
      <CompanyPage id={/^\d+$/.test(id) ? Number(id) : null} />
    </>
  );
}
