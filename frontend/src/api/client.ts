/**
 * API client with interceptors for auth token and request-id.
 *
 * Attaches `Authorization: Bearer <token>` and `X-Request-Id` to every
 * request. Normalises error responses and handles 401 (expired token).
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function uuid4(): string {
  return crypto.randomUUID();
}

function getToken(): string | null {
  return localStorage.getItem("gurupix_token");
}

export function setToken(token: string): void {
  localStorage.setItem("gurupix_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("gurupix_token");
}

export interface ApiError {
  detail: string;
  request_id?: string;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Request-Id": uuid4(),
    ...(options.headers as Record<string, string> | undefined),
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body: ApiError = await res.json().catch(() => ({
      detail: res.statusText,
    }));

    // Global 401 redirect only for protected endpoints — not for login/signup
    // where 401 means "bad credentials" and should be shown as an error.
    const isAuthEndpoint =
      path.includes("/auth/login") || path.includes("/auth/signup");
    if (res.status === 401 && !isAuthEndpoint) {
      clearToken();
      window.location.href = "/login";
    }

    throw body;
  }

  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
};
