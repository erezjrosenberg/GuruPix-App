# GuruPix Backend

FastAPI application for GuruPix. See repo root `docs/DEVELOPER_GUIDE.md` for setup and run instructions.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

## Tests

- Unit: `pytest tests/unit`
- Integration: `pytest tests/integration` (requires docker-compose up in `infra/`)
