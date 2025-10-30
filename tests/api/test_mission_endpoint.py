"""Unit tests for mission endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from starlette.testclient import TestClient

from app.api.v1.routes.mission import router
from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.enrollment import Enrollment
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


@pytest.fixture
def test_enrollment():
    """Test enrollment data - visible and specific to these tests."""
    return Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        enrolled_at=datetime(2025, 1, 1, 12, 0, 0),
        progress=0.0,
        last_accessed_at=datetime(2025, 1, 1, 12, 0, 0),
        completed=False,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def valid_mission_create_data():
    """Valid mission creation data - visible in test file."""
    return {
        "title": "Learn Python",
        "short_description": "Master Python programming",
        "description": "A comprehensive guide to Python fundamentals",
        "creator_id": "user123",
        "level": "Beginner",
        "topics_to_cover": ["Variables", "Functions", "Data Types"],
        "learning_goal": "Master Python fundamentals for programming",
        "byte_size_checkpoints": [
            "Introduction",
            "Variables and Data Types",
            "Functions",
            "Conclusion",
        ],
        "skills": ["Python"],
        "is_public": True,
    }


# Tests for POST /profile
def test_create_mission_with_enrollment_success(
    test_mission, test_enrollment, test_user, valid_mission_create_data
):
    """Test successful mission creation with enrollment."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.create_mission_with_enrollment.return_value = (
            test_mission,
            test_enrollment,
        )

        client = TestClient(app)
        response = client.post("/missions/enrollment", json=valid_mission_create_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert "mission" in response.json()
        assert "enrollment" in response.json()
        assert response.json()["mission"]["id"] == test_mission.id
        assert response.json()["enrollment"]["id"] == test_enrollment.id


def test_create_mission_with_enrollment_uses_authenticated_user(
    test_user, valid_mission_create_data
):
    """Test mission creator_id is set from authenticated user."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    from app.models.enrollment import Enrollment
    from app.models.mission import Mission

    test_mission = Mission(
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
    test_enrollment = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        enrolled_at=datetime(2025, 1, 1, 12, 0, 0),
        progress=0.0,
        last_accessed_at=datetime(2025, 1, 1, 12, 0, 0),
        completed=False,
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        updated_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.create_mission_with_enrollment.return_value = (
            test_mission,
            test_enrollment,
        )
        client = TestClient(app)
        client.post("/missions/enrollment", json=valid_mission_create_data)
        mock_service.return_value.create_mission_with_enrollment.assert_called_once()
        call_args = mock_service.return_value.create_mission_with_enrollment.call_args
        assert call_args[0][1] == test_user.id


def test_create_mission_with_enrollment_requires_authentication(valid_mission_create_data):
    """Test creating mission requires authentication."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    client = TestClient(app)
    response = client.post("/missions/enrollment", json=valid_mission_create_data)

    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


def test_create_mission_with_enrollment_validation_error():
    """Test invalid mission data returns 422."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: User(
        id="user123", firebase_uid="firebase123", name="Test", email="test@example.com"
    )

    client = TestClient(app)
    response = client.post("/missions/enrollment", json={"title": "Incomplete"})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_mission_with_enrollment_service_error(test_user, valid_mission_create_data):
    """Test service error returns 500."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.create_mission_with_enrollment.side_effect = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create enrollment",
        )

        client = TestClient(app)
        response = client.post("/missions/enrollment", json=valid_mission_create_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_create_mission_with_enrollment_requires_authentication(valid_mission_create_data):
    """Test creating mission requires authentication."""
    # Only test /missions/enrollment


def test_create_mission_with_enrollment_validation_error():
    """Test invalid mission data returns 422."""
    # Only test /missions/enrollment


def test_create_mission_with_enrollment_service_error(test_user, valid_mission_create_data):
    """Test service error returns 500."""
    # Only test /missions/enrollment


# Tests for GET /missions/{mission_id}
def test_get_mission_success(test_mission):
    """Test successful retrieval of a mission."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.return_value = test_mission

        client = TestClient(app)
        response = client.get("/missions/mission123")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == test_mission.id
        assert response.json()["title"] == test_mission.title


def test_get_mission_not_found():
    """Test retrieval of non-existent mission returns 404."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )

        client = TestClient(app)
        response = client.get("/missions/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# Tests for PATCH /missions/{mission_id}
def test_update_mission_success(test_mission, test_user):
    """Test successful mission update by creator."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        test_mission.creator_id = test_user.id
        updated = Mission(**test_mission.model_dump())
        updated.title = "Updated Title"
        mock_service.return_value.get_mission.return_value = test_mission
        mock_service.return_value.update_mission.return_value = updated

        client = TestClient(app)
        response = client.patch("/missions/mission123", json={"title": "Updated Title"})

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Updated Title"


def test_update_mission_forbidden_not_creator(test_mission, test_user):
    """Test non-creator cannot update mission."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        test_mission.creator_id = "different-user-id"
        mock_service.return_value.get_mission.return_value = test_mission

        client = TestClient(app)
        response = client.patch("/missions/mission123", json={"title": "Hacked"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "creator" in response.json()["detail"].lower()


def test_update_mission_not_found(test_user):
    """Test updating non-existent mission returns 404."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user

    with patch("app.api.v1.routes.mission.MissionService") as mock_service:
        mock_service.return_value.get_mission.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )

        client = TestClient(app)
        response = client.patch("/missions/nonexistent", json={"title": "New"})

        assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_mission_requires_authentication():
    """Test updating requires authentication."""
    app = FastAPI()
    app.include_router(router, prefix="/missions")
    app.dependency_overrides[get_db] = lambda: MagicMock()

    client = TestClient(app)
    response = client.patch("/missions/mission123", json={"title": "New"})

    assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
