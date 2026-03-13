import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/useProfile";

const SAVE_DEBOUNCE_MS = 800;

export default function HomePage() {
  const { user, loading, logout } = useAuth();
  const { profile, needsOnboarding, patchProfile, loading: profileLoading } = useProfile();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [region, setRegion] = useState("US");
  const [saved, setSaved] = useState(false);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Redirect new users to onboarding
  useEffect(() => {
    if (!loading && !profileLoading && user && needsOnboarding) {
      navigate("/onboarding", { replace: true });
    }
  }, [loading, profileLoading, user, needsOnboarding, navigate]);

  // Sync form from profile
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name ?? "");
      setBio(profile.bio ?? "");
      setRegion(profile.region ?? "US");
    }
  }, [profile]);

  // Autosave on change
  useEffect(() => {
    if (!profile || !user) return;

    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);

    const currentDisplayName = displayName;
    const currentBio = bio;
    const currentRegion = region;

    const hasChanges =
      (profile.display_name ?? "") !== currentDisplayName ||
      (profile.bio ?? "") !== currentBio ||
      (profile.region ?? "US") !== currentRegion;

    if (!hasChanges) return;

    saveTimeoutRef.current = setTimeout(() => {
      patchProfile({
        display_name: currentDisplayName || null,
        bio: currentBio || null,
        region: currentRegion || null,
      }).then(() => {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      });
    }, SAVE_DEBOUNCE_MS);

    return () => {
      if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    };
  }, [displayName, bio, region, profile, user, patchProfile]);

  if (loading) {
    return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  }

  if (!user) {
    return (
      <div style={{ maxWidth: 500, margin: "80px auto", textAlign: "center" }}>
        <h1>GuruPix</h1>
        <p>Hyper-personalized movie & TV recommendations.</p>
        <a
          href="/login"
          style={{
            display: "inline-block",
            marginTop: 20,
            padding: "10px 24px",
            background: "#2563eb",
            color: "#fff",
            borderRadius: 4,
            textDecoration: "none",
            fontWeight: 600,
          }}
        >
          Get Started
        </a>
      </div>
    );
  }

  if (profileLoading || needsOnboarding) {
    return <p style={{ textAlign: "center", marginTop: 80 }}>Loading...</p>;
  }

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", padding: "0 16px" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <h1 style={{ margin: 0 }}>GuruPix</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 14, color: "#666" }}>{user.email}</span>
          <button
            onClick={logout}
            style={{
              padding: "6px 14px",
              background: "none",
              border: "1px solid #ddd",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Log out
          </button>
        </div>
      </header>

      <section
        style={{
          marginBottom: 32,
          padding: 20,
          background: "#f8f9fa",
          borderRadius: 8,
          border: "1px solid #eee",
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 16 }}>Your profile</h2>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>
            Email (read-only)
          </label>
          <input
            type="email"
            value={user.email}
            readOnly
            disabled
            style={{
              width: "100%",
              padding: 8,
              background: "#eee",
              border: "1px solid #ccc",
              borderRadius: 4,
              color: "#666",
            }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>
            Display name
          </label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="How should we call you?"
            maxLength={100}
            style={{
              width: "100%",
              padding: 8,
              border: "1px solid #ccc",
              borderRadius: 4,
            }}
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>
            Bio
          </label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="What kind of movies or shows do you enjoy?"
            maxLength={500}
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              border: "1px solid #ccc",
              borderRadius: 4,
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ marginBottom: 0 }}>
          <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 4 }}>
            Region
          </label>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            style={{
              width: "100%",
              padding: 8,
              border: "1px solid #ccc",
              borderRadius: 4,
            }}
          >
            <option value="US">United States</option>
            <option value="UK">United Kingdom</option>
            <option value="IL">Israel</option>
            <option value="DE">Germany</option>
            <option value="FR">France</option>
            <option value="CA">Canada</option>
          </select>
        </div>

        {saved && (
          <p style={{ marginTop: 12, fontSize: 13, color: "#16a34a" }}>Changes saved.</p>
        )}
      </section>

      <p>Welcome! Recommendations are coming soon.</p>
      <Link
        to="/catalog"
        style={{
          display: "inline-block",
          marginTop: 16,
          color: "#2563eb",
          textDecoration: "none",
          fontWeight: 500,
        }}
      >
        Browse catalog →
      </Link>
    </div>
  );
}
