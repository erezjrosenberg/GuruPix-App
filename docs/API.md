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

### Later stages

- **Stage 4**: POST /auth/signup, POST /auth/login, GET /auth/google/start, GET /auth/google/callback
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
- **Auth**: Bearer token in `Authorization` header or session cookie (TBD in Stage 4).

This table will be updated as each stage is implemented.
