/// <reference types="node" />
import { defineConfig, devices } from "@playwright/test";

/**
 * E2E tests for GuruPix. Stage 0: minimal config.
 * Run from repo root: npx playwright test (from tests/e2e) or from repo root with config path.
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run dev",
        cwd: "../../frontend",
        url: "http://localhost:5173",
        reuseExistingServer: !process.env.CI,
      },
});
