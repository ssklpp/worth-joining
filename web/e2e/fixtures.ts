// smoke 테스트의 page: API(:8000) 응답을 e2e/api/의 JSON 파일로 돌려준다. DB · API 서버 없이 돈다.
// E2E_RECORD=1이면 실제 API에 보내고 성공한 응답(5xx 제외)을 주소마다 파일 하나로 저장한다(npm run test:e2e:record).
// 저장된 파일이 없는 API 요청은 끊는다(abort). 화면이 부르는 API나 응답이 바뀌면 녹화를 다시 한다.
// 지도 핀(/map/companies)은 지도 범위마다 주소가 달라 저장하지 않는다(지도 동작은 map.spec.ts가 본다)
import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { test as base } from "@playwright/test";

export { expect } from "@playwright/test";

export const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const RECORD = process.env.E2E_RECORD === "1";
const CORS = { "access-control-allow-origin": "*" };

/** /companies?q=우아한 → companies_q_EC_9A_..._<해시 8자>.json */
function fileFor(dir: string, url: URL) {
  const key = url.pathname + url.search;
  const slug = key.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 60);
  return path.join(dir, `${slug}_${createHash("sha1").update(key).digest("hex").slice(0, 8)}.json`);
}

export const test = base.extend({
  page: async ({ page }, run, testInfo) => { // run: Playwright의 use(React Hook 규칙과 이름이 겹쳐 바꿈)
    const dir = path.join(testInfo.project.testDir, "api");
    if (RECORD) await mkdir(dir, { recursive: true });
    await page.route(`${API}/**`, async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname === "/map/companies") return route.abort();
      const file = fileFor(dir, url);
      if (RECORD) {
        const res = await route.fetch().catch(() => null); // 화면이 취소한 요청
        if (!res) return route.abort();
        const body = await res.text();
        if (res.status() < 500) {
          await writeFile(file, JSON.stringify({ status: res.status(), body: JSON.parse(body) }, null, 1) + "\n");
        }
        return route.fulfill({ response: res, body });
      }
      const saved = await readFile(file, "utf8").catch(() => null);
      if (!saved) return route.abort();
      const { status, body } = JSON.parse(saved);
      return route.fulfill({ status, json: body, headers: CORS });
    });
    await run(page);
  },
});
