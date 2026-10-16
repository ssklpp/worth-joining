// 웹 화면 자동 테스트(Playwright, web/README.md "화면 테스트").
// smoke: API 응답을 e2e/api/에 저장해 두고 돌려준다. DB · API 서버 · 지도 키 없이 CI에서 돈다.
// map: 지도 키와 로컬 API가 있어야 하는 테스트(지도 핀 · 반경 원). 로컬에서만 돈다.
import { defineConfig, devices } from "@playwright/test";

const CI = !!process.env.CI;
const PORT = process.env.E2E_PORT ?? "3000"; // 떠 있는 개발 서버와 겹치지 않게 바꿀 때
const BASE = `http://localhost:${PORT}`;
const desktop = {
  ...devices["Desktop Chrome"],
  viewport: { width: 1400, height: 900 },
  // 로컬은 설치된 Edge를 쓰고(브라우저를 따로 받지 않는다), CI는 Playwright의 Chromium을 쓴다
  channel: CI ? undefined : "msedge",
  locale: "ko-KR",
};

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  retries: CI ? 1 : 0,
  reporter: CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: { baseURL: BASE, trace: "retain-on-failure" },
  projects: [
    { name: "smoke", testIgnore: /map\.spec\.ts/, use: desktop },
    { name: "map", testMatch: /map\.spec\.ts/, use: desktop },
  ],
  // 로컬은 떠 있는 개발 서버(:3000)를 그대로 쓴다. CI는 빌드한 앱(npm run build 다음)을 띄운다
  webServer: {
    command: CI ? `npm run start -- -p ${PORT}` : `npm run dev -- -p ${PORT}`,
    url: BASE,
    reuseExistingServer: !CI,
    timeout: 120_000,
  },
});
