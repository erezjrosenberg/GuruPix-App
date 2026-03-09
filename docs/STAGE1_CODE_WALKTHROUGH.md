# Stage 1 Code Walkthrough — Beginner-Friendly

This document walks through every file we added or changed for Stage 1, line by line, with beginner-level explanations. Use it alongside the code in your editor.

---

## Table of contents

1. [Version helper](#1-version-helper-appcoreversionpy)
2. [Response schemas](#2-response-schemas-appschemassystempy)
3. [System API router](#3-system-api-router-appapisystempy)
4. [Main app and middleware wiring](#4-main-app-and-middleware-wiring-appmainpy)
5. [RequestId middleware](#5-requestid-middleware-appmiddlewarerequest_idpy)
6. [Timing middleware](#6-timing-middleware-appmiddlewaretimingpy)
7. [Logging middleware](#7-logging-middleware-appmiddlewareloggingpy)
8. [Error middleware](#8-error-middleware-appmiddlewareerrorpy)
9. [Unit tests](#9-unit-tests-testsunittest_system_endpointspy)
10. [Integration test](#10-integration-test-testsintegrationtest_health_endpointpy)

---

## 1. Version helper — `app/core/version.py`

**What this file does:** It answers one question: “What version is this backend?” in a single place, so we don’t hard-code the version everywhere.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 1 | `from __future__ import annotations` | Lets you use `str` instead of `"str"` in type hints (Python 3.7+ style). Makes forward references and cleaner types possible. |
| 3 | `import os` | We use `os.getenv()` to read environment variables. |
| 4 | `from importlib.metadata import ...` | `importlib.metadata` is the standard way to read **installed package** info (e.g. version from `pyproject.toml`). We import the function as `pkg_version` and the exception `PackageNotFoundError`. |
| 7 | `def get_app_version() -> str:` | Function that returns a string. The `-> str` is a **type hint**: it tells humans and tools (e.g. mypy) “this function returns a string.” |
| 16 | `os.getenv("GURUPIX_BACKEND_VERSION")` | Reads the environment variable. Returns `None` if it’s not set. **Why:** In Docker or CI we can set this to a git SHA or build number without touching code. |
| 17–18 | `if env_version: return env_version` | If the user set the env var, we use it and stop. **Priority 1.** |
| 20–21 | `return pkg_version("gurupix-backend")` | Asks Python: “What version of the package named `gurupix-backend` is installed?” That comes from `pyproject.toml` when you run `pip install -e .`. **Priority 2.** |
| 22–24 | `except PackageNotFoundError: return "0.1.0"` | If the package isn’t installed (e.g. you’re running from the repo without `pip install -e .`), we don’t crash—we return a sensible default. **Priority 3.** |

**Beginner takeaway:** One function, three ways to get the version (env → package → default). The rest of the app just calls `get_app_version()` and doesn’t care which one was used.

---

## 2. Response schemas — `app/schemas/system.py`

**What this file does:** It defines the **exact shape** of the JSON our API returns for health, version, and errors. Pydantic checks that we never send a wrong shape.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 1 | `from __future__ import annotations` | Same as above—enables modern type hint syntax. |
| 3 | `from pydantic import BaseModel` | **Pydantic** is a library that validates data. `BaseModel` is the base class for “a bag of fields with types.” |
| 6–7 | `class HealthResponse(BaseModel): status: str` | A model with one field, `status`, that must be a string. When we do `HealthResponse(status="ok")`, Pydantic checks it. When FastAPI sends the response, it turns this into `{"status": "ok"}`. |
| 9–10 | `class VersionResponse(BaseModel): version: str` | Same idea: one field `version`. So the API always returns `{"version": "0.1.0"}` (or whatever string). |
| 13–16 | `class ErrorResponse(BaseModel): detail: str; request_id: str` | Our **standard error shape**. Every error response will have exactly these two string fields. Clients and logs can rely on that. |

**Beginner takeaway:** These classes are **contracts**. If someone adds a typo (e.g. `statos` instead of `status`), Pydantic will complain. That catches bugs early.

---

## 3. System API router — `app/api/system.py`

**What this file does:** Defines the two “system” HTTP endpoints (`/api/v1/health` and `/api/v1/version`) and wires them to our schemas.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 3 | `from fastapi import APIRouter` | An **APIRouter** is a group of routes. We can give it a prefix (e.g. `/api/v1`) and later “mount” it on the main app with one line. |
| 5–6 | `from app.core.version import ...` and `from app.schemas.system import ...` | We use our version helper and response models in this file. |
| 9 | `router = APIRouter(prefix="/api/v1", tags=["system"])` | Create a router. Every route we add to `router` will automatically live under `/api/v1`. The `tags=["system"]` groups these endpoints in the Swagger/OpenAPI docs. |
| 11–15 | `@router.get("/health", response_model=HealthResponse)` and `get_health()` | **Decorator** `@router.get("/health")` means: “When someone does GET /api/v1/health, call the function below.” `response_model=HealthResponse` tells FastAPI: “Serialize the return value as HealthResponse JSON.” We return `HealthResponse(status="ok")` so the body is always `{"status": "ok"}`. |
| 12 | `async def get_health() -> HealthResponse:` | We use `async` because FastAPI supports async; for this simple function it doesn’t matter much, but it’s consistent with the rest of the app. |
| 17–21 | `@router.get("/version", ...)` and `get_version()` | Same pattern. We call `get_app_version()` to get the string and wrap it in `VersionResponse(version=...)`. |

**Beginner takeaway:** The router only knows about `/health` and `/version`. The **prefix** is added when we do `app.include_router(system_router)` in `main.py`, so the full paths are `/api/v1/health` and `/api/v1/version`.

---

## 4. Main app and middleware wiring — `app/main.py`

**What this file does:** Creates the FastAPI app, adds all middleware in the right order, registers global exception handlers, and mounts the system router. This is the “brain” that wires everything together.

### The helper: `_build_error_response`

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 19 | `def _build_error_response(status_code: int, detail: str, request: Request) -> JSONResponse:` | A **private** helper (the leading `_` means “internal use”). We use it from the exception handlers to avoid repeating the same logic. |
| 20 | `request_id = getattr(request.state, "request_id", None)` | Safely get `request_id` from `request.state`. If it wasn’t set (e.g. 404 before middleware runs), we get `None`. |
| 21–24 | `if request_id is None: request_id = str(uuid.uuid4()); request.state.request_id = request_id` | If we don’t have an ID, generate one and attach it to the request so it’s available for the response. |
| 26 | `body = ErrorResponse(detail=detail, request_id=request_id)` | Build the standard error body using our Pydantic model. |
| 27 | `content=body.model_dump()` | Pydantic’s `model_dump()` turns the model into a plain dict FastAPI can serialize to JSON. |
| 28 | `response.headers["X-Request-Id"] = request_id` | So the client always sees the request ID in the header too. |

### The app factory: `create_app()`

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 34 | `logging.basicConfig(level=logging.INFO)` | So that our middleware’s `logger.info(...)` actually prints. Without this, you might not see log lines. |
| 36–40 | `app = FastAPI(title=..., description=..., version=get_app_version())` | Create the FastAPI app. `version` here is what shows up in the OpenAPI docs; we use our helper so it’s always in sync. |
| 42–50 | `app.add_middleware(...)` four times | **Order matters.** In Starlette/FastAPI, middleware is a stack: the **last** one you add runs **first** (outermost). So the actual order for a request is: RequestId → Timing → Logging → Error → your route. We add them in reverse so that RequestId runs first and sets `request.state.request_id` for the others. |
| 52–69 | `@app.exception_handler(StarletteHTTPException)` and `@app.exception_handler(RequestValidationError)` | **Exception handlers** catch specific exceptions. When FastAPI/Starlette raises a 404 (or any HTTPException), the first handler runs. When request body validation fails (e.g. wrong JSON), the second runs. Both call `_build_error_response` so the JSON always has `detail` and `request_id`. |
| 72 | `app.include_router(system_router)` | “Mount” the system router. All routes defined in `system_router` (e.g. GET /health, GET /version) now belong to the app under the prefix `/api/v1`. |
| 74–77 | `@app.get("/")` and `root()` | The root URL returns a short message and points users to `/docs`. |
| 79 | `return app` | The factory returns the configured app. |
| 83 | `app = create_app()` | This is what uvicorn and tests use: `uvicorn app.main:app` means “use the object named `app` in `app.main`.” |

**Beginner takeaway:** Middleware runs on every request. Exception handlers run only when something raises. By registering both, we make sure 200s, 404s, and 500s all get a consistent shape and headers.

---

## 5. RequestId middleware — `app/middleware/request_id.py`

**What this file does:** Gives every request a unique ID (or uses the one the client sent), stores it on the request, and sends it back in the response header. That way you can trace one request across logs and clients.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 6 | `from starlette.middleware.base import BaseHTTPMiddleware` | FastAPI is built on **Starlette**. This base class is the standard way to write middleware: you implement `dispatch()`, and it takes care of calling the next step in the chain. |
| 11 | `class RequestIdMiddleware(BaseHTTPMiddleware):` | Our class extends that base. The “app” we get in `__init__` is the next thing in the chain (another middleware or the route handler). |
| 19–21 | `def __init__(self, app: Callable, header_name: str = "X-Request-Id")` | `app` is the next handler in the stack. We can optionally use a different header name; by default we use `X-Request-Id`. |
| 23 | `async def dispatch(self, request: Request, call_next: ...) -> Response:` | **Every** middleware implements `dispatch`. You receive the `request`, and you call `call_next(request)` to pass it to the next layer. You get back a `response` and can modify it before returning. |
| 24 | `request_id = request.headers.get(self.header_name) or str(uuid.uuid4())` | If the client sent `X-Request-Id`, use it. Otherwise create a new UUID4 (random but unique). The `or` is because `.get()` returns `None` when the header is missing. |
| 25 | `request.state.request_id = request_id` | Attach the ID to the request. **request.state** is a namespace that lives for the lifetime of this request; other code (e.g. logging, error handler) can read it. |
| 27 | `response = await call_next(request)` | Pass the request down the stack. This is where the rest of the app (other middleware + your route) runs. We **await** it because it’s async. |
| 28–29 | `response.headers[...] = request_id; return response` | Add the request ID to the response headers and return. The client (or a load balancer) can then correlate this response with the same ID. |

**Beginner takeaway:** Middleware = “before and after” the rest of the app. We do something before (`request_id`, put on state), call the rest of the app, then do something after (put ID on response).

---

## 6. Timing middleware — `app/middleware/timing.py`

**What this file does:** Measures how long the request took (from entering this middleware until the response comes back) and puts that duration in the `X-Response-Time-ms` header.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 3 | `import time` | We use `time.perf_counter()` for high-resolution timing (better than `time.time()` for measuring short durations). |
| 19 | `start = time.perf_counter()` | Record the time **before** we call the rest of the app. |
| 20 | `response = await call_next(request)` | Let the request go through all inner middleware and the route. |
| 21 | `duration_ms = (time.perf_counter() - start) * 1000` | Time **after** minus time **before** gives elapsed seconds; multiply by 1000 to get milliseconds. |
| 22 | `response.headers[self.header_name] = f"{duration_ms:.2f}"` | Put the number in the header as a string with two decimal places (e.g. `"12.34"`). We use a string because headers are text. |
| 23 | `return response` | Send the response back up the stack (with the new header). |

**Beginner takeaway:** Same “before / call_next / after” pattern. We only add one header; we don’t change the body or status code.

---

## 7. Logging middleware — `app/middleware/logging.py`

**What this file does:** Writes one structured log line per request (method, path, status code, duration, request_id) so we can search and analyze logs later.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 3 | `import json` | We log a **JSON** string so log aggregators (e.g. CloudWatch, Datadog) can parse it and index fields. |
| 4 | `import logging` | Python’s standard logging. We don’t use `print()` so we can control levels (INFO, WARNING) and outputs (console, file). |
| 12 | `logger = logging.getLogger("gurupix.request")` | Get a logger with a **name**. You can later configure “log everything from `gurupix.request` at INFO level” in one place. |
| 24–26 | `start = time.perf_counter(); response = await call_next(request); duration_ms = ...` | Same pattern as timing: we measure how long the inner stack took. We could reuse TimingMiddleware’s value, but measuring here keeps this middleware self-contained. |
| 28 | `request_id = getattr(request.state, "request_id", None)` | RequestId runs before us, so usually `request_id` is set. We use `getattr(..., None)` so we don’t crash if something is misconfigured. |
| 30–37 | `payload = { "event": "http_request", "method": ..., "path": ..., ... }` | Build a dict with everything we want in one log line. `round(duration_ms, 2)` keeps the number readable. |
| 39 | `logger.info(json.dumps(payload, sort_keys=True))` | Turn the dict into a JSON string and log it at INFO level. `sort_keys=True` keeps the order consistent for easier diffing. |
| 40 | `return response` | We don’t change the response; we only observe and log. |

**Beginner takeaway:** Structured logging (one JSON object per request) is easier to query than ad-hoc print statements. The `request_id` in the log is the same as in the response header, so you can find all log lines for one request.

---

## 8. Error middleware — `app/middleware/error.py`

**What this file does:** Catches exceptions that happen **inside** the request (e.g. in a route or in inner middleware), logs them, and returns a JSON response with our standard `{ "detail", "request_id" }` shape instead of a plain 500 HTML page.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 7–9 | `from fastapi.exceptions import RequestValidationError` and `from starlette.exceptions import HTTPException as StarletteHTTPException` | Two important exception types: validation errors (e.g. invalid body) and HTTP errors (e.g. 404, 403) raised by code. |
| 16 | `logger = logging.getLogger("gurupix.error")` | Separate logger for errors so we can set different levels or outputs for “request log” vs “error log.” |
| 26–29 | `request_id = getattr(...); if request_id is None: request_id = str(uuid.uuid4()); request.state.request_id = request_id` | Same idea as in `_build_error_response`: ensure we have a request ID so every error response can include it. |
| 31–32 | `try: return await call_next(request)` | We run the rest of the app inside a try. If anything raises, we catch it below. |
| 33–42 | `except RequestValidationError as exc:` | When the request body/query doesn’t match the expected schema, FastAPI raises this. We log a warning (with the validation details in `extra`), then return a 422 response with our standard shape. |
| 43–55 | `except StarletteHTTPException as exc:` | When code raises HTTPException (e.g. 404, 403), we log it and return a JSON response with the same status code and our body shape. |
| 56–65 | `except Exception as exc:` | Any **other** exception (e.g. bug in our code, database down). We log the full traceback with `logger.exception(...)` and return 500 with a generic message so we don’t leak internals to the client. |
| 68–71 | `_error_response(status_code, detail, request_id)` | Builds `ErrorResponse(detail=..., request_id=...)` and returns a `JSONResponse` with that body and the given status code. |

**Beginner takeaway:** This middleware is the “safety net” for the inner app. Without it, an unhandled exception would result in a default HTML error page. With it, the client always gets JSON and a request_id they can send to support.

---

## 9. Unit tests — `tests/unit/test_system_endpoints.py`

**What this file does:** Checks that the health and version endpoints return the right status, body, and headers, and that a 404 returns our error shape. No real HTTP server: we call the app in-process with FastAPI’s `TestClient`.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 3 | `from fastapi.testclient import TestClient` | **TestClient** wraps the ASGI app and lets you do `client.get("/api/v1/health")` as if you were sending HTTP. It runs the full stack (middleware + routes) in the same process. |
| 6 | `from app.main import app` | We need the same `app` object that production uses (created by `create_app()`). |
| 9 | `client = TestClient(app)` | One client instance for all tests. It’s cheap to reuse. |
| 13–14 | `response = client.get("/api/v1/health"); assert response.status_code == 200` | Send GET and check we get 200 OK. |
| 15 | `assert response.json() == {"status": "ok"}` | The body must be exactly this. That’s our schema contract. |
| 18–21 | `assert response.headers.get("X-Request-Id")` and non-empty | Middleware must have added the header. We don’t care about the exact value, only that it’s present. |
| 23–25 | Same for `X-Response-Time-ms` | Timing middleware must have added this. |
| 28–35 | `test_version_endpoint_returns_expected_version` | We check that the `version` field exists, is a string, and equals `get_app_version()`. So the endpoint and the helper stay in sync. |
| 38–46 | `test_not_found_uses_error_middleware_shape` | Request a path that doesn’t exist. We expect 404 and a body with both `detail` and `request_id` as non-empty strings. That’s the contract from the exception handler. |

**Beginner takeaway:** Unit tests run fast and don’t need Docker or a real server. They prove that our routes and middleware behave as designed. If someone removes the request_id from the error handler, this test will fail.

---

## 10. Integration test — `tests/integration/test_health_endpoint.py`

**What this file does:** Calls the app through the **async** path (using httpx and ASGI transport) and checks that a client-supplied `X-Request-Id` is echoed back. That verifies the full async stack and header handling.

| Line(s) | Code | Explanation |
|--------|------|-------------|
| 4 | `from httpx import ASGITransport, AsyncClient` | **httpx** is like `requests` but supports async and can talk to an ASGI app directly (no network). **ASGITransport** is the bridge: “send the request to this app as if it were HTTP.” |
| 9 | `@pytest.mark.asyncio` | Tells pytest that this test is **async** and must be run in an event loop. pytest-asyncio provides that. |
| 10 | `async def test_health_endpoint_reachable_with_custom_request_id()` | An async test so we can use `async with AsyncClient(...)`. |
| 12 | `transport = ASGITransport(app=app)` | “When I make a request, send it to this FastAPI app.” No port, no real HTTP. |
| 13 | `async with AsyncClient(transport=transport, base_url="http://test") as client:` | Create an HTTP client that uses our app. `base_url="http://test"` is required for relative paths like `/api/v1/health` to resolve correctly. |
| 14–17 | `response = await client.get("/api/v1/health", headers={"X-Request-Id": "integration-test-id"})` | Send GET with a **custom** request ID. We want to confirm the server echoes it back. |
| 19–21 | Assert status 200, body `{"status": "ok"}`, and `X-Request-Id == "integration-test-id"` | So the full pipeline (middleware + route) is working and the header we sent is the one we get back. |

**Beginner takeaway:** Integration tests use a more “real” path (async, full middleware). Here we specifically check that the app respects the client’s request ID. In CI, we don’t start uvicorn; we call the app in-process via ASGITransport, so it’s still fast and reliable.

---

## Quick reference: request flow

For a request like `GET /api/v1/health`:

1. **RequestIdMiddleware** runs first: sets or generates `X-Request-Id`, stores it in `request.state`.
2. **TimingMiddleware**: records start time, then calls next.
3. **LoggingMiddleware**: records start time, then calls next.
4. **ErrorMiddleware**: wraps the next call in try/except; if nothing raises, response goes back.
5. **Route handler** `get_health()` runs; returns `HealthResponse(status="ok")`.
6. Response goes back up: Error → Logging (log the request, add duration) → Timing (add `X-Response-Time-ms`) → RequestId (add `X-Request-Id` header) → client.

If something raises (e.g. 404 or 500), either the **exception handlers** in `main.py` (for 404/validation) or **ErrorMiddleware** (for errors inside the stack) will catch it and return a JSON body with `detail` and `request_id`.

---

*End of Stage 1 code walkthrough.*
