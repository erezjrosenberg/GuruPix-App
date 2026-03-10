# GuruPix — Developer Guide

Setup, tests, and environment for local development. Assume a **brand new machine**; no preinstalled tools unless verified below.

## Prerequisites (Install Once)

### 1. Docker and Docker Compose

- **macOS**: Install [Docker Desktop](https://docs.docker.com/desktop/install/mac-install/). This includes Docker Compose.
- **Windows**: Install [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/).
- **Linux**: Install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

Verify:

```bash
docker --version
docker compose version
```

### 2. Node.js (for frontend)

- Install **Node.js 20 LTS** from [nodejs.org](https://nodejs.org/) or via a version manager (nvm, fnm).
- Verify: `node --version` (v20.x) and `npm --version`.

### 3. Python (for backend and ML)

- Install **Python 3.11+** from [python.org](https://www.python.org/downloads/) or via pyenv.
- Verify: `python3 --version` (3.11 or higher).

### 4. Git

- Install from [git-scm.com](https://git-scm.com/). Verify: `git --version`.

## Repository Layout

See `docs/ARCHITECTURE.md` and the root `ROADMAP_GuruPix_System_Design.md` for the full layout. Key dirs:

- `backend/` — FastAPI app
- `frontend/` — React app
- `ml/` — Training, embedding, evaluation
- `infra/` — docker-compose.yml, k8s
- `tests/` — E2E (Playwright), load
- `docs/` — Architecture, API, privacy, runbooks

## Environment Setup

### 1. Clone and enter the repo

```bash
cd "/Users/erezrosenberg/Desktop/GuruPix App"
```

(Or your actual clone path.)

### 2. Copy environment examples

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit `backend/.env` and `frontend/.env.local` if you need to override defaults (e.g. ports, URLs).

**Auth-related env vars (Stage 4+)** — add to `backend/.env` for authentication:

- `SECRET_KEY` — secret for JWT signing (required for auth)
- `JWT_ALGORITHM` — e.g. `HS256` (default)
- `JWT_EXPIRE_MINUTES` — token expiry (e.g. `60`)
- `GOOGLE_CLIENT_ID` — for Google OAuth
- `GOOGLE_CLIENT_SECRET` — for Google OAuth
- `OAUTH_CALLBACK_BASE_URL` — base URL for OAuth callback (e.g. `http://localhost:8000`)

### 3. Start infrastructure (Postgres, Redis, Qdrant)

```bash
cd infra
docker compose up -d
cd ..
```

Verify containers: `docker compose -f infra/docker-compose.yml ps`. All services should be “Up”.

### 4. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cd ..
```

### 5. Frontend setup

```bash
cd frontend
npm install
cd ..
```

### 6. ML (optional for Stage 0)

```bash
cd ml
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

## Running Locally

### Start infrastructure (once per dev session)

```bash
cd infra && docker compose up -d && cd ..
```

### Run backend

```bash
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
```

Backend: http://localhost:8000

Quick checks (open in a browser or use curl):

- `http://localhost:8000/api/v1/health` → `{ "status": "ok" }`
- `http://localhost:8000/api/v1/version` → `{ "version": "..." }`

### Run frontend (separate terminal)

```bash
cd frontend && npm run dev
```

Frontend: http://localhost:5173 (or port shown in terminal)

### Run ML smoke (when implemented)

```bash
cd ml && source .venv/bin/activate && python train.py --smoke
```

## Tests

| Scope | Command | Notes |
|-------|--------|--------|
| Backend unit | `cd backend && pytest tests/unit` | No services required |
| Backend integration | `cd backend && pytest tests/integration` | Requires docker-compose up |
| Frontend unit | `cd frontend && npm test` | Vitest |
| E2E | `cd tests/e2e && npx playwright test` | Backend + frontend running; Playwright installed |
| Model smoke | `cd ml && python train.py --smoke` | ML deps + optional data |

## Linting and Formatting

- **Backend**: `cd backend && ruff check . && black . && mypy app`
- **Frontend**: `cd frontend && npm run lint`
- **Pre-commit**: From repo root, `pre-commit run --all-files` (after `pre-commit install`)

## CI

GitHub Actions runs on push/PR:

1. Lint (backend + frontend)
2. Unit tests (backend + frontend)
3. Integration tests (compose)
4. E2E tests (Playwright)
5. Model smoke tests
6. Security scan

Do not merge if any job fails. See `.github/workflows/ci.yml`.

## Troubleshooting

- **Port in use**: Change ports in `infra/docker-compose.yml` or in `.env` (e.g. `POSTGRES_PORT`, `REDIS_PORT`).
- **Database connection refused**: Ensure `docker compose up -d` in `infra` and that `DATABASE_URL` in `backend/.env` matches compose (host, port, user, password, dbname).
- **Frontend can’t reach backend**: Set `VITE_API_BASE_URL` in `frontend/.env.local` to your backend URL (e.g. http://localhost:8000).

For more detail, see `ROADMAP_GuruPix_System_Design.md` and `docs/ARCHITECTURE.md`.

**Beginner-friendly code walkthrough:** After Stage 1, read `docs/STAGE1_CODE_WALKTHROUGH.md` for a line-by-line explanation of the backend health/version endpoints and all middleware.

### Before starting Stage 2

- Run backend lint and tests from a clean state:  
  `cd backend && ruff check . && black --check . && mypy app && pytest tests/unit tests/integration -v`
- Ensure infrastructure starts: `cd infra && docker compose up -d` (Postgres is required for Stage 2 migrations).
- Your `backend/.env` should already have `DATABASE_URL` (see `backend/.env.example`); Stage 2 will add SQLAlchemy and Alembic and use it.

### Before starting Stage 4

- Ensure infrastructure is running (Postgres **and** Redis required):
  `cd infra && docker compose up -d`
- Run all backend tests to confirm a clean baseline:
  `cd backend && .venv/bin/python -m pytest tests/unit tests/integration -v`
- Verify Redis is reachable: `redis-cli ping` should return `PONG`.
- Your `backend/.env` should include `REDIS_URL=redis://localhost:6379/0` (see `backend/.env.example`).
- Stage 3 added two new middleware (`RateLimitMiddleware`, `SessionMiddleware`) and a `CacheService` — all backed by Redis. Stage 4 will build on these for auth sessions.

### Before starting Stage 5

- Ensure Stage 4 auth is working: signup, login, and `GET /auth/me` with Bearer token.
- Run all backend tests to confirm a clean baseline:
  `cd backend && .venv/bin/python -m pytest tests/unit tests/integration -v`
- Your `backend/.env` should include auth vars (`SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`) and, for Google OAuth, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `OAUTH_CALLBACK_BASE_URL`.
