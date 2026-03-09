# GuruPix — Development Changelog

Release notes and notable changes per stage/PR.

---

## Stage 0 — Repo Bootstrap + CI + Contracts

**What changed**

- Repo skeleton created per roadmap layout: `backend/`, `frontend/`, `ml/`, `infra/`, `tests/e2e`, `tests/load`, `docs/`.
- Docs: `ARCHITECTURE.md`, `API.md`, `DEVELOPER_GUIDE.md`, `PRIVACY_AND_DATA.md`, `RUNBOOKS.md`.
- `infra/docker-compose.yml`: Postgres 16, Redis 7, Qdrant; optional MinIO commented.
- `.env.example` for backend and frontend.
- Backend: FastAPI skeleton (`app/main.py`), `pyproject.toml`, unit + integration placeholder tests.
- Frontend: Vite + React + TypeScript, ESLint, Prettier, Vitest, placeholder unit test.
- ML: `train.py` (--smoke), `embed.py`, `evaluate.py`, placeholder smoke test.
- GitHub Actions CI: lint (backend + frontend), unit (backend + frontend), integration (compose), e2e (Playwright), model smoke, security (audit).
- Pre-commit: ruff, black, mypy, pytest unit (backend); eslint, prettier, vitest (frontend).

**Tests run**

- Backend unit: `pytest tests/unit` — pass.
- Backend integration: `pytest tests/integration` — pass (placeholders).
- Frontend unit: `npm test` — pass.
- E2E: Playwright placeholder — pass when backend is up.
- Model smoke: `python train.py --smoke` — pass.

**Done when**

- `docker-compose up -d` (in infra) works.
- CI is green (all jobs pass).

---

## Stage 1 — Backend Foundation + Middleware

**What changed**

- Added `/api/v1/health` and `/api/v1/version` FastAPI endpoints with typed Pydantic response schemas.
- Implemented core middleware: `RequestIdMiddleware`, `LoggingMiddleware`, `TimingMiddleware`, and `ErrorMiddleware` with normalized error shape `{ "detail": string, "request_id": string }`.
- Introduced `app.core.version.get_app_version()` to resolve the running backend version (env var → installed package → fallback).
- Updated API and developer docs to describe the new endpoints, headers (`X-Request-Id`, `X-Response-Time-ms`), and quick local checks.

**Tests run**

- Backend unit: `cd backend && pytest tests/unit` — pass.
- Backend integration: `cd backend && pytest tests/integration` — pass.

**Done when**

- `/api/v1/health` and `/api/v1/version` are reachable and return the documented schemas.
- All four middleware components are active for requests and covered by tests.

---

## Stage 2 — Database + Migrations

**What changed**

- SQLAlchemy models for all tables: `users`, `oauth_accounts`, `profiles`, `items`, `item_availability`, `item_reviews_agg`, `events`, `models`, `contexts`, `context_events`.
- Alembic initial migration (`001_initial_schema.py`) creating all tables from scratch.
- Integration tests for migration lifecycle (upgrade/downgrade/upgrade) and insert/select smoke per table.

**Tests run**

- Backend integration: `cd backend && pytest tests/integration` — pass (12 DB tests + 1 health endpoint).

**Done when**

- Migration runs clean from scratch in CI.

---

## Stage 3 — Redis (Cache + Rate Limit + Session)

**What changed**

- Added `redis[hiredis]>=5.0` dependency to `pyproject.toml`.
- Extended `Settings` with `redis_url`, `rate_limit_per_minute`, and `session_ttl_seconds`.
- Created async Redis client (`app/clients/redis.py`) with startup/shutdown lifecycle management (fail-open if Redis is unavailable).
- Implemented **RateLimitMiddleware** (`app/middleware/rate_limit.py`):
  - Fixed-window counter per IP per route using Redis INCR + EXPIRE.
  - Configurable limit (default 100 req/min).
  - Returns 429 with standard error shape when exceeded.
  - Adds `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers.
  - Fails open if Redis is unavailable.
- Implemented **SessionMiddleware** (`app/middleware/session.py`):
  - Generates or accepts `X-Session-Id` header.
  - Stores session_id on `request.state.session_id`.
  - Echoes session_id back via response header.
  - Touches session in Redis with configurable TTL.
- Created **CacheService** (`app/clients/cache.py`):
  - Namespaced keys (`gurupix:{namespace}:{key}`).
  - JSON-serialized values with TTL.
  - `get`, `set`, `delete`, `invalidate_namespace` (SCAN-based).
- Wired Redis lifecycle into FastAPI via `lifespan` context manager in `main.py`.
- Updated middleware stack order (6 middleware total).

**Tests run**

- Backend unit (30 tests): `cd backend && pytest tests/unit -v` — all pass.
  - New: `test_rate_limit_middleware.py` (5 tests), `test_session_middleware.py` (3 tests), `test_cache.py` (7 tests), `test_config.py` (+3 tests).
- Backend integration (19 tests): `cd backend && pytest tests/integration -v` — all pass.
  - New: `test_redis_integration.py` (6 tests: ping, rate limit 429, session headers, cache round-trip, namespace invalidation).

**Done when**

- Redis is required in integration tests and passes.
- Rate limiting triggers 429 after N requests.
- Every response includes `X-Session-Id`.
- Cache set/get/delete/invalidate works end-to-end.
