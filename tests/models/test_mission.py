"""Unit tests for Mission model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.mission import Mission, MissionCreate, MissionUpdate


def test_mission_model_valid_creation():
    """Should create mission with all required fields."""
    mission = Mission(
        id="mission123",
        title="Learn Python Basics",
        description="A comprehensive guide to Python fundamentals",
        creator_id="user123",
        is_public=True,
        skills=["Python", "Programming"],
    )

    assert mission.id == "mission123"
    assert mission.title == "Learn Python Basics"
    assert mission.description == "A comprehensive guide to Python fundamentals"
    assert mission.creator_id == "user123"
    assert mission.is_public is True
    assert mission.skills == ["Python", "Programming"]


def test_mission_model_skills_defaults_to_empty_list():
    """Should default skills to empty list when not provided."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        description="Python guide",
        creator_id="user123",
    )

    assert mission.skills == []


def test_mission_model_is_public_defaults_to_true():
    """Should default is_public to True when not provided."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        description="Python guide",
        creator_id="user123",
    )

    assert mission.is_public is True


def test_mission_model_timestamps_auto_generated():
    """Should auto-generate created_at and updated_at timestamps."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        description="Python guide",
        creator_id="user123",
    )

    assert isinstance(mission.created_at, datetime)
    assert isinstance(mission.updated_at, datetime)


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("id", {"title": "Title", "description": "Desc", "creator_id": "user123"}),
        ("title", {"id": "mission123", "description": "Desc", "creator_id": "user123"}),
        ("description", {"id": "mission123", "title": "Title", "creator_id": "user123"}),
        ("creator_id", {"id": "mission123", "title": "Title", "description": "Desc"}),
    ],
)
def test_mission_model_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing."""
    with pytest.raises(ValidationError):
        Mission(**data)


def test_mission_create_valid():
    """Should create MissionCreate with required fields."""
    mission_create = MissionCreate(
        title="Learn Python",
        description="Python guide",
        creator_id="user123",
        skills=["Python", "Programming"],
    )

    assert mission_create.title == "Learn Python"
    assert mission_create.description == "Python guide"
    assert mission_create.creator_id == "user123"
    assert mission_create.is_public is True
    assert mission_create.skills == ["Python", "Programming"]


def test_mission_create_is_public_can_be_false():
    """Should allow is_public to be set to False."""
    mission_create = MissionCreate(
        title="Private Mission",
        description="Private guide",
        creator_id="user123",
        is_public=False,
        skills=None,
    )

    assert mission_create.is_public is False


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("title", {"description": "Desc", "creator_id": "user123"}),
        ("description", {"title": "Title", "creator_id": "user123"}),
        ("creator_id", {"title": "Title", "description": "Desc"}),
    ],
)
def test_mission_create_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing in MissionCreate."""
    with pytest.raises(ValidationError):
        MissionCreate(**data)


def test_mission_update_all_fields_optional():
    """Should allow MissionUpdate with no fields."""
    mission_update = MissionUpdate()

    assert mission_update.title is None
    assert mission_update.description is None
    assert mission_update.is_public is None


def test_mission_update_partial_fields():
    """Should allow MissionUpdate with only some fields."""
    mission_update = MissionUpdate(title="Updated Title")

    assert mission_update.title == "Updated Title"
    assert mission_update.description is None
    assert mission_update.is_public is None


def test_mission_update_all_fields():
    """Should allow MissionUpdate with all fields."""
    mission_update = MissionUpdate(
        title="Updated Title",
        description="Updated Description",
        is_public=False,
    )

    assert mission_update.title == "Updated Title"
    assert mission_update.description == "Updated Description"
    assert mission_update.is_public is False


@pytest.mark.parametrize(
    "is_public_value",
    [True, False],
)
def test_mission_is_public_accepts_boolean(is_public_value):
    """Should accept both True and False for is_public."""
    mission = Mission(
        id="mission123",
        title="Test Mission",
        description="Test",
        creator_id="user123",
        is_public=is_public_value,
    )

    assert mission.is_public is is_public_value
