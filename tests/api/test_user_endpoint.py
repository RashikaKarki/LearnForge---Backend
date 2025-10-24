"""Unit tests for user endpoints."""

from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from app.api.v1.routes.user import router
from app.models.user import User


def test_get_profile_success_returns_200():
    """Should return 200 with user profile data."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com"
        )
        return await call_next(request)

    app.include_router(router, prefix="/user")
    client = TestClient(app)
    
    response = client.get("/user/profile")
    
    assert response.status_code == 200


def test_get_profile_returns_user_id():
    """Should return user ID in response."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com"
        )
        return await call_next(request)

    app.include_router(router, prefix="/user")
    client = TestClient(app)
    
    response = client.get("/user/profile")
    
    assert response.json()["id"] == "user123"


def test_get_profile_returns_user_email():
    """Should return user email in response."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com"
        )
        return await call_next(request)

    app.include_router(router, prefix="/user")
    client = TestClient(app)
    
    response = client.get("/user/profile")
    
    assert response.json()["email"] == "test@example.com"


def test_get_profile_returns_user_name():
    """Should return user name in response."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com"
        )
        return await call_next(request)

    app.include_router(router, prefix="/user")
    client = TestClient(app)
    
    response = client.get("/user/profile")
    
    assert response.json()["name"] == "Test User"


def test_get_profile_includes_picture_field():
    """Should include picture field in response."""
    app = FastAPI()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com"
        )
        return await call_next(request)

    app.include_router(router, prefix="/user")
    client = TestClient(app)
    
    response = client.get("/user/profile")
    
    assert "picture" in response.json()
