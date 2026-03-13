# GuruPix

Hyper-personalized movie & TV recommendation app. Built in staged, test-gated increments per `ROADMAP_GuruPix_System_Design.md`.


## Common commands

| Command | Description |
|---------|-------------|
| `npm run dev:full` | One-command setup and run: starts infra, backend, and frontend together |
| `npm run dev` | Start backend + frontend (requires infra already running) |
| `npm test` | Run all tests (backend, frontend, ML, E2E) |

## Stage 0 complete

- Repo skeleton, docs, docker-compose, CI (GitHub Actions), and pre-commit are in place.
- **New to the project?** Start with **[docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)** for setup on a new machine (Docker, Node, Python, Git) and how to run backend, frontend, and tests locally.

## Quick start (after prerequisites)

```bash
# 1. Copy env files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Start infrastructure
cd infra && docker compose up -d && cd ..

# 3. Backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" && uvicorn app.main:app --reload

# 4. Frontend (another terminal)
cd frontend && npm install && npm run dev
```

## Key docs

| Doc | Purpose |
|-----|--------|
| [ROADMAP_GuruPix_System_Design.md](ROADMAP_GuruPix_System_Design.md) | Single source of truth — staged roadmap and contracts |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview and repo layout |
| [docs/API.md](docs/API.md) | Endpoint contract table |
| [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Setup, run, test (beginner-friendly) |
| [docs/PRIVACY_AND_DATA.md](docs/PRIVACY_AND_DATA.md) | Data contract and user rights |
| [docs/CHANGELOG_DEV.md](docs/CHANGELOG_DEV.md) | Per-stage release notes |

## CI

Merge is gated on: lint (backend + frontend), unit tests, integration tests, E2E (Playwright), model smoke, security audit. See [.github/workflows/ci.yml](.github/workflows/ci.yml).

Do not skip stages; wait for confirmation before moving from Stage 0 to Stage 1.
