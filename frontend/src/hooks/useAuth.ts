import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, clearToken, setToken } from "@/api/client";

interface User {
  id: string;
  email: string;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface GoogleStartResponse {
  authorization_url: string;
}

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export function useAuth() {
  const navigate = useNavigate();
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("gurupix_token");
    if (!token) {
      setState({ user: null, loading: false, error: null });
      return;
    }
    try {
      const user = await api.get<User>("/api/v1/auth/me");
      setState({ user, loading: false, error: null });
    } catch {
      clearToken();
      setState({ user: null, loading: false, error: null });
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const signup = useCallback(
    async (email: string, password: string) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const data = await api.post<TokenResponse>("/api/v1/auth/signup", {
          email,
          password,
        });
        setToken(data.access_token);
        await fetchUser();
        navigate("/");
      } catch (err: unknown) {
        const msg =
          err && typeof err === "object" && "detail" in err
            ? (err as { detail: string }).detail
            : "Signup failed";
        setState((s) => ({ ...s, loading: false, error: msg }));
      }
    },
    [fetchUser, navigate],
  );

  const login = useCallback(
    async (email: string, password: string) => {
      setState((s) => ({ ...s, loading: true, error: null }));
      try {
        const data = await api.post<TokenResponse>("/api/v1/auth/login", {
          email,
          password,
        });
        setToken(data.access_token);
        await fetchUser();
        navigate("/");
      } catch (err: unknown) {
        const msg =
          err && typeof err === "object" && "detail" in err
            ? (err as { detail: string }).detail
            : "Login failed";
        setState((s) => ({ ...s, loading: false, error: msg }));
      }
    },
    [fetchUser, navigate],
  );

  const startGoogleLogin = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.get<GoogleStartResponse>(
        "/api/v1/auth/google/start",
      );
      window.location.href = data.authorization_url;
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "detail" in err
          ? (err as { detail: string }).detail
          : "Google login unavailable";
      setState((s) => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setState({ user: null, loading: false, error: null });
    navigate("/login");
  }, [navigate]);

  return {
    user: state.user,
    loading: state.loading,
    error: state.error,
    signup,
    login,
    startGoogleLogin,
    logout,
  };
}
