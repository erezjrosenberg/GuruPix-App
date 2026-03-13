#!/usr/bin/env bash
# Run backend + frontend together. Ctrl+C stops both.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKEND_PID=""
cleanup() {
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM

# Kill any existing backend on port 8000 (from a previous run)
PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [[ -n "$PIDS" ]]; then
  echo "Stopping existing backend (pids: $PIDS)..."
  echo "$PIDS" | xargs kill -9 2>/dev/null || true
  sleep 2
fi

echo "Running migrations..."
(cd backend && .venv/bin/python -m alembic upgrade head 2>/dev/null) || true

echo "Starting backend..."
(cd backend && .venv/bin/uvicorn app.main:app --reload --reload-dir app) &
BACKEND_PID=$!

echo "Waiting for backend to be ready..."
for i in {1..30}; do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null | grep -q 200; then
    echo "Backend ready."
    break
  fi
  sleep 0.5
done

echo "Starting frontend..."
cd frontend && npm run dev
