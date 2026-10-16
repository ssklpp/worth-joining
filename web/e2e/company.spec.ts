// 회사 검색 · 상세 · 오류 화면
import { API, expect, test } from "./fixtures";

test("search-detail 검색 → 결과 → 회사 상세 → 채용 사이트 바로가기", async ({ page }) => {
  await page.goto("/");
  // 개발 서버는 첫 화면이 React에 연결(hydration)되기 전에 입력하면 사라진다. 넘어갈 때까지 다시 한다
  await expect(async () => {
    await page.getByRole("searchbox", { name: "회사명 또는 사업자번호 앞 6자리" }).fill("우아한");
    await page.getByRole("button", { name: "검색", exact: true }).click();
    await expect(page).toHaveURL(/\?q=/, { timeout: 1_000 });
  }).toPass();

  const results = page.getByRole("region", { name: "검색 결과" });
  await results.getByRole("link", { name: /우아한형제들/ }).click();

  await expect(page).toHaveURL(/\/companies\/31650$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("주식회사 우아한형제들");
  for (const title of ["회사 체력", "회사 근처 주거비", "가입자 추이", "재무"]) {
    await expect(page.getByRole("heading", { level: 2, name: title })).toBeVisible();
  }
  // 회사명에서 법인 표기를 빼고 검색한다(decisions/008)
  await expect(page.getByRole("link", { name: "사람인에서 채용공고 보기" }))
    .toHaveAttribute("href", /saramin\.co\.kr.*searchword=%EC%9A%B0%EC%95%84%ED%95%9C%ED%98%95%EC%A0%9C%EB%93%A4$/);
  await expect(page.getByRole("link", { name: "잡코리아에서 채용공고 보기" }))
    .toHaveAttribute("href", /jobkorea\.co\.kr.*stext=/);
});

test("company-404 없는 회사는 안내 화면", async ({ page }) => {
  await page.goto("/companies/999999999");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("회사를 찾을 수 없습니다");
  await page.goto("/companies/abc");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("회사를 찾을 수 없습니다");
});

test("api-error API 오류면 안내와 다시 시도", async ({ page }) => {
  // 저장된 응답보다 나중에 건 route가 먼저다. 첫 요청만 500으로 바꾸고 나머지는 저장된 응답으로
  let failed = false;
  await page.route(`${API}/companies/31650`, (route) => {
    if (failed) return route.fallback();
    failed = true;
    return route.fulfill({ status: 500, json: { detail: "서버 오류" } });
  });
  await page.goto("/companies/31650");

  const alert = page.getByRole("alert").filter({ hasText: "정보를 불러오지 못했습니다" });
  await expect(alert).toBeVisible();
  await alert.getByRole("button", { name: "다시 시도" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("주식회사 우아한형제들");
});
