import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import LoginPage from "./LoginPage";

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <LoginPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  localStorage.removeItem("gurupix_token");
  vi.resetModules();
});

describe("LoginPage", () => {
  it("renders login form with email and password fields", () => {
    renderLogin();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders 'Continue with Google' button", () => {
    renderLogin();
    expect(
      screen.getByRole("button", { name: /continue with google/i })
    ).toBeInTheDocument();
  });

  it("renders log in button by default", () => {
    renderLogin();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("toggles to signup mode", async () => {
    renderLogin();
    const toggle = screen.getByRole("button", { name: /sign up/i });
    await userEvent.click(toggle);
    expect(
      screen.getByRole("button", { name: /create account/i })
    ).toBeInTheDocument();
  });

  it("submits login form", async () => {
    const { api } = await import("@/api/client");
    const mockPost = vi.mocked(api.post);
    mockPost.mockResolvedValueOnce({
      access_token: "test-token",
      token_type: "bearer",
    });

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "user@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "Password123!");

    const loginBtn = screen.getByRole("button", { name: /log in/i });
    await userEvent.click(loginBtn);

    expect(mockPost).toHaveBeenCalledWith("/api/v1/auth/login", {
      email: "user@example.com",
      password: "Password123!",
    });
  });

  it("calls google start when Continue with Google is clicked", async () => {
    const { api } = await import("@/api/client");
    const mockGet = vi.mocked(api.get);
    mockGet.mockResolvedValueOnce({
      authorization_url: "https://accounts.google.com/o/oauth2/v2/auth?...",
    });

    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, href: "" },
    });

    renderLogin();
    const googleBtn = screen.getByRole("button", {
      name: /continue with google/i,
    });
    await userEvent.click(googleBtn);

    expect(mockGet).toHaveBeenCalledWith("/api/v1/auth/google/start");

    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });

  it("displays error message on login failure", async () => {
    const { api } = await import("@/api/client");
    const mockPost = vi.mocked(api.post);
    mockPost.mockRejectedValueOnce({ detail: "Invalid email or password" });

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "user@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "WrongPass1!");

    const loginBtn = screen.getByRole("button", { name: /log in/i });
    await userEvent.click(loginBtn);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/invalid email or password/i);
  });
});
