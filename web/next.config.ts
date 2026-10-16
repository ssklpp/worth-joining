import type { NextConfig } from "next";

const DEV = process.env.NODE_ENV !== "production";
const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// 네이버 지도(Web Dynamic Map)가 쓰는 출처: 스크립트 · 인증(oapi.map.naver.com), 지도 타일 · 스타일(JSONP)
// (*.pstatic.net, 로컬 http에서는 *.naver.net), 오류 수집(*.navercorp.com). scheme을 적지 않아 페이지와 같은
// 방식(로컬 http, 배포 https)을 따른다. 바뀌면 화면 테스트의 CSP 위반 검사가 실패한다(web/e2e)
const NAVER = "*.naver.com *.naver.net *.pstatic.net *.navercorp.com";

// CSP: 허용 목록 밖의 스크립트 · 연결 · 프레임 · 플러그인을 막는다. Next.js가 페이지에 인라인 스크립트를 넣고
// 화면에 인라인 스타일이 있어 'unsafe-inline'은 연다(nonce 방식은 모든 페이지가 동적 렌더링이 되어 쓰지 않는다).
// 개발 서버는 새로 고침(HMR)에 eval과 웹소켓을 쓴다
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline'${DEV ? " 'unsafe-eval'" : ""} ${NAVER}`,
  "style-src 'self' 'unsafe-inline'",
  `img-src 'self' data: blob: ${NAVER}`,
  "font-src 'self' data:",
  `connect-src 'self' ${API} ${NAVER}${DEV ? " ws:" : ""}`,
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

// 기본 보안 헤더(개선 검토 6번)와 CSP(2026-10-16)
const SECURITY_HEADERS = [
  { key: "Content-Security-Policy", value: CSP },
  { key: "X-Frame-Options", value: "DENY" }, // 다른 사이트가 iframe으로 감싸는 클릭재킹 차단
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" }, // 채용 사이트로 나갈 때 경로를 넘기지 않는다
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
};

export default nextConfig;
