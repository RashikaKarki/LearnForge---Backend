"""Unit tests for Firebase session middleware."""


from fastapi import FastAPI
from starlette.testclient import TestClient

from app.middleware.firebase_session_middleware import FirebaseSessionMiddleware


def test_middleware_missing_cookie():
    """Should return 401 without cookie."""
    app = FastAPI()
    app.add_middleware(FirebaseSessionMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 401


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
