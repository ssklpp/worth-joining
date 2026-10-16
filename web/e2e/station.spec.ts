// 역 시세(반경 · 기간) · 역 비교 · 없는 역
import { expect, test } from "./fixtures";

test("station-radius 반경 · 기간 버튼에 따라 시세와 안내가 바뀐다", async ({ page }) => {
  await page.goto("/stations/4");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("강남역");

  const radius = page.getByRole("radiogroup", { name: "역에서 거리" });
  const contracts = page.locator("dt", { hasText: /^월세 계약$/ }).locator("+ dd");
  await expect(radius.getByRole("radio", { name: "반경 500m" })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByText(/역에서 500m 안\(지도의 원\)/)).toBeVisible();
  await expect(contracts).toHaveText("437건");

  await radius.getByRole("radio", { name: "반경 750m" }).click();
  await expect(radius.getByRole("radio", { name: "반경 750m" })).toHaveAttribute("aria-checked", "true");
  await expect(page.getByText(/역에서 750m 안\(지도의 원\)/)).toBeVisible();
  await expect(page.getByText(/이웃 역의 범위와 겹칠 수 있습니다/)).toBeVisible();
  await expect(contracts).toHaveText("1,215건");

  const period = page.getByRole("radiogroup", { name: "계약 기간" });
  await period.getByRole("radio", { name: "최근 24개월" }).click();
  await expect(period.getByRole("radio", { name: "최근 24개월" })).toHaveAttribute("aria-checked", "true");
  await expect(contracts).not.toHaveText("1,215건");
});

test("station-compare 없어진 역은 빠지고, 빼기를 눌러도 표가 사라지지 않는다(#81)", async ({ page }) => {
  // 비교함에 지금 없는 역(99999)이 남아 있는 상황
  await page.addInitScript(() => {
    if (sessionStorage.getItem("seeded")) return;
    sessionStorage.setItem("seeded", "1");
    localStorage.setItem("worth-joining.station-compare", JSON.stringify([
      { id: 21, name: "신림역" }, { id: 10, name: "홍대입구역" }, { id: 99999, name: "없는역" }]));
  });
  await page.goto("/stations/compare");

  const headers = page.locator("thead a");
  await expect(headers).toHaveText(["신림역", "홍대입구역"]);
  expect(await page.evaluate(() => localStorage.getItem("worth-joining.station-compare"))).not.toContain("99999");

  // 빼기 직후 표가 로딩 상자로 바뀌는지 지켜본다
  await page.evaluate(() => {
    (window as unknown as { lost: boolean }).lost = false;
    new MutationObserver(() => {
      if (!document.querySelector("table")) (window as unknown as { lost: boolean }).lost = true;
    }).observe(document.body, { childList: true, subtree: true });
  });
  // 아래 비교함 막대의 칩(×)에도 같은 이름이 있어 표 안의 버튼을 누른다
  await page.getByRole("table").getByRole("button", { name: "신림역 비교에서 빼기" }).click();
  await expect(headers).toHaveText(["홍대입구역"]);
  expect(await page.evaluate(() => (window as unknown as { lost: boolean }).lost)).toBe(false);
});

test("station-404 없는 역은 안내 화면", async ({ page }) => {
  await page.goto("/stations/999999");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("역을 찾을 수 없습니다");
});
