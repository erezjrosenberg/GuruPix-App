from __future__ import annotations

import uuid
from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_endpoint_returns_expected_version() -> None:
    with patch("app.api.system.get_app_version", return_value="9.8.7-mock"):
        response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {"version": "9.8.7-mock"}


def test_root_endpoint_returns_message() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "GuruPix" in body["message"]


def test_not_found_returns_standard_error_shape() -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert isinstance(body["detail"], str)
    assert isinstance(body["request_id"], str)
    assert body["request_id"] != ""
    # Header and body request_id must match
    assert response.headers.get("X-Request-Id") == body["request_id"]


def test_client_provided_request_id_is_echoed_back() -> None:
    custom_id = f"unit-test-{uuid.uuid4()}"
    response = client.get("/api/v1/health", headers={"X-Request-Id": custom_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-Id") == custom_id


def test_response_time_header_is_parseable_float() -> None:
    response = client.get("/api/v1/health")

    raw = response.headers.get("X-Response-Time-ms")
    assert raw is not None
    duration = float(raw)
    assert duration >= 0
