/**
 * Stage 4 E2E: Authentication flows (email/password + mocked Google OAuth).
 *
 * Uses Playwright route interception to mock backend API responses so tests
 * run without a live backend. The frontend dev server is started by the
 * Playwright webServer config.
 */
import { test, expect } from "@playwright/test";

// -- Login page rendering ----------------------------------------------------

test.describe("Login page", () => {
  test("renders email and password fields", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("renders Log In button", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("button", { name: /log in/i }),
    ).toBeVisible();
  });

  test("renders Continue with Google button", async ({ page }) => {
    await page.goto("/login");
    await expect(
      page.getByRole("button", { name: /continue with google/i }),
    ).toBeVisible();
  });

  test("can toggle between login and signup modes", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /sign up/i }).click();
    await expect(
      page.getByRole("button", { name: /create account/i }),
    ).toBeVisible();
    await page.getByRole("button", { name: /log in/i }).click();
    await expect(
      page.getByRole("button", { name: /log in$/i }),
    ).toBeVisible();
  });
});

// -- Email/password login flow -----------------------------------------------

test.describe("Email/password auth flow", () => {
  test("successful signup redirects to home", async ({ page }) => {
    // Mock /auth/me to return 401 initially (no token)
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"Unauthorized"}' }),
    );

    await page.goto("/login");

    // Mock signup endpoint
    await page.route("**/api/v1/auth/signup", (route) =>
      route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "fake-jwt-for-e2e",
          token_type: "bearer",
        }),
      }),
    );

    // After signup, /auth/me should return the user
    await page.unroute("**/api/v1/auth/me");
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
          email: "e2e@example.com",
          created_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );

    // Mock /profiles/me so user stays on home (has completed onboarding)
    await page.route("**/api/v1/profiles/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
          display_name: null,
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

    // Toggle to signup mode
    await page.getByRole("button", { name: /sign up/i }).click();

    await page.locator('input[type="email"]').fill("e2e@example.com");
    await page.locator('input[type="password"]').fill("StrongPass1!");
    await page.getByRole("button", { name: /create account/i }).click();

    // Should redirect to home and show user email
    await expect(page.getByText("e2e@example.com")).toBeVisible({ timeout: 5000 });
  });

  test("failed login shows error message", async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"Unauthorized"}' }),
    );

    await page.goto("/login");

    await page.route("**/api/v1/auth/login", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid email or password" }),
      }),
    );

    await page.locator('input[type="email"]').fill("bad@example.com");
    await page.locator('input[type="password"]').fill("WrongPass1!");
    await page.getByRole("button", { name: /log in/i }).click();

    await expect(page.getByRole("alert")).toContainText(
      /invalid email or password/i,
    );
  });
});

// -- Mocked Google OAuth flow ------------------------------------------------

test.describe("Google OAuth flow (mocked)", () => {
  test("clicking Continue with Google redirects to consent URL", async ({
    page,
  }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 401, contentType: "application/json", body: '{"detail":"Unauthorized"}' }),
    );

    // Mock google/start to return a fake authorization URL (to our own callback)
    await page.route("**/api/v1/auth/google/start", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          authorization_url:
            "https://accounts.google.com/o/oauth2/v2/auth?state=fake-state",
        }),
      }),
    );

    await page.goto("/login");
    const googleBtn = page.getByRole("button", {
      name: /continue with google/i,
    });

    // Intercept navigation to Google (we don't want to actually go there)
    const [request] = await Promise.all([
      page.waitForEvent("request", (req) =>
        req.url().includes("accounts.google.com"),
      ),
      googleBtn.click(),
    ]);

    expect(request.url()).toContain("accounts.google.com");
    expect(request.url()).toContain("state=fake-state");
  });

  test("callback page exchanges code and redirects to home", async ({
    page,
  }) => {
    // Mock the callback API to return a JWT
    await page.route("**/api/v1/auth/google/callback*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "oauth-jwt-for-e2e",
          token_type: "bearer",
        }),
      }),
    );

    // After callback stores the token, /auth/me returns the user
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
          email: "oauth-user@gmail.com",
          created_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );

    // Mock /profiles/me so user stays on home
    await page.route("**/api/v1/profiles/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_id: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
          display_name: null,
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

    // Simulate Google redirecting back to our callback page with code + state
    await page.goto("/auth/google/callback?code=auth-code&state=valid-state");

    // Should redirect to home and show the user's email
    await expect(page.getByText("oauth-user@gmail.com")).toBeVisible({
      timeout: 5000,
    });
  });

  test("callback page shows error on failed exchange", async ({ page }) => {
    await page.route("**/api/v1/auth/google/callback*", (route) =>
      route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid or expired state" }),
      }),
    );

    await page.goto("/auth/google/callback?code=bad-code&state=bad-state");

    await expect(page.getByRole("alert")).toContainText(
      /invalid or expired state/i,
    );
    await expect(page.getByText(/back to login/i)).toBeVisible();
  });

  test("callback page shows error when params missing", async ({ page }) => {
    await page.goto("/auth/google/callback");

    await expect(page.getByRole("alert")).toContainText(
      /missing authorization code or state/i,
    );
  });
});

// -- Onboarding flow (new user) -----------------------------------------------

test.describe("Onboarding flow", () => {
  test("new user without profile is redirected to onboarding", async ({
    page,
  }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "new-user-id",
          email: "new@example.com",
          created_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );

    // No profile = new user, triggers onboarding redirect
    await page.route("**/api/v1/profiles/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: "null",
      }),
    );

    // Set token so useAuth considers user logged in
    await page.goto("/login");
    await page.evaluate(() =>
      localStorage.setItem("gurupix_token", "fake-token-for-onboarding-test"),
    );
    await page.goto("/");

    await expect(page).toHaveURL(/\/onboarding/);
    await expect(page.getByText(/welcome to gurupix/i)).toBeVisible();
    await expect(page.getByText(/tell us a bit about yourself/i)).toBeVisible();
  });

  test("onboarding requires consent to continue", async ({ page }) => {
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "new-user-2",
          email: "new2@example.com",
          created_at: "2026-01-01T00:00:00Z",
        }),
      }),
    );
    await page.route("**/api/v1/profiles/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: "null",
      }),
    );

    await page.goto("/login");
    await page.evaluate(() =>
      localStorage.setItem("gurupix_token", "fake-token-2"),
    );
    await page.goto("/");

    await expect(page).toHaveURL(/\/onboarding/);
    // Continue button should be disabled without consent
    const continueBtn = page.getByRole("button", { name: /continue/i });
    await expect(continueBtn).toBeDisabled();
  });
});
