# GuruPix — API Contract

This document defines the endpoint contract table. Endpoints are added in later stages; this is the single source of truth for API shape.

## Base URL

- Local: `http://localhost:8000` (backend)
- API prefix: `/api/v1` (applied starting in Stage 1)

## Endpoints (by Stage)

### Stage 1 — System + Health

- **Base**: `http://localhost:8000/api/v1`

| Method | Path        | Description        | Response shape                |
|--------|-------------|--------------------|-------------------------------|
| GET    | `/health`   | Liveness check     | `{ "status": "ok" }`          |
| GET    | `/version`  | Backend version    | `{ "version": "<string>" }`   |

All responses include these headers:

| Header | Description |
|--------|-------------|
| `X-Request-Id` | Incoming value echoed or generated server-side (UUID-4) |
| `X-Response-Time-ms` | Stringified milliseconds (e.g. `"12.34"`) |
| `X-Session-Id` | Session identifier — client value echoed or new UUID-4 generated (Stage 3) |
| `X-RateLimit-Limit` | Max requests allowed per window (Stage 3, only when Redis is available) |
| `X-RateLimit-Remaining` | Requests remaining in the current window (Stage 3) |
| `X-RateLimit-Reset` | Unix epoch second when the window resets (Stage 3) |

Rate limiting returns `429 Too Many Requests` with the standard error shape when exceeded.

### Stage 4 — Authentication

Auth uses **JWT bearer tokens** (not session cookies). Include `Authorization: Bearer <token>` for protected endpoints.

| Method | Path | Description | Auth | Request | Response | Status codes |
|--------|------|-------------|------|---------|----------|--------------|
| POST | `/auth/signup` | Create account | No | `{ "email": string, "password": string }` (password min 8 chars) | `{ "access_token": string, "token_type": "bearer" }` | 201 success, 409 email exists, 422 validation error |
| POST | `/auth/login` | Authenticate | No | `{ "email": string, "password": string }` | `{ "access_token": string, "token_type": "bearer" }` | 200 success, 401 bad credentials |
| GET | `/auth/me` | Current user | Yes (Bearer) | — | `{ "id": string, "email": string, "created_at": string }` | 200 success, 401 missing/invalid token |
| GET | `/auth/google/start` | Start Google OAuth | No | — | `{ "authorization_url": string }` | 200 success |
| GET | `/auth/google/callback` | OAuth callback | No | Query: `code`, `state` | Redirect or JWT response | 200 success, 400 missing/invalid code/state |

**Headers for protected endpoints**

| Header | Description |
|--------|-------------|
| `Authorization` | `Bearer <access_token>` — required for `/auth/me` and other protected routes |

**OAuth flow**

1. Client calls `GET /auth/google/start` → receives `authorization_url`.
2. User visits URL, signs in with Google, is redirected to callback with `code` and `state`.
3. Client calls `GET /auth/google/callback?code=...&state=...` → receives JWT (state validated via Redis).

### Later stages

- **Stage 5**: GET /availability, GET /reviews/aggregate, POST /ingest/items (admin)
- **Stage 6**: POST /profiles, GET /profiles/me, PATCH /profiles/me, DELETE /profiles/me, POST /profiles/me/export
- **Stage 7**: POST /contexts/parse, POST /contexts, GET /contexts, DELETE /contexts/{id}, POST /recommendations/contextual
- **Stage 8**: GET /recommendations, GET /recommendations/{item_id}/explain
- **Stage 9**: POST /recommendations/{item_id}/feedback
- **Stage 12**: POST /connectors/ai-profile/import, DELETE /connectors/ai-profile

## Common Response Shapes

- **Error**: `{ "detail": string, "request_id": string }` (normalized by ErrorMiddleware)
- **Pagination**: `{ "items": [], "total": number, "page": number, "page_size": number }` (where applicable)

## Request Conventions

- **Request ID**: Client may send `X-Request-Id`; otherwise server generates one. Response headers include `X-Request-Id`, `X-Response-Time-ms`.
- **Auth**: Bearer token in `Authorization: Bearer <token>` header (Stage 4).

This table will be updated as each stage is implemented.
