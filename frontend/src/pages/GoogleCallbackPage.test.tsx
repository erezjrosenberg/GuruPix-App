import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import GoogleCallbackPage from "./GoogleCallbackPage";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

function renderCallback(search = "?code=auth-code&state=valid-state") {
  return render(
    <MemoryRouter initialEntries={[`/auth/google/callback${search}`]}>
      <GoogleCallbackPage />
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.restoreAllMocks();
  mockNavigate.mockClear();
  localStorage.removeItem("gurupix_token");
});

describe("GoogleCallbackPage", () => {
  it("renders loading state initially with valid params", async () => {
    const { api } = await import("@/api/client");
    const mockGet = vi.mocked(api.get);
    mockGet.mockReturnValue(new Promise(() => {})); // never resolves

    renderCallback();
    expect(screen.getByText(/signing you in/i)).toBeInTheDocument();
  });

  it("shows error when code is missing", () => {
    renderCallback("?state=valid-state");
    expect(screen.getByRole("alert")).toHaveTextContent(
      /missing authorization code or state/i
    );
  });

  it("shows error when state is missing", () => {
    renderCallback("?code=auth-code");
    expect(screen.getByRole("alert")).toHaveTextContent(
      /missing authorization code or state/i
    );
  });

  it("calls callback API and navigates on success", async () => {
    const { api, setToken } = await import("@/api/client");
    const mockGet = vi.mocked(api.get);
    const mockSetToken = vi.mocked(setToken);
    mockGet.mockResolvedValueOnce({
      access_token: "test-jwt-token",
      token_type: "bearer",
    });

    renderCallback();

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/auth/google/callback")
      );
    });

    await waitFor(() => {
      expect(mockSetToken).toHaveBeenCalledWith("test-jwt-token");
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/", { replace: true });
    });
  });

  it("shows error on API failure", async () => {
    const { api } = await import("@/api/client");
    const mockGet = vi.mocked(api.get);
    mockGet.mockRejectedValueOnce({ detail: "Invalid or expired state" });

    renderCallback();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/invalid or expired state/i);
  });

  it("shows generic error when API error has no detail", async () => {
    const { api } = await import("@/api/client");
    const mockGet = vi.mocked(api.get);
    mockGet.mockRejectedValueOnce(new Error("Network error"));

    renderCallback();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/google sign-in failed/i);
  });

  it("shows 'Back to login' link on error", async () => {
    renderCallback("?state=valid-state");
    expect(screen.getByText(/back to login/i)).toBeInTheDocument();
    expect(screen.getByText(/back to login/i).closest("a")).toHaveAttribute(
      "href",
      "/login"
    );
  });
});
