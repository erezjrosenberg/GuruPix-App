import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";
import { api } from "@/api/client";

export default function OnboardingPage() {
  const { user, loading: authLoading } = useAuth();
  const { needsOnboarding, fetchProfile } = useProfile();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [region, setRegion] = useState("US");
  const [consent, setConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect if already has profile
  if (!authLoading && user && !needsOnboarding) {
    navigate("/", { replace: true });
    return null;
  }

  // Redirect if not logged in
  if (!authLoading && !user) {
    navigate("/login", { replace: true });
    return null;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!consent) {
      setError("You must accept data processing to continue.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/v1/profiles/me", {
        display_name: displayName || null,
        bio: bio || null,
        region: region || null,
        languages: null,
        providers: null,
        consent_data_processing: true,
      });
      await fetchProfile();
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "detail" in err
          ? (err as { detail: string }).detail
          : "Failed to save. Please try again.";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (authLoading) {
    return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  }

  return (
    <div style={{ maxWidth: 480, margin: "60px auto", padding: "0 20px" }}>
      <h1 style={{ textAlign: "center", marginBottom: 8 }}>
        Welcome to GuruPix
      </h1>
      <p style={{ textAlign: "center", color: "#666", marginBottom: 32 }}>
        Tell us a bit about yourself so we can personalize your experience.
      </p>

      <form onSubmit={handleSubmit}>
        {error && (
          <div
            role="alert"
            style={{
              padding: "10px 14px",
              marginBottom: 16,
              background: "#fee",
              border: "1px solid #c00",
              borderRadius: 6,
              color: "#900",
            }}
          >
            {error}
          </div>
        )}

        <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
          Display name (optional)
        </label>
        <input
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="How should we call you?"
          maxLength={100}
          style={{
            width: "100%",
            padding: 10,
            marginBottom: 16,
            borderRadius: 6,
            border: "1px solid #ccc",
          }}
        />

        <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
          Bio (optional)
        </label>
        <textarea
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder="What kind of movies or shows do you enjoy?"
          maxLength={500}
          rows={3}
          style={{
            width: "100%",
            padding: 10,
            marginBottom: 16,
            borderRadius: 6,
            border: "1px solid #ccc",
            resize: "vertical",
          }}
        />

        <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
          Region
        </label>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          style={{
            width: "100%",
            padding: 10,
            marginBottom: 24,
            borderRadius: 6,
            border: "1px solid #ccc",
          }}
        >
          <option value="US">United States</option>
          <option value="UK">United Kingdom</option>
          <option value="IL">Israel</option>
          <option value="DE">Germany</option>
          <option value="FR">France</option>
          <option value="CA">Canada</option>
        </select>

        <div
          style={{
            padding: 16,
            marginBottom: 24,
            background: "#f8f9fa",
            borderRadius: 6,
            border: "1px solid #eee",
          }}
        >
          <label
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 10,
              cursor: "pointer",
            }}
          >
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              style={{ marginTop: 4 }}
            />
            <span>
              I agree to GuruPix processing my preferences and usage data to
              provide personalized recommendations. I understand this data is
              used solely to improve my experience.{" "}
              <a href="/privacy" style={{ color: "#2563eb" }}>
                Privacy policy
              </a>
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={submitting || !consent}
          style={{
            width: "100%",
            padding: 12,
            background: consent ? "#2563eb" : "#ccc",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            cursor: consent && !submitting ? "pointer" : "not-allowed",
            fontWeight: 600,
          }}
        >
          {submitting ? "Saving..." : "Continue"}
        </button>
      </form>
    </div>
  );
}
