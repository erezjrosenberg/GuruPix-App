import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import { api, clearToken, setToken } from "@/api/client";

interface User {
  id: string;
  email: string;
  created_at: string;
  is_admin?: boolean;
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

interface AuthContextValue extends AuthState {
  signup: (email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  startGoogleLogin: () => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
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
      setState((s) => ({ ...s, user, loading: false, error: null }));
    } catch {
      clearToken();
      setState({ user: null, loading: false, error: null });
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  // Refetch when token is set from outside (e.g. Google OAuth callback)
  useEffect(() => {
    const handler = () => fetchUser();
    window.addEventListener("gurupix:token-set", handler);
    return () => window.removeEventListener("gurupix:token-set", handler);
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
    [fetchUser, navigate]
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
            : "Invalid email or password";
        setState((s) => ({ ...s, loading: false, error: msg }));
      }
    },
    [fetchUser, navigate]
  );

  const startGoogleLogin = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.get<GoogleStartResponse>(
        "/api/v1/auth/google/start"
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

  const value: AuthContextValue = {
    ...state,
    signup,
    login,
    startGoogleLogin,
    logout,
    fetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export { AuthContext };
