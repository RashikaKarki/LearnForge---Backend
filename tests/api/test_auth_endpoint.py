"""Unit tests for auth endpoints."""

import time
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.api.v1.routes.auth import router


def test_create_session_success():
    """Should create session with valid token."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    with patch("app.api.v1.routes.auth.auth") as mock_auth:
        mock_auth.verify_id_token.return_value = {
            "uid": "user123",
            "auth_time": int(time.time()),
        }
        mock_auth.create_session_cookie.return_value = "session_cookie"

        client = TestClient(app)
        response = client.post("/auth/create-session", json={"id_token": "token"})

        assert response.status_code == 201


def test_logout_success():
    """Should logout successfully."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    with patch("app.api.v1.routes.auth.auth") as mock_auth:
        mock_auth.verify_session_cookie.return_value = {"uid": "user123"}

        client = TestClient(app)
        client.cookies.set("session", "valid_session")
        response = client.post("/auth/logout")

        assert response.status_code == 200


def test_logout_without_cookie():
    """Should return 200 without cookie."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    client = TestClient(app)
    response = client.post("/auth/logout")

    assert response.status_code == 200


def test_refresh_session_success():
    """Should refresh valid session."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    with patch("app.api.v1.routes.auth.auth") as mock_auth:
        mock_auth.verify_session_cookie.return_value = {"uid": "user123"}
        mock_auth.create_session_cookie.return_value = "new_session"

        client = TestClient(app)
        client.cookies.set("session", "valid")
        response = client.post("/auth/refresh-session")

        assert response.status_code == 200


def test_refresh_session_no_cookie():
    """Should return 401 without cookie."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    client = TestClient(app)
    response = client.post("/auth/refresh-session")

    assert response.status_code == 401


def test_get_session_status_valid():
    """Should return status for valid session."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    with patch("app.api.v1.routes.auth.auth") as mock_auth:
        mock_auth.verify_session_cookie.return_value = {
            "uid": "user123",
            "email": "test@test.com",
        }

        client = TestClient(app)
        client.cookies.set("session", "valid")
        response = client.get("/auth/session-status")

        assert response.status_code == 200


def test_get_session_status_no_cookie():
    """Should return 401 without cookie."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    client = TestClient(app)
    response = client.get("/auth/session-status")

    assert response.status_code == 401
