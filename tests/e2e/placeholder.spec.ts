/**
 * Stage 0: placeholder E2E so CI has a runnable Playwright suite.
 * Real flows (login, onboarding, recs) added in later stages.
 */
import { test, expect } from "@playwright/test";

test("frontend or backend is reachable", async ({ page }) => {
  // Prefer frontend; if E2E_BASE_URL points to backend, root returns JSON
  const base = process.env.E2E_BASE_URL ?? "http://localhost:5173";
  const res = await page.goto(base);
  expect(res?.status()).toBeLessThan(500);
});
