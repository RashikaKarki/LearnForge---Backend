from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from app.middleware.firebase_middleware import FirebaseAuthMiddleware


@pytest.fixture
def app() -> FastAPI:
    app: FastAPI = FastAPI()
    # Mock the database
    app.state.db = MagicMock()

    @app.get("/protected")
    async def protected(request: Request):
        user = getattr(request.state, "current_user", None)
        if user:
            return {"user": {"firebase_uid": user.firebase_uid, "email": user.email}}
        return {"user": None}

    app.add_middleware(FirebaseAuthMiddleware)
    return app


def test_missing_authorization_header(app: FastAPI):
    client = TestClient(app)
    resp = client.get("/protected")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing Authorization header"


def test_invalid_authorization_scheme(app: FastAPI):
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Token abc"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid auth scheme"


def test_malformed_authorization_header(app: FastAPI):
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Malformed Authorization header"


@patch("firebase_admin.auth.verify_id_token")
def test_invalid_token(mock_verify, app: FastAPI):
    mock_verify.side_effect = Exception("invalid")

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer badtoken"})

    assert resp.status_code == 500
    assert "Internal server error" in resp.json()["detail"]


@patch("firebase_admin.auth.verify_id_token")
@patch("app.middleware.firebase_middleware.UserService")
def test_valid_token_sets_request_state_user(mock_user_service, mock_verify, app: FastAPI):
    mock_verify.return_value = {
        "uid": "user123",
        "email": "user@example.com",
        "name": "Test User",
        "picture": "http://example.com/pic.jpg",
    }

    mock_user_instance = MagicMock()
    mock_user = MagicMock()
    mock_user.firebase_uid = "user123"
    mock_user.email = "user@example.com"
    mock_user_instance.get_or_create_user.return_value = mock_user
    mock_user_service.return_value = mock_user_instance

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer goodtoken"})

    assert resp.status_code == 200
    assert resp.json()["user"]["firebase_uid"] == "user123"
    assert resp.json()["user"]["email"] == "user@example.com"


@patch("firebase_admin.auth.verify_id_token")
def test_expired_token(mock_verify, app: FastAPI):
    from firebase_admin.auth import ExpiredIdTokenError

    mock_verify.side_effect = ExpiredIdTokenError("Token expired", cause=None)

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer expiredtoken"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token expired"
    assert resp.json()["error_code"] == "TOKEN_EXPIRED"


@patch("firebase_admin.auth.verify_id_token")
def test_revoked_token(mock_verify, app: FastAPI):
    from firebase_admin.auth import RevokedIdTokenError

    mock_verify.side_effect = RevokedIdTokenError("Token revoked")

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer revokedtoken"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token revoked"
    assert resp.json()["error_code"] == "TOKEN_REVOKED"


@patch("firebase_admin.auth.verify_id_token")
def test_invalid_id_token(mock_verify, app: FastAPI):
    from firebase_admin.auth import InvalidIdTokenError

    mock_verify.side_effect = InvalidIdTokenError("Invalid token", cause=None)

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer invalidtoken"})

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid token"
    assert resp.json()["error_code"] == "TOKEN_INVALID"


def test_excluded_path_docs(app: FastAPI):
    client = TestClient(app)
    resp = client.get("/docs")

    assert resp.status_code == 200


def test_options_request_bypasses_auth(app: FastAPI):
    client = TestClient(app)
    resp = client.options("/protected")

    assert resp.status_code != 401
