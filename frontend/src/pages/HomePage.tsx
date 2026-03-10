import { useAuth } from "@/hooks/useAuth";

export default function HomePage() {
  const { user, loading, logout } = useAuth();

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
      <p>Welcome! Recommendations are coming soon.</p>
    </div>
  );
}
