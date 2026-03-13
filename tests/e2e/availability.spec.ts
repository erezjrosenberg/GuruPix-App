/**
 * Stage 5.3 E2E: Catalog page displays where-to-watch on cards.
 *
 * Mocks API responses for items and availability.
 */
import { test, expect } from "@playwright/test";

test.describe("Catalog page - where to watch", () => {
  test("displays item cards with where-to-watch section", async ({ page }) => {
    await page.route("**/api/v1/items", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: 1,
            type: "movie",
            title: "E2E Test Movie",
            synopsis: "A test film for E2E.",
            genres: ["Comedy"],
            runtime: 90,
            release_date: "2024-01-01",
            language: "en",
          },
        ]),
      }),
    );

    await page.route("**/api/v1/availability*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            provider: "Netflix",
            region: "US",
            url: "https://netflix.com/test",
            availability_type: "stream",
          },
          {
            provider: "Amazon",
            region: "US",
            url: "https://amazon.com/test",
            availability_type: "rent",
          },
        ]),
      }),
    );

    await page.route("**/api/v1/reviews/aggregate*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { source: "RT_CRITICS", score: 91, scale: 100, normalized_score: 91 },
          { source: "RT_AUDIENCE", score: 98, scale: 100, normalized_score: 98 },
        ]),
      }),
    );

    await page.goto("/catalog");

    await expect(page.getByText("E2E Test Movie")).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Scores from:")).toBeVisible();
    await expect(page.getByText(/RT CRITICS 91%/)).toBeVisible();
    await expect(page.getByText("Where to watch:")).toBeVisible();
    await expect(page.getByRole("link", { name: "Netflix" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Amazon" })).toBeVisible();
  });

  test("shows empty state when no items", async ({ page }) => {
    await page.route("**/api/v1/items", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      }),
    );

    await page.goto("/catalog");

    await expect(
      page.getByText(/no items in catalog|run seed ingestion/i),
    ).toBeVisible({ timeout: 5000 });
  });

  test("catalog link from home navigates to catalog", async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "e2e-user-id",
          email: "e2e@example.com",
          created_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );

    // Mock profile so user is not redirected to onboarding
    await page.route("**/api/v1/profiles/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_id: "e2e-user-id",
          display_name: "E2E User",
          bio: null,
          region: "US",
          languages: null,
          providers: null,
          preferences: {},
          consent: { data_processing: true },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );

    await page.route("**/api/v1/items", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      }),
    );

    // Set token so AuthContext fetches user and shows logged-in home view
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("gurupix_token", "fake-token-for-catalog-test");
      window.dispatchEvent(new CustomEvent("gurupix:token-set"));
    });
    await page.goto("/");
    const catalogLink = page.getByRole("link", { name: /browse catalog/i });
    await catalogLink.click({ timeout: 15000 });

    await expect(page).toHaveURL(/\/catalog/);
  });
});
