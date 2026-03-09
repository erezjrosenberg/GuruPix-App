"""
Unit test for LoggingMiddleware.

Verifies that each request emits a structured JSON log line containing
the required fields: event, method, path, status_code, duration_ms, request_id.
"""

from __future__ import annotations

import json
import logging

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_logging_middleware_emits_structured_log(caplog: logging.LogRecord) -> None:
    with caplog.at_level(logging.INFO, logger="gurupix.request"):
        client.get("/api/v1/health")

    log_lines = [r for r in caplog.records if r.name == "gurupix.request"]
    assert len(log_lines) >= 1, "Expected at least one log from gurupix.request"

    payload = json.loads(log_lines[-1].getMessage())

    assert payload["event"] == "http_request"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/health"
    assert payload["status_code"] == 200
    assert isinstance(payload["duration_ms"], (int, float))
    assert payload["duration_ms"] >= 0
    assert payload["request_id"] is not None
