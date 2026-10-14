import type { NextConfig } from "next";

// 기본 보안 헤더(개선 검토 6번). CSP는 네이버 지도 스크립트 출처를 모두 열어야 해서 두지 않는다
const SECURITY_HEADERS = [
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
