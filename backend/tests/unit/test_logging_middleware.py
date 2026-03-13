"""
Unit test for LoggingMiddleware.

Verifies that each request triggers a structured log with the required fields.
Uses a mock on the logger to avoid flakiness from test order / logger state.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from app.main import create_app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_logging_middleware_emits_structured_log() -> None:
    """LoggingMiddleware must log each request with event, method, path, status_code, duration_ms, request_id."""
    log_calls: list[tuple[str, str]] = []

    def capture_info(msg: str, *args: object, **kwargs: object) -> None:
        log_calls.append(("info", msg))

    with patch("app.middleware.logging.logger") as mock_logger:
        mock_logger.info.side_effect = capture_info

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/health")

    assert response.status_code == 200, "Health endpoint must return 200"
    assert len(log_calls) >= 1, f"Expected at least one log call; got {len(log_calls)}"

    payload = json.loads(log_calls[-1][1])

    assert payload["event"] == "http_request", "Log must have event=http_request"
    assert payload["method"] == "GET", "Log must record GET method"
    assert payload["path"] == "/api/v1/health", "Log must record request path"
    assert payload["status_code"] == 200, "Log must record status code"
    assert isinstance(payload["duration_ms"], (int, float)), "Log must have numeric duration_ms"
    assert payload["duration_ms"] >= 0, "duration_ms must be non-negative"
    assert payload["request_id"] is not None, "Log must include request_id"
