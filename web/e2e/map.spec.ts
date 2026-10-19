// 지도가 있어야 보이는 동작. 네이버 지도 키(web/.env.local)와 로컬 API(:8000)가 필요해 로컬에서만 돈다:
//   npm run test:e2e:map
import { expect, liveTest as test } from "./fixtures";

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

test("map-station-click 회사 핀 옆의 역도 눌린다: 핀을 감싼 지도 칸이 클릭을 가로채지 않는다", async ({ page }) => {
  await page.goto("/");
  // 분당구는 서현역 바로 위에 회사 핀(삼성전자판매)이 있다(2026-10-16 성남 추가 뒤 발견)
  await page.getByRole("combobox", { name: "지역" }).selectOption("41135");
  const station = page.getByRole("button", { name: "서현역 시세 보기" });
  await expect(station).toBeVisible();
  await station.click({ timeout: 5000 });
  await expect(page).toHaveURL(/\/stations\/\d+$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("서현역");
});

test("map-list-size 목록을 20곳씩 보면 지도 핀도 20개, 다시 10곳씩", async ({ page }) => {
  await page.goto("/");
  const items = page.locator("ul li a[href^='/companies/']");
  await expect(items).toHaveCount(10);
  const size = page.getByRole("combobox", { name: "한 페이지에 보일 회사 수" });

  await size.selectOption("20");
  await expect(items).toHaveCount(20);
  // 지도 핀도 이 페이지의 20곳. 같은 위치의 회사는 핀 하나로 묶여 20개보다 적을 수 있다
  await expect.poll(() => page.locator("button[aria-pressed]").count()).toBeGreaterThan(10);
  expect(await page.locator("button[aria-pressed]").count()).toBeLessThanOrEqual(20);
  await expect(page.getByText(/^1–20 \//)).toBeVisible();

  await size.selectOption("10");
  await expect(items).toHaveCount(10);
});

test("map-list-keep 상세에 갔다 '목록으로' 돌아와도 정렬 · 20곳씩이 남는다", async ({ page }) => {
  await page.goto("/");
  const sort = page.getByRole("combobox", { name: "정렬" });
  const size = page.getByRole("combobox", { name: "한 페이지에 보일 회사 수" });
  await sort.selectOption("growth");
  await size.selectOption("20");
  const items = page.locator("ul li a[href^='/companies/']");
  await expect(items).toHaveCount(20);

  await items.first().click();
  await expect(page).toHaveURL(/\/companies\/\d+$/);
  await page.getByRole("button", { name: "목록으로" }).click();

  await expect(sort).toHaveValue("growth");
  await expect(size).toHaveValue("20");
  await expect(items).toHaveCount(20);
});

test("map-station-norent 원룸 계약이 없는 역은 이유를 보여 준다(이촌역)", async ({ page }) => {
  await page.goto("/stations/757");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("이촌역");
  await expect(page.getByText(/역 500m 안에 최근 12개월 원룸 계약이 없어/)).toBeVisible();
  await expect(page.getByText(/아파트와 단독 · 다가구는\s*세지 않아/)).toBeVisible();
});
