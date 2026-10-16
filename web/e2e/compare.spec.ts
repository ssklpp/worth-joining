// 회사 비교함(최대 3곳) · 비교 화면 · 공유 링크
import { expect, test } from "./fixtures";

const headers = (page: import("@playwright/test").Page) => page.locator("thead a");

test("compare-box 비교에 담기 3곳 → 4번째는 막힘 → 비교 화면", async ({ page }) => {
  for (const id of [31650, 32079, 54656]) {
    await page.goto(`/companies/${id}`);
    await page.getByRole("button", { name: "비교에 담기", exact: true }).click();
    // 비교함 칩의 "× (회사명) 비교에서 빼기"와 구분해 정확한 이름으로 찾는다
    await expect(page.getByRole("button", { name: "비교에서 빼기", exact: true })).toBeVisible();
  }
  await page.goto("/companies/87863");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("주식회사우아한청년들");
  await expect(page.getByRole("button", { name: "비교함이 가득 찼습니다" })).toBeDisabled();

  await page.getByRole("link", { name: "비교하기", exact: true }).click();
  await expect(page).toHaveURL(/\/compare$/);
  await expect(page.getByRole("heading", { level: 2, name: "가입자 지수" })).toBeVisible();
  await expect(headers(page)).toHaveText(["주식회사 우아한형제들", "（주）비바리퍼블리카", "주식회사 무신사"]);
});

test("compare-share 공유 링크(?ids=)로 열면 그 회사들을 담는다", async ({ page }) => {
  await page.goto("/compare?ids=31650,54656");
  await expect(page).toHaveURL(/\/compare$/);
  await expect(headers(page)).toHaveText(["주식회사 우아한형제들", "주식회사 무신사"]);
});
