import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  localStorage.removeItem("gurupix_token");
  vi.restoreAllMocks();
});

describe("App", () => {
  it("renders GuruPix title on the home page", async () => {
    render(<App />);
    const heading = await screen.findByRole("heading", { name: /gurupix/i });
    expect(heading).toBeInTheDocument();
  });

  it("shows 'Get Started' link when not logged in", async () => {
    render(<App />);
    const link = await screen.findByText(/get started/i);
    expect(link).toBeInTheDocument();
  });
});
