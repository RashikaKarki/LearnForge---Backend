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


def test_update_user_name_success(test_app, test_user):
    """Should successfully update user name."""
    updated_user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Updated Name",
        email="test@example.com",
        learning_style=["examples", "step-by-step"],
    )
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = updated_user
        client = TestClient(test_app)
        response = client.put(
            "/user/update",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        mock_service.return_value.update_user.assert_called_once()


def test_update_user_learning_style_success(test_app, test_user):
    """Should successfully update user learning style."""
    updated_user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
        learning_style=["metaphors", "analogies"],
    )
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = updated_user
        client = TestClient(test_app)
        response = client.put(
            "/user/update",
            json={"learning_style": ["metaphors", "analogies"]},
        )
        assert response.status_code == 200
        assert response.json()["learning_style"] == ["metaphors", "analogies"]
        mock_service.return_value.update_user.assert_called_once()


def test_update_user_name_and_learning_style_success(test_app, test_user):
    """Should successfully update both name and learning style."""
    updated_user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Updated Name",
        email="test@example.com",
        learning_style=["step-by-step", "examples"],
    )
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = updated_user
        client = TestClient(test_app)
        response = client.put(
            "/user/update",
            json={"name": "Updated Name", "learning_style": ["step-by-step", "examples"]},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
        assert response.json()["learning_style"] == ["step-by-step", "examples"]
        mock_service.return_value.update_user.assert_called_once()


def test_update_user_empty_body_success(test_app, test_user):
    """Should handle empty update body (no fields to update)."""
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = test_user
        client = TestClient(test_app)
        response = client.put("/user/update", json={})
        assert response.status_code == 200
        mock_service.return_value.update_user.assert_called_once()


def test_update_user_requires_authentication(test_app):
    """Should require authentication."""
    test_app.include_router(router, prefix="/user")
    client = TestClient(test_app)
    response = client.put("/user/update", json={"name": "New Name"})
    assert response.status_code in [401, 403]


def test_update_user_rejects_email_field(test_app, test_user):
    """Should ignore email field in update request (extra fields are ignored)."""
    updated_user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="New Name",
        email="test@example.com",  # Email should remain unchanged
        learning_style=[],
    )
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = updated_user
        client = TestClient(test_app)
        response = client.put(
            "/user/update",
            json={"name": "New Name", "email": "new@example.com"},
        )
        # Extra fields (email) should be ignored, request should succeed
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        # Verify that update_user was called (email field was ignored by Pydantic)
        mock_service.return_value.update_user.assert_called_once()


def test_update_user_rejects_picture_field(test_app, test_user):
    """Should ignore picture field in update request (extra fields are ignored)."""
    updated_user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="New Name",
        email="test@example.com",
        picture=None,  # Picture should remain unchanged
        learning_style=[],
    )
    test_app.dependency_overrides[get_current_user] = lambda: test_user
    test_app.include_router(router, prefix="/user")
    with patch("app.api.v1.routes.user.UserService") as mock_service:
        mock_service.return_value.update_user.return_value = updated_user
        client = TestClient(test_app)
        response = client.put(
            "/user/update",
            json={"name": "New Name", "picture": "https://example.com/pic.jpg"},
        )
        # Extra fields (picture) should be ignored, request should succeed
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"
        # Verify that update_user was called (picture field was ignored by Pydantic)
        mock_service.return_value.update_user.assert_called_once()
