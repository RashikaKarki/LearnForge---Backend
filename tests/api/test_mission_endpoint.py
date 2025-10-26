"""Unit tests for mission endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from starlette.testclient import TestClient

from app.api.v1.routes.mission import router
from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.mission import Mission
from app.models.user import User


# Test Data Fixtures (Keep visible in test file per guideline)
@pytest.fixture
def test_mission():
    """Test mission data - visible and specific to these tests."""
    return Mission(
        id="mission123",
        title="Learn Python",
        short_description="Master Python programming",
        description="A comprehensive guide to Python fundamentals",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Variables", "Functions", "Data Types"],
        learning_goal="Master Python fundamentals for programming",
        byte_size_checkpoints=[
            "Introduction",
            "Variables and Data Types",
            "Functions",
            "Conclusion",
        ],
        skills=["Python"],
        is_public=True,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def test_user():
    """Test user data - visible and specific to these tests."""
    return User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
        picture=None,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 1, 12, 0, 0),
    )


# Tests for GET /missions/{mission_id}
def test_get_mission_success(test_mission):
    """Test successful retrieval of a mission."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.return_value = test_mission

        client = TestClient(app)
        response = client.get("/mission123")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == test_mission.id
        assert response.json()["title"] == test_mission.title


def test_get_mission_not_found():
    """Test retrieval of non-existent mission returns 404."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )

        client = TestClient(app)
        response = client.get("/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# Tests for PATCH /missions/{mission_id}
def test_update_mission_success(test_mission, test_user):
    """Test successful mission update by creator."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        test_mission.creator_id = test_user.id
        updated = Mission(**test_mission.model_dump())
        updated.title = "Updated Title"
        mock_service.return_value.get_mission.return_value = test_mission
        mock_service.return_value.update_mission.return_value = updated

        client = TestClient(app)
        response = client.patch("/mission123", json={"title": "Updated Title"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Updated Title"


def test_update_mission_forbidden_not_creator(test_mission, test_user):
    """Test non-creator cannot update mission."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        test_mission.creator_id = "different-user-id"
        mock_service.return_value.get_mission.return_value = test_mission

        client = TestClient(app)
        response = client.patch("/mission123", json={"title": "Hacked"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "creator" in response.json()["detail"].lower()


def test_update_mission_not_found(test_user):
    """Test updating non-existent mission returns 404."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )

        client = TestClient(app)
        response = client.patch("/nonexistent", json={"title": "New"})

        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_mission_requires_authentication():
    """Test updating requires authentication."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: MagicMock()

    client = TestClient(app)
    response = client.patch("/mission123", json={"title": "New"})

    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
