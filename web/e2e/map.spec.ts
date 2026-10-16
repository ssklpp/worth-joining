// 지도가 있어야 보이는 동작. 네이버 지도 키(web/.env.local)와 로컬 API(:8000)가 필요해 로컬에서만 돈다:
//   npm run test:e2e:map
import { expect, test } from "@playwright/test";

test.skip(!!process.env.CI, "지도 키와 로컬 API가 필요하다");

test("map-list 첫 화면: 지도 안의 회사 10곳씩 목록과 페이지 번호", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 2, name: /지도 안의 회사|같은 위치의 회사/ })).toBeVisible();
  const items = page.locator("ul li a[href^='/companies/']");
  await expect(items).toHaveCount(10);

  const pager = page.getByRole("navigation", { name: "목록 페이지" });
  await pager.getByRole("button", { name: "2페이지" }).click();
  await expect(pager.getByRole("button", { name: "2페이지" })).toHaveAttribute("aria-current", "page");
  await expect(items).toHaveCount(10);
});

test("map-station 역 시세: 빈 회사 핀 없이(#80) 역을 강조하고 반경 원 두 개를 그린다", async ({ page }) => {
  await page.goto("/stations/4");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("강남역");
  await expect(page.getByRole("button", { name: "강남역 시세 보기" })).toBeVisible();
  // 역을 회사처럼 select해서 생기던 빈 핀(이름만 "강남역")이 없어야 한다
  await expect(page.getByRole("button", { name: "강남역", exact: true })).toHaveCount(0);
  await expect(page.getByText("500m", { exact: true })).toBeVisible();
  await expect(page.getByText("750m", { exact: true })).toBeVisible();
});
