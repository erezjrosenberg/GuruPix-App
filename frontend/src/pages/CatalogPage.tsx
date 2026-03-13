/**
 * Catalog page — displays items with where-to-watch availability (Stage 5.3).
 *
 * Fetches items from GET /items and availability from GET /availability
 * per item. Uses default region US.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";

interface Item {
  id: number;
  type: string;
  title: string;
  synopsis: string | null;
  genres: string[] | null;
  runtime: number | null;
  release_date: string | null;
}

interface Availability {
  provider: string;
  region: string;
  url: string | null;
  availability_type: string;
}

interface ReviewAggregate {
  source: string;
  score: number;
  scale: number;
  normalized_score: number | null;
}

const DEFAULT_REGION = "US";

export default function CatalogPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [availabilityByItem, setAvailabilityByItem] = useState<
    Record<number, Availability[]>
  >({});
  const [reviewsByItem, setReviewsByItem] = useState<
    Record<number, ReviewAggregate[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const itemsData = await api.get<Item[]>("/api/v1/items");
        if (cancelled) return;
        setItems(itemsData);

        const avail: Record<number, Availability[]> = {};
        const revs: Record<number, ReviewAggregate[]> = {};
        for (const item of itemsData) {
          const [av, rv] = await Promise.all([
            api.get<Availability[]>(
              `/api/v1/availability?item_id=${item.id}&region=${DEFAULT_REGION}`
            ),
            api.get<ReviewAggregate[]>(
              `/api/v1/reviews/aggregate?item_id=${item.id}`
            ),
          ]);
          if (cancelled) return;
          avail[item.id] = av;
          revs[item.id] = rv;
        }
        setAvailabilityByItem(avail);
        setReviewsByItem(revs);
      } catch (e) {
        if (!cancelled) {
          setError(
            e && typeof e === "object" && "detail" in e
              ? String((e as { detail: string }).detail)
              : "Failed to load catalog"
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <p style={{ textAlign: "center", marginTop: 80 }}>Loading catalog...</p>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: "40px auto", padding: 16 }}>
        <p role="alert" style={{ color: "#c00" }}>
          {error}
        </p>
        <Link to="/">Back to home</Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 16px" }}>
      <header style={{ marginBottom: 24 }}>
        <Link
          to="/"
          style={{
            display: "inline-block",
            marginBottom: 16,
            color: "#2563eb",
            textDecoration: "none",
          }}
        >
          ← Back to home
        </Link>
        <h1 style={{ margin: 0 }}>Catalog</h1>
        <p style={{ margin: "8px 0 0", color: "#666" }}>
          Where to watch in {DEFAULT_REGION}
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gap: 24,
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        }}
      >
        {items.map((item) => {
          const avail = availabilityByItem[item.id] ?? [];
          const reviews = reviewsByItem[item.id] ?? [];
          return (
            <article
              key={item.id}
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                padding: 16,
                backgroundColor: "#fff",
              }}
            >
              <h2 style={{ margin: "0 0 8px", fontSize: 18 }}>{item.title}</h2>
              <p style={{ margin: "0 0 8px", fontSize: 12, color: "#666" }}>
                {item.type} {item.runtime ? `• ${item.runtime} min` : ""}
              </p>
              {reviews.length > 0 && (
                <div
                  style={{
                    marginBottom: 8,
                    fontSize: 12,
                    color: "#6b7280",
                  }}
                >
                  <strong>Scores from:</strong>{" "}
                  {reviews
                    .map(
                      (r) =>
                        `${r.source.replace(/_/g, " ")} ${
                          r.normalized_score ??
                          Math.round((r.score / r.scale) * 100)
                        }%`
                    )
                    .join(" / ")}
                </div>
              )}
              {item.synopsis && (
                <p
                  style={{
                    margin: "0 0 12px",
                    fontSize: 14,
                    lineHeight: 1.4,
                    color: "#374151",
                  }}
                >
                  {item.synopsis.slice(0, 120)}
                  {item.synopsis.length > 120 ? "…" : ""}
                </p>
              )}
              {avail.length > 0 && (
                <div
                  style={{
                    marginTop: 12,
                    paddingTop: 12,
                    borderTop: "1px solid #e5e7eb",
                  }}
                >
                  <strong style={{ fontSize: 12, color: "#6b7280" }}>
                    Where to watch:
                  </strong>
                  <ul style={{ margin: "4px 0 0", paddingLeft: 20 }}>
                    {avail.map((a) => (
                      <li key={`${a.provider}-${a.availability_type}`}>
                        {a.url ? (
                          <a
                            href={a.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ fontSize: 13 }}
                          >
                            {a.provider}
                          </a>
                        ) : (
                          <span style={{ fontSize: 13 }}>{a.provider}</span>
                        )}
                        <span
                          style={{
                            fontSize: 11,
                            color: "#9ca3af",
                            marginLeft: 4,
                          }}
                        >
                          ({a.availability_type})
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          );
        })}
      </div>

      {items.length === 0 && (
        <p style={{ textAlign: "center", color: "#6b7280" }}>
          No items in catalog. Run seed ingestion as admin.
        </p>
      )}
    </div>
  );
}
