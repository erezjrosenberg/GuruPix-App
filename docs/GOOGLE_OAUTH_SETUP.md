# Google OAuth Setup Guide

This guide walks you through creating Google OAuth credentials and configuring GuruPix for "Continue with Google" sign-in.

## End-to-End Flow Overview

1. **User clicks "Continue with Google"** on the login page.
2. **Frontend** calls `GET /api/v1/auth/google/start` → backend returns an `authorization_url`.
3. **User is redirected** to Google's consent screen (via `window.location.href`).
4. **User signs in** with Google and approves the requested scopes (`openid`, `email`, `profile`).
5. **Google redirects** the user's browser to your **Authorized redirect URI** with `?code=...&state=...`.
6. **Frontend** (`GoogleCallbackPage` at `/auth/google/callback`) receives the redirect, reads `code` and `state` from the URL, and calls `GET /api/v1/auth/google/callback?code=...&state=...` on the backend.
7. **Backend** validates `state` (CSRF protection via Redis), exchanges the `code` for tokens with Google, extracts user info from the `id_token`, creates or links the user in the DB, and returns a JWT.
8. **Frontend** stores the JWT in `localStorage` and redirects the user to the home page.

### Key Components

| Component | Path | Purpose |
|-----------|------|---------|
| Backend start | `GET /api/v1/auth/google/start` | Returns Google OAuth URL with state |
| Backend callback | `GET /api/v1/auth/google/callback` | Exchanges code for tokens, creates user, returns JWT |
| Frontend callback | `/auth/google/callback` | Receives redirect from Google, calls backend, stores JWT |
| Google OAuth client | `backend/app/clients/google_oauth.py` | Builds auth URL, exchanges code, decodes id_token |

### Redirect URI

The **redirect URI** is where Google sends the user after sign-in. It must:

- Match **exactly** what you configure in Google Cloud Console (including trailing slashes, ports, scheme).
- For local dev with frontend on port 5173: `http://localhost:5173/auth/google/callback`
- For production: `https://yourdomain.com/auth/google/callback`

---

## Creating Google OAuth Credentials

### Step 1: Open Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.

### Step 2: Create or Select a Project

1. Click the project dropdown at the top.
2. Click **New Project** (or select an existing one).
3. Name it (e.g. "GuruPix") and click **Create**.

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen** (or [direct link](https://console.cloud.google.com/apis/credentials/consent)).
2. Choose **External** (for any Google user) or **Internal** (for your org only).
3. Fill in:
   - **App name**: GuruPix (or your app name)
   - **User support email**: your email
   - **Developer contact email**: your email
4. Under **Scopes**, add:
   - `openid`
   - `email`
   - `profile`
5. Save and continue through the wizard.

### Step 4: Create OAuth 2.0 Client ID

1. Go to **APIs & Services** → **Credentials** (or [direct link](https://console.cloud.google.com/apis/credentials)).
2. Click **+ Create Credentials** → **OAuth client ID**.
3. Select **Web application** as the application type.
4. **Name**: e.g. "GuruPix Web Client".
5. **Authorized JavaScript origins** (add your frontend origins):
   - Local dev: `http://localhost:5173`
   - Production: `https://yourdomain.com`
6. **Authorized redirect URIs** (add exactly what your app uses):
   - Local dev: `http://localhost:5173/auth/google/callback`
   - Production: `https://yourdomain.com/auth/google/callback`
7. Click **Create**.
8. **Copy the Client ID and Client Secret** — the secret is shown only once. Store them securely.

### Step 5: Configure GuruPix

Add to `backend/.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:5173/auth/google/callback
```

For production:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=https://yourdomain.com/auth/google/callback
```

### Step 6: Restart and Test

1. Restart the backend (`npm run dev:full` or your dev command).
2. Open the login page and click **Continue with Google**.
3. You should be redirected to Google, then back to the app with a JWT stored.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `redirect_uri_mismatch` | Redirect URI in request doesn't match Google Console | Add the exact URI to **Authorized redirect URIs** in Google Console. Ensure `OAUTH_REDIRECT_URI` in `.env` matches. |
| `origin_mismatch` | Request from unregistered origin | Add the origin (e.g. `http://localhost:5173`) to **Authorized JavaScript origins**. |
| `OAuth unavailable — state store is not reachable` | Redis not running | Start Redis (`docker compose up -d` in `infra/`). |
| `Invalid or expired state` | State expired (10 min) or reused | Try again; ensure you're not reusing the same auth URL. |
| `Missing authorization code or state parameter` | User landed on callback without code/state | Check that the redirect URI is correct and that Google is redirecting there. |

---

## Security Notes

- Never commit `GOOGLE_CLIENT_SECRET` to version control.
- Use environment variables or a secrets manager in production.
- The `state` parameter prevents CSRF; it is stored in Redis with a 10-minute TTL.
- For production, use HTTPS and ensure your redirect URI uses `https://`.
