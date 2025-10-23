import firebase_admin.auth as firebase_auth_module
import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from app.middleware.firebase_middleware import FirebaseAuthMiddleware


class DummyException(Exception):
    pass


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/protected")
    async def protected(request: Request):
        # middleware should set request.state.user when token is valid
        return {"user": getattr(request.state, "user", None)}

    app.add_middleware(FirebaseAuthMiddleware)
    return app


def test_missing_authorization_header(app):
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing or invalid Authorization header"


def test_invalid_authorization_scheme(app):
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing or invalid Authorization header"


def test_invalid_token(app, monkeypatch):
    # mock verify_id_token to raise an exception
    def fake_verify(token):
        raise Exception("invalid")

    monkeypatch.setattr(firebase_auth_module, "verify_id_token", fake_verify)

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid or expired token: invalid"


def test_valid_token_sets_request_state_user(app, monkeypatch):
    # mock verify_id_token to return a decoded token dict
    def fake_verify(token):
        return {"uid": "user123", "email": "user@example.com"}

    monkeypatch.setattr(firebase_auth_module, "verify_id_token", fake_verify)

    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer goodtoken"})
    assert resp.status_code == 200
    assert resp.json()["user"] == {"uid": "user123", "email": "user@example.com"}
