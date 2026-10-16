import type { Metadata } from "next";
import { IBM_Plex_Sans_KR } from "next/font/google";
import { preconnect } from "react-dom";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

// 글꼴은 IBM Plex Sans KR 한 가족만(docs/03 3장).
// 한글 글꼴은 글자 범위마다 파일이 100여 개로 나뉜다. 미리 받기(preload)를 켜면 굵기 4종의 조각 280개(2.6MB)를
// 모두 <link rel="preload">로 받아 첫 화면이 늦어진다. 끄면 브라우저가 화면에 쓰인 글자 조각만 받는다
const plex = IBM_Plex_Sans_KR({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
  preload: false,
  variable: "--font-plex",
});

// lib/api.ts(클라이언트 모듈)의 API_BASE와 같은 값. 서버 컴포넌트라 직접 읽는다
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const metadata: Metadata = {
  title: { default: "다닐만한가", template: "%s | 다닐만한가" },
  description: "국민연금 공개 자료로 보는 서울 · 성남 회사의 인원 추이, 입퇴사율, 추정 연봉",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  // 첫 화면이 곧 부를 API와 네이버 지도 서버에 미리 연결해 둔다(Lighthouse "Preconnect to required origins")
  preconnect(API_BASE, { crossOrigin: "anonymous" });
  preconnect("https://oapi.map.naver.com");
  preconnect("https://nrbe.pstatic.net");
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
