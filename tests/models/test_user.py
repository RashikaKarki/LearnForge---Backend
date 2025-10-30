"""Tests for User models.

Focus: Data validation and model structure only.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.user import (
    User,
    UserCreate,
    UserEnrolledMission,
    UserEnrolledMissionCreate,
    UserEnrolledMissionUpdate,
    UserUpdate,
)


@pytest.fixture
def test_user():
    return User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
    )


@pytest.fixture
def test_enrolled():
    return UserEnrolledMission(
        mission_id="mission123",
        mission_title="Test Mission",
        mission_short_description="Test description",
        mission_skills=["Python", "FastAPI"],
        progress=50.0,
        byte_size_checkpoints=["intro", "basics", "advanced"],
        enrolled_at=datetime(2025, 1, 1, 12, 0, 0),
        last_accessed_at=datetime(2025, 1, 2, 12, 0, 0),
        completed=False,
        updated_at=datetime(2025, 1, 2, 12, 0, 0),
    )


def test_create_with_all_fields(test_enrolled):
    assert test_enrolled.mission_id == "mission123"
    assert test_enrolled.mission_title == "Test Mission"
    assert test_enrolled.progress == 50.0
    assert len(test_enrolled.mission_skills) == 2


def test_create_with_defaults():
    enrolled = UserEnrolledMission(
        mission_id="mission123",
        mission_title="Test Mission",
        mission_short_description="Test description",
        byte_size_checkpoints=["intro", "basics", "advanced"],
    )
    assert enrolled.mission_skills == []
    assert enrolled.progress == 0.0
    assert enrolled.completed is False
    assert isinstance(enrolled.enrolled_at, datetime)


@pytest.mark.parametrize(
    "progress,valid",
    [
        (0.0, True),
        (50.0, True),
        (100.0, True),
        (-1.0, False),
        (101.0, False),
    ],
)
def test_progress_validation(progress, valid):
    if valid:
        enrolled = UserEnrolledMission(
            mission_id="m1",
            mission_title="Title",
            mission_short_description="Desc",
            progress=progress,
            byte_size_checkpoints=["intro", "basics"],
        )
        assert enrolled.progress == progress
    else:
        with pytest.raises(ValidationError):
            UserEnrolledMission(
                mission_id="m1",
                mission_title="Title",
                mission_short_description="Desc",
                progress=progress,
                byte_size_checkpoints=["intro", "basics"],
            )


def test_create_with_defaults_enrolled_mission_create():
    create_data = UserEnrolledMissionCreate(
        mission_id="mission123",
        mission_title="Test Mission",
        mission_short_description="Test description",
        byte_size_checkpoints=["intro", "basics", "advanced"],
    )
    assert create_data.mission_skills == []
    assert create_data.progress == 0.0
    assert create_data.completed is False


def test_all_fields_optional_enrolled_mission_update():
    update_data = UserEnrolledMissionUpdate()
    assert update_data.progress is None
    assert update_data.last_accessed_at is None
    assert update_data.completed is None


def test_partial_update_enrolled_mission_update():
    update_data = UserEnrolledMissionUpdate(progress=75.0)
    assert update_data.progress == 75.0
    assert update_data.completed is None


def test_create_with_all_fields_user():
    user = User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
        picture="https://example.com/pic.jpg",
        enrolled_missions=[],
        learning_style=["examples", "step-by-step"],
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )
    assert user.id == "user123"
    assert user.firebase_uid == "firebase123"
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.enrolled_missions == []
    assert user.learning_style == ["examples", "step-by-step"]


def test_create_with_defaults_user():
    user = User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
    )
    assert user.picture is None
    assert user.enrolled_missions == []
    assert user.learning_style == []
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_create_with_enrolled_missions_user():
    enrolled = UserEnrolledMission(
        mission_id="m1",
        mission_title="Mission 1",
        mission_short_description="Desc",
        byte_size_checkpoints=["intro", "basics"],
    )
    user = User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
        enrolled_missions=[enrolled],
    )
    assert len(user.enrolled_missions) == 1
    assert user.enrolled_missions[0].mission_id == "m1"


def test_learning_style_defaults_to_empty_list_user():
    user = User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
    )
    assert user.learning_style == []


def test_create_with_learning_style_user():
    user = User(
        id="user123",
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
        learning_style=["examples", "metaphors", "analogies", "step-by-step"],
    )
    assert len(user.learning_style) == 4
    assert "examples" in user.learning_style
    assert "step-by-step" in user.learning_style


@pytest.mark.parametrize(
    "email",
    [
        "invalid-email",
        "no-at-sign",
        "@no-local-part.com",
        "no-domain@",
        "",
    ],
)
def test_invalid_email_raises_error(email):
    with pytest.raises(ValidationError):
        User(
            id="user123",
            firebase_uid="firebase123",
            name="Test User",
            email=email,
        )


def test_create_with_all_fields_user_create():
    user_data = UserCreate(
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
        picture="https://example.com/pic.jpg",
    )
    assert user_data.firebase_uid == "firebase123"
    assert user_data.name == "Test User"
    assert user_data.email == "test@example.com"


def test_create_without_optional_fields_user_create():
    user_data = UserCreate(
        firebase_uid="firebase123",
        name="Test User",
        email="test@example.com",
    )
    assert user_data.picture is None


def test_all_fields_optional_user_update():
    update_data = UserUpdate()
    assert update_data.name is None
    assert update_data.email is None
    assert update_data.picture is None
    assert update_data.learning_style is None


def test_partial_update_name_only_user_update():
    update_data = UserUpdate(name="New Name")
    assert update_data.name == "New Name"
    assert update_data.email is None
    assert update_data.learning_style is None


def test_update_learning_style_user_update():
    update_data = UserUpdate(learning_style=["examples", "metaphors", "analogies"])
    assert update_data.learning_style == ["examples", "metaphors", "analogies"]
    assert update_data.name is None
    assert update_data.email is None


def test_update_learning_style_to_empty_list_user_update():
    update_data = UserUpdate(learning_style=[])
    assert update_data.learning_style == []
    assert update_data.name is None
    assert update_data.email is None


def test_update_all_fields_including_learning_style_user_update():
    update_data = UserUpdate(
        name="Updated Name",
        email="updated@example.com",
        picture="https://example.com/new-pic.jpg",
        learning_style=["step-by-step", "examples"],
    )
    assert update_data.name == "Updated Name"
    assert update_data.email == "updated@example.com"
    assert str(update_data.picture) == "https://example.com/new-pic.jpg"
    assert update_data.learning_style == ["step-by-step", "examples"]
