import type { Metadata } from "next";
import { IBM_Plex_Sans_KR } from "next/font/google";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

// 글꼴은 IBM Plex Sans KR 한 가족만(docs/03 3장)
const plex = IBM_Plex_Sans_KR({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
  variable: "--font-plex",
});

export const metadata: Metadata = {
  title: { default: "다닐만한가", template: "%s | 다닐만한가" },
  description: "국민연금 공개 자료로 보는 서울 회사의 인원 추이, 입퇴사율, 추정 연봉",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko" className={plex.variable}>
      <body>
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
