"""Unit tests for Firebase session middleware."""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request
from firebase_admin.auth import (
    ExpiredIdTokenError,
    ExpiredSessionCookieError,
    InvalidIdTokenError,
    InvalidSessionCookieError,
    RevokedIdTokenError,
    RevokedSessionCookieError,
)
from starlette.testclient import TestClient

from app.middleware.firebase_session_middleware import FirebaseSessionMiddleware
from app.models.user import User


def test_middleware_missing_auth():
    """Should return 401 without cookie or Authorization header."""
    app = FastAPI()
    app.state.db = MagicMock()  # Mock database for middleware
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 401
    assert "Missing authentication token" in response.json()["detail"]
    assert response.json()["error_code"] == "AUTH_MISSING"


def test_middleware_excluded_path():
    """Should skip auth for excluded paths."""
    app = FastAPI()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/docs")
    def docs_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/docs")

    assert response.status_code == 200


def test_middleware_options_request():
    """Should skip auth for OPTIONS."""
    app = FastAPI()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.options("/test")
    def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.options("/test")

    assert response.status_code == 200


def test_middleware_with_session_cookie():
    """Should authenticate successfully with session cookie."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint(request: Request):
        return {"user_id": request.state.current_user.id}

    mock_user = User(
        id="user123",
        firebase_uid="firebase123",
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.jpg",
    )

    with (
        patch("app.middleware.firebase_session_middleware.auth") as mock_auth,
        patch("app.middleware.firebase_session_middleware.UserService") as mock_user_service,
    ):
        mock_auth.verify_session_cookie.return_value = {
            "uid": "firebase123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
        }
        mock_user_service.return_value.get_or_create_user.return_value = mock_user

        client = TestClient(app)
        response = client.get("/test", cookies={"session": "valid_session_cookie"})

        assert response.status_code == 200
        assert response.json()["user_id"] == "user123"
        mock_auth.verify_session_cookie.assert_called_once_with(
            "valid_session_cookie", check_revoked=True
        )


def test_middleware_with_authorization_header_session_cookie():
    """Should authenticate successfully with session cookie in Authorization header."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint(request: Request):
        return {"user_id": request.state.current_user.id}

    mock_user = User(
        id="user123",
        firebase_uid="firebase123",
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.jpg",
    )

    with (
        patch("app.middleware.firebase_session_middleware.auth") as mock_auth,
        patch("app.middleware.firebase_session_middleware.UserService") as mock_user_service,
    ):
        mock_auth.verify_session_cookie.return_value = {
            "uid": "firebase123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
        }
        mock_user_service.return_value.get_or_create_user.return_value = mock_user

        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Bearer valid_session_cookie"})

        assert response.status_code == 200
        assert response.json()["user_id"] == "user123"
        mock_auth.verify_session_cookie.assert_called_once_with(
            "valid_session_cookie", check_revoked=True
        )


def test_middleware_with_authorization_header_id_token():
    """Should authenticate successfully with ID token in Authorization header (fallback)."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint(request: Request):
        return {"user_id": request.state.current_user.id}

    mock_user = User(
        id="user123",
        firebase_uid="firebase123",
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.jpg",
    )

    with (
        patch("app.middleware.firebase_session_middleware.auth") as mock_auth,
        patch("app.middleware.firebase_session_middleware.UserService") as mock_user_service,
    ):
        # First call fails with issuer error (indicating it's an ID token)
        # The error message must contain "iss", "issuer", and "securetoken.google.com" or "session.firebase.google.com"
        issuer_error = InvalidSessionCookieError(
            "The session cookie has an invalid issuer. Expected securetoken.google.com",
            cause=Exception("issuer mismatch"),
        )
        mock_auth.verify_session_cookie.side_effect = issuer_error
        mock_auth.verify_id_token.return_value = {
            "uid": "firebase123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
        }
        mock_user_service.return_value.get_or_create_user.return_value = mock_user

        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Bearer id_token"})

        assert response.status_code == 200
        assert response.json()["user_id"] == "user123"
        mock_auth.verify_session_cookie.assert_called_once_with("id_token", check_revoked=True)
        mock_auth.verify_id_token.assert_called_once_with("id_token", check_revoked=True)


def test_middleware_prefers_cookie_over_header():
    """Should prefer session cookie over Authorization header."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint(request: Request):
        return {"user_id": request.state.current_user.id}

    mock_user = User(
        id="user123",
        firebase_uid="firebase123",
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.jpg",
    )

    with (
        patch("app.middleware.firebase_session_middleware.auth") as mock_auth,
        patch("app.middleware.firebase_session_middleware.UserService") as mock_user_service,
    ):
        mock_auth.verify_session_cookie.return_value = {
            "uid": "firebase123",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "http://example.com/pic.jpg",
        }
        mock_user_service.return_value.get_or_create_user.return_value = mock_user

        client = TestClient(app)
        response = client.get(
            "/test",
            cookies={"session": "cookie_token"},
            headers={"Authorization": "Bearer header_token"},
        )

        assert response.status_code == 200
        assert response.json()["user_id"] == "user123"
        # Should use cookie token, not header token
        mock_auth.verify_session_cookie.assert_called_once_with("cookie_token", check_revoked=True)


def test_middleware_expired_session_cookie():
    """Should return 401 for expired session cookie."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        mock_auth.verify_session_cookie.side_effect = ExpiredSessionCookieError(
            "Session expired", cause=Exception("expired")
        )

        client = TestClient(app)
        response = client.get("/test", cookies={"session": "expired_cookie"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "SESSION_EXPIRED"
        assert "Session expired" in response.json()["detail"]


def test_middleware_expired_id_token():
    """Should return 401 for expired ID token."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        # First call fails with issuer error, then ID token verification fails
        mock_auth.verify_session_cookie.side_effect = InvalidSessionCookieError(
            "The session cookie has an invalid issuer. Expected securetoken.google.com",
            cause=Exception("issuer mismatch"),
        )
        mock_auth.verify_id_token.side_effect = ExpiredIdTokenError(
            "Token expired", cause=Exception("expired")
        )

        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Bearer expired_token"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "TOKEN_EXPIRED"
        assert "ID token expired" in response.json()["detail"]


def test_middleware_revoked_session_cookie():
    """Should return 401 for revoked session cookie."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        mock_auth.verify_session_cookie.side_effect = RevokedSessionCookieError("Session revoked")

        client = TestClient(app)
        response = client.get("/test", cookies={"session": "revoked_cookie"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "SESSION_REVOKED"
        assert "Session revoked" in response.json()["detail"]


def test_middleware_revoked_id_token():
    """Should return 401 for revoked ID token."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        # First call fails with issuer error, then ID token verification fails
        mock_auth.verify_session_cookie.side_effect = InvalidSessionCookieError(
            "The session cookie has an invalid issuer. Expected securetoken.google.com",
            cause=Exception("issuer mismatch"),
        )
        mock_auth.verify_id_token.side_effect = RevokedIdTokenError("Token revoked")

        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Bearer revoked_token"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "TOKEN_REVOKED"
        assert "ID token revoked" in response.json()["detail"]


def test_middleware_invalid_session_cookie():
    """Should return 401 for invalid session cookie."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        mock_auth.verify_session_cookie.side_effect = InvalidSessionCookieError(
            "Invalid session", cause=Exception("invalid")
        )

        client = TestClient(app)
        response = client.get("/test", cookies={"session": "invalid_cookie"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "SESSION_INVALID"
        assert "Invalid session" in response.json()["detail"]


def test_middleware_invalid_id_token():
    """Should return 401 for invalid ID token."""
    app = FastAPI()
    app.state.db = MagicMock()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    with patch("app.middleware.firebase_session_middleware.auth") as mock_auth:
        # First call fails with issuer error, then ID token verification fails
        mock_auth.verify_session_cookie.side_effect = InvalidSessionCookieError(
            "The session cookie has an invalid issuer. Expected securetoken.google.com",
            cause=Exception("issuer mismatch"),
        )
        mock_auth.verify_id_token.side_effect = InvalidIdTokenError(
            "Invalid token", cause=Exception("invalid")
        )

        client = TestClient(app)
        response = client.get("/test", headers={"Authorization": "Bearer invalid_token"})

        assert response.status_code == 401
        assert response.json()["error_code"] == "TOKEN_INVALID"
        assert "Invalid ID token" in response.json()["detail"]
