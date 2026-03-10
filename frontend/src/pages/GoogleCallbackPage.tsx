import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, setToken } from "@/api/client";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export default function GoogleCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code || !state) {
      setError("Missing authorization code or state parameter.");
      return;
    }

    api
      .get<TokenResponse>(
        `/api/v1/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
      )
      .then((data) => {
        setToken(data.access_token);
        navigate("/", { replace: true });
      })
      .catch((err: unknown) => {
        const msg =
          err && typeof err === "object" && "detail" in err
            ? (err as { detail: string }).detail
            : "Google sign-in failed";
        setError(msg);
      });
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div style={{ maxWidth: 400, margin: "80px auto", textAlign: "center" }}>
        <h2>Sign-in Error</h2>
        <p role="alert" style={{ color: "#c00" }}>
          {error}
        </p>
        <a href="/login">Back to login</a>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto", textAlign: "center" }}>
      <p>Signing you in...</p>
    </div>
  );
}
