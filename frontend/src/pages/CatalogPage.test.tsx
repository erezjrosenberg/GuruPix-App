/**
 * Unit tests for CatalogPage (Stage 5.3–5.4).
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import CatalogPage from "./CatalogPage";
import * as api from "@/api/client";

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

function renderCatalog() {
  return render(
    <BrowserRouter>
      <CatalogPage />
    </BrowserRouter>,
  );
}

describe("CatalogPage", () => {
  it("shows loading state initially", () => {
    vi.mocked(api.api.get).mockImplementation(
      () => new Promise(() => {}),
    );
    renderCatalog();
    expect(screen.getByText(/loading catalog/i)).toBeInTheDocument();
  });

  it("displays items with availability and reviews", async () => {
    vi.mocked(api.api.get)
      .mockResolvedValueOnce([
        {
          id: 1,
          type: "movie",
          title: "Test Movie",
          synopsis: "A test.",
          genres: ["Comedy"],
          runtime: 90,
          release_date: "2024-01-01",
          language: "en",
        },
      ])
      .mockResolvedValueOnce([
        { provider: "Netflix", region: "US", url: "https://n.com", availability_type: "stream" },
      ])
      .mockResolvedValueOnce([
        { source: "RT_CRITICS", score: 91, scale: 100, normalized_score: 91 },
      ]);

    renderCatalog();

    await waitFor(() => {
      expect(screen.getByText("Test Movie")).toBeInTheDocument();
    });
    expect(screen.getByText("Where to watch:")).toBeInTheDocument();
    expect(screen.getByText("Scores from:")).toBeInTheDocument();
  });

  it("shows empty state when no items", async () => {
    vi.mocked(api.api.get)
      .mockResolvedValueOnce([]);

    renderCatalog();

    await waitFor(() => {
      expect(screen.getByText(/no items in catalog|run seed ingestion/i)).toBeInTheDocument();
    });
  });
});
