# GuruPix — Runbooks

Operational runbooks for deployment, incidents, and maintenance. To be expanded in later stages.

## Local Infrastructure

- Start: `cd infra && docker compose up -d`
- Stop: `cd infra && docker compose down`
- Logs: `docker compose -f infra/docker-compose.yml logs -f [service]`

## Backend

- Run: `cd backend && uvicorn app.main:app --reload`
- Health: `curl http://localhost:8000/api/v1/health` (after Stage 1)

## Frontend

- Run: `cd frontend && npm run dev`
- Build: `cd frontend && npm run build`

## Database (Postgres)

- Migrations: `cd backend && alembic upgrade head` (after Stage 2)
- Rollback: `cd backend && alembic downgrade -1`

(Additional runbooks for production will be added in Stage 13.)
