import { FormEvent, useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login, signup, startGoogleLogin, loading, error } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (isSignup) {
      signup(email, password);
    } else {
      login(email, password);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", padding: "0 16px" }}>
      <h1 style={{ textAlign: "center", marginBottom: 8 }}>GuruPix</h1>
      <p style={{ textAlign: "center", color: "#666", marginBottom: 32 }}>
        Hyper-personalized movie & TV recommendations
      </p>

      <form onSubmit={handleSubmit}>
        <h2 style={{ marginBottom: 16 }}>{isSignup ? "Sign Up" : "Log In"}</h2>

        {error && (
          <div
            role="alert"
            style={{
              padding: "8px 12px",
              marginBottom: 12,
              background: "#fee",
              border: "1px solid #c00",
              borderRadius: 4,
              color: "#900",
            }}
          >
            {error}
          </div>
        )}

        <label htmlFor="email" style={{ display: "block", marginBottom: 4 }}>
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            width: "100%",
            padding: 8,
            marginBottom: 12,
            borderRadius: 4,
            border: "1px solid #ccc",
          }}
        />

        <label
          htmlFor="password"
          style={{ display: "block", marginBottom: 4 }}
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          minLength={8}
          autoComplete={isSignup ? "new-password" : "current-password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: "100%",
            padding: 8,
            marginBottom: 16,
            borderRadius: 4,
            border: "1px solid #ccc",
          }}
        />

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: 10,
            background: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: loading ? "not-allowed" : "pointer",
            fontWeight: 600,
          }}
        >
          {loading ? "..." : isSignup ? "Create Account" : "Log In"}
        </button>
      </form>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          margin: "20px 0",
          gap: 8,
        }}
      >
        <hr style={{ flex: 1, border: "none", borderTop: "1px solid #ddd" }} />
        <span style={{ color: "#999", fontSize: 13 }}>or</span>
        <hr style={{ flex: 1, border: "none", borderTop: "1px solid #ddd" }} />
      </div>

      <button
        type="button"
        onClick={startGoogleLogin}
        disabled={loading}
        style={{
          width: "100%",
          padding: 10,
          background: "#fff",
          color: "#333",
          border: "1px solid #ddd",
          borderRadius: 4,
          cursor: loading ? "not-allowed" : "pointer",
          fontWeight: 600,
        }}
      >
        Continue with Google
      </button>

      <p style={{ textAlign: "center", marginTop: 20, fontSize: 14 }}>
        {isSignup ? "Already have an account?" : "Need an account?"}{" "}
        <button
          type="button"
          onClick={() => setIsSignup(!isSignup)}
          style={{
            background: "none",
            border: "none",
            color: "#2563eb",
            cursor: "pointer",
            textDecoration: "underline",
            padding: 0,
          }}
        >
          {isSignup ? "Log in" : "Sign up"}
        </button>
      </p>
    </div>
  );
}
