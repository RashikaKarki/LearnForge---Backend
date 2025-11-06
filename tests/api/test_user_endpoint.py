"""Unit tests for user endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request
import pytest
from starlette.testclient import TestClient

from app.api.v1.routes.user import router
from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.user import User, UserEnrolledMission


@pytest.fixture
def test_app():
    app = FastAPI()
    app.state.db = MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    return app


@pytest.fixture
def test_user():
    return User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
    )


def test_get_profile_success_returns_200(test_app, test_user):
    """Should return 200 with user profile data."""

    @test_app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = test_user
        return await call_next(request)

    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_user.return_value = test_user
        client = TestClient(test_app)
        response = client.get("/user/profile")
        assert response.status_code == 200


def test_get_profile_returns_user_id(test_app, test_user):
    """Should return user ID in response."""

    @test_app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = test_user
        return await call_next(request)

    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_user.return_value = test_user
        client = TestClient(test_app)
        response = client.get("/user/profile")
        assert response.json()["id"] == "user123"


def test_get_profile_returns_user_email(test_app, test_user):
    """Should return user email in response."""

    @test_app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = test_user
        return await call_next(request)

    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_user.return_value = test_user
        client = TestClient(test_app)
        response = client.get("/user/profile")
        assert response.json()["email"] == "test@example.com"


def test_get_profile_returns_user_name(test_app, test_user):
    """Should return user name in response."""

    @test_app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = test_user
        return await call_next(request)

    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_user.return_value = test_user
        client = TestClient(test_app)
        response = client.get("/user/profile")
        assert response.json()["name"] == "Test User"


def test_get_profile_includes_picture_field(test_app, test_user):
    """Should include picture field in response."""

    @test_app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = test_user
        return await call_next(request)

    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_user.return_value = test_user
        client = TestClient(test_app)
        assert "picture" in client.get("/user/profile").json()


def test_get_enrolled_missions_success(test_app, test_user):
    """Should return list of enrolled missions."""
    enrolled_missions = [
        UserEnrolledMission(
            mission_id="mission1",
            mission_title="Learn Python",
            mission_short_description="Master Python programming",
            mission_skills=["Python"],
            progress=50.0,
            byte_size_checkpoints=["intro", "basics", "advanced", "conclusion"],
            completed_checkpoints=["intro", "basics"],
            enrolled_at=datetime(2025, 1, 1),
            last_accessed_at=datetime(2025, 1, 5),
            completed=False,
            updated_at=datetime(2025, 1, 5),
        )
    ]
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_enrolled_missions.return_value = enrolled_missions
        client = TestClient(test_app)
        resp = client.get("/user/enrolled-missions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["mission_id"] == "mission1"
        assert resp.json()[0]["progress"] == 50.0


def test_get_enrolled_missions_empty(test_app, test_user):
    """Should return empty list when no enrollments."""
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_enrolled_missions.return_value = []
        client = TestClient(test_app)
        resp = client.get("/user/enrolled-missions")
        assert resp.status_code == 200
        assert resp.json() == []


def test_get_enrolled_missions_requires_authentication(test_app):
    """Should require authentication."""
    test_app.include_router(router, prefix="/user")
    client = TestClient(test_app)
    resp = client.get("/user/enrolled-missions")
    assert resp.status_code in [401, 403]


def test_get_enrolled_missions_respects_limit(test_app, test_user):
    """Should respect limit parameter."""
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.get_enrolled_missions.return_value = []
        client = TestClient(test_app)
        client.get("/user/enrolled-missions?limit=50")
        mock_service.return_value.get_enrolled_missions.assert_called_once_with(
            test_user.id, limit=50
        )
