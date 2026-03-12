# GuruPix — common commands from repo root
# Usage: make <target>

export PATH := /Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:$(PATH)

.PHONY: docker_up test test-backend-unit test-backend-integration test-frontend test-e2e

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

# Ensure infra containers are running (starts them if not)
docker_up:
	@if command -v docker >/dev/null 2>&1; then \
		cd infra && docker compose up -d; \
	else \
		echo "⚠  docker not found — skipping container startup (integration/DB tests will be skipped)"; \
	fi

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# Backend unit tests (no external deps)
test-backend-unit:
	cd backend && .venv/bin/python -m pytest tests/unit -v

# Backend integration tests (needs Postgres + Redis — starts containers first)
test-backend-integration: docker_up
	cd backend && .venv/bin/python -m pytest tests/integration -v

# Frontend unit tests
test-frontend:
	cd frontend && npm run test

# E2E tests (Playwright auto-starts frontend via webServer at localhost:5173)
test-e2e:
	cd tests/e2e && npx playwright test --reporter=list

# Run ALL tests (starts containers, then backend + frontend + e2e)
test: docker_up
	cd backend && .venv/bin/python -m pytest tests/unit tests/integration -v
	cd frontend && npm run test
	cd tests/e2e && npx playwright test --reporter=list
