#!/usr/bin/env bash
# One command to check prerequisites, fix what's missing, and run the app.
# Usage: ./scripts/bootstrap-and-run.sh   or   npm run dev:full
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== GuruPix bootstrap & run ==="

# 1. Docker
if ! command -v docker &>/dev/null; then
  echo "Error: Docker not found. Install Docker Desktop first."
  exit 1
fi
if ! docker info &>/dev/null; then
  echo "Error: Docker is not running. Start Docker Desktop."
  exit 1
fi

# 2. Start infra (Postgres, Redis) and wait for healthy
echo "Checking infrastructure..."
cd infra
if ! docker compose ps 2>/dev/null | grep -q "Up"; then
  echo "Starting Postgres, Redis..."
  docker compose up -d --wait
else
  # Ensure containers are healthy before proceeding
  echo "Waiting for containers to be healthy..."
  for i in {1..30}; do
    if docker compose ps 2>/dev/null | grep -q "healthy"; then
      break
    fi
    sleep 1
  done
fi
cd "$ROOT"

# 3. Backend .env
if [[ ! -f backend/.env ]]; then
  echo "Creating backend/.env from .env.example..."
  cp backend/.env.example backend/.env
fi

# 4. Frontend .env.local
if [[ ! -f frontend/.env.local ]]; then
  echo "Creating frontend/.env.local from .env.example..."
  cp frontend/.env.example frontend/.env.local
fi

# 5. Backend venv + deps
if [[ ! -d backend/.venv ]]; then
  echo "Creating backend virtualenv..."
  cd backend && python3 -m venv .venv && pip install -e ".[dev]" && cd "$ROOT"
fi
if ! backend/.venv/bin/python -c "import fastapi" 2>/dev/null; then
  echo "Installing backend dependencies..."
  cd backend && pip install -e ".[dev]" && cd "$ROOT"
fi

# 6. Frontend deps
if [[ ! -d frontend/node_modules ]]; then
  echo "Installing frontend dependencies..."
  cd frontend && npm install && cd "$ROOT"
fi

# 7. DB migrations (admin created by migration 003; data persists in Postgres volume)
echo "Running database migrations..."
(cd backend && .venv/bin/python -m alembic upgrade head) || true

echo ""
echo "All set. Starting backend + frontend..."
exec bash "$ROOT/scripts/dev.sh"
