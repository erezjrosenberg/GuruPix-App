"""
Unit tests for SessionMiddleware.

Redis is mocked so no external service is required.  Tests verify:
- A session_id is generated when the client does not provide one.
- A client-provided X-Session-Id is echoed back unchanged.
- The session_id appears on request.state for downstream code.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from app.middleware.session import SessionMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SessionMiddleware)

    @app.get("/check-session")
    def check_session(request: Request) -> dict[str, str]:
        return {"session_id": getattr(request.state, "session_id", "")}

    return app


@patch("app.middleware.session.Settings")
@patch("app.middleware.session.get_redis_client")
def test_session_id_generated_when_missing(mock_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.session_ttl_seconds = 3600
    mock_redis.return_value = None

    client = TestClient(_make_app())
    resp = client.get("/check-session")

    assert resp.status_code == 200
    header_id = resp.headers.get("X-Session-Id")
    assert header_id is not None
    uuid.UUID(header_id)

    body_id = resp.json()["session_id"]
    assert body_id == header_id


@patch("app.middleware.session.Settings")
@patch("app.middleware.session.get_redis_client")
def test_client_session_id_echoed_back(mock_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.session_ttl_seconds = 3600
    mock_redis.return_value = None

    client = TestClient(_make_app())
    custom = f"my-session-{uuid.uuid4()}"
    resp = client.get("/check-session", headers={"X-Session-Id": custom})

    assert resp.status_code == 200
    assert resp.headers.get("X-Session-Id") == custom
    assert resp.json()["session_id"] == custom


@patch("app.middleware.session.Settings")
@patch("app.middleware.session.get_redis_client")
def test_session_touches_redis_when_available(mock_redis, mock_settings_cls) -> None:
    mock_settings_cls.return_value.session_ttl_seconds = 7200
    redis_mock = AsyncMock()
    mock_redis.return_value = redis_mock

    client = TestClient(_make_app())
    resp = client.get("/check-session")

    assert resp.status_code == 200
    redis_mock.set.assert_called_once()
    call_args = redis_mock.set.call_args
    assert call_args.kwargs.get("ex") == 7200
