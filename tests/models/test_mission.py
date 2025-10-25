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
        short_description="An introductory course on Python",
        description="A comprehensive guide to Python fundamentals",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Variables", "Functions", "Data Types"],
        learning_goal="Master Python fundamentals for data science",
        byte_size_checkpoints=["Intro to Python", "Variables and Data Types", "Functions"],
        is_public=True,
        skills=["Python", "Programming"],
    )

    assert mission.id == "mission123"
    assert mission.title == "Learn Python Basics"
    assert mission.short_description == "An introductory course on Python"
    assert mission.description == "A comprehensive guide to Python fundamentals"
    assert mission.creator_id == "user123"
    assert mission.level == "Beginner"
    assert mission.topics_to_cover == ["Variables", "Functions", "Data Types"]
    assert mission.learning_goal == "Master Python fundamentals for data science"
    assert mission.byte_size_checkpoints == [
        "Intro to Python",
        "Variables and Data Types",
        "Functions",
    ]
    assert mission.is_public is True
    assert mission.skills == ["Python", "Programming"]


def test_mission_model_skills_defaults_to_empty_list():
    """Should default skills to empty list when not provided."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        short_description="An introductory course on Python",
        description="Python guide",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Python Basics"],
        learning_goal="Learn Python programming",
        byte_size_checkpoints=["Introduction", "Variables", "Functions", "Conclusion"],
    )

    assert mission.skills == []


def test_mission_model_is_public_defaults_to_true():
    """Should default is_public to True when not provided."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        short_description="An introductory course on Python",
        description="Python guide",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Python Basics"],
        learning_goal="Learn Python programming",
        byte_size_checkpoints=["Introduction", "Variables", "Functions", "Conclusion"],
    )

    assert mission.is_public is True


def test_mission_model_timestamps_auto_generated():
    """Should auto-generate created_at and updated_at timestamps."""
    mission = Mission(
        id="mission123",
        title="Learn Python",
        short_description="An introductory course on Python",
        description="Python guide",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Python Basics"],
        learning_goal="Learn Python programming",
        byte_size_checkpoints=["Introduction", "Variables", "Functions", "Conclusion"],
    )

    assert isinstance(mission.created_at, datetime)
    assert isinstance(mission.updated_at, datetime)


@pytest.mark.parametrize(
    "missing_field,data",
    [
        (
            "id",
            {
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "title",
            {
                "id": "mission123",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "short_description",
            {
                "id": "mission123",
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "description",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "creator_id",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "level",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "topics_to_cover",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "learning_goal",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "byte_size_checkpoints",
            {
                "id": "mission123",
                "title": "Title",
                "short_description": "Short Desc",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
            },
        ),
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
        short_description="An introductory course on Python",
        description="Python guide",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Variables", "Functions"],
        learning_goal="Master Python fundamentals",
        byte_size_checkpoints=["Introduction", "Variables", "Functions", "Conclusion"],
        skills=["Python", "Programming"],
    )

    assert mission_create.title == "Learn Python"
    assert mission_create.short_description == "An introductory course on Python"
    assert mission_create.description == "Python guide"
    assert mission_create.creator_id == "user123"
    assert mission_create.level == "Beginner"
    assert mission_create.topics_to_cover == ["Variables", "Functions"]
    assert mission_create.learning_goal == "Master Python fundamentals"
    assert mission_create.byte_size_checkpoints == [
        "Introduction",
        "Variables",
        "Functions",
        "Conclusion",
    ]
    assert mission_create.is_public is True
    assert mission_create.skills == ["Python", "Programming"]


def test_mission_create_is_public_can_be_false():
    """Should allow is_public to be set to False."""
    mission_create = MissionCreate(
        title="Private Mission",
        short_description="A private guide",
        description="Private guide",
        creator_id="user123",
        level="Intermediate",
        topics_to_cover=["Advanced Topics"],
        learning_goal="Learn advanced concepts",
        byte_size_checkpoints=["Intro", "Advanced Concepts", "Practice", "Review"],
        is_public=False,
        skills=None,
    )

    assert mission_create.is_public is False


@pytest.mark.parametrize(
    "missing_field,data",
    [
        (
            "title",
            {
                "description": "Desc",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "description",
            {
                "title": "Title",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "creator_id",
            {
                "title": "Title",
                "description": "Desc",
                "short_description": "Short Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "short_description",
            {
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "level",
            {
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "topics_to_cover",
            {
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "level": "Beginner",
                "learning_goal": "Goal",
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "learning_goal",
            {
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "byte_size_checkpoints": ["CP1", "CP2", "CP3", "CP4"],
            },
        ),
        (
            "byte_size_checkpoints",
            {
                "title": "Title",
                "description": "Desc",
                "creator_id": "user123",
                "short_description": "Short Desc",
                "level": "Beginner",
                "topics_to_cover": ["Topic1"],
                "learning_goal": "Goal",
            },
        ),
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
        short_description="Test Mission",
        description="Test",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Topic1"],
        learning_goal="Learn something",
        byte_size_checkpoints=["CP1", "CP2", "CP3", "CP4"],
        is_public=is_public_value,
    )

    assert mission.is_public is is_public_value


def test_mission_create_byte_size_checkpoints_min_length():
    """Should enforce minimum 4 checkpoints."""
    with pytest.raises(ValidationError) as exc_info:
        MissionCreate(
            title="Test",
            short_description="Test",
            description="Test",
            creator_id="user123",
            level="Beginner",
            topics_to_cover=["Topic1"],
            learning_goal="Learn something",
            byte_size_checkpoints=["CP1", "CP2", "CP3"],  # Only 3, needs 4
        )

    assert "byte_size_checkpoints" in str(exc_info.value)


def test_mission_create_byte_size_checkpoints_max_length():
    """Should enforce maximum 6 checkpoints."""
    with pytest.raises(ValidationError) as exc_info:
        MissionCreate(
            title="Test",
            short_description="Test",
            description="Test",
            creator_id="user123",
            level="Beginner",
            topics_to_cover=["Topic1"],
            learning_goal="Learn something",
            byte_size_checkpoints=["CP1", "CP2", "CP3", "CP4", "CP5", "CP6", "CP7"],  # 7, max is 6
        )

    assert "byte_size_checkpoints" in str(exc_info.value)


@pytest.mark.parametrize(
    "valid_level",
    ["Beginner", "Intermediate", "Advanced"],
)
def test_mission_create_valid_level_values(valid_level):
    """Should accept valid level values: Beginner, Intermediate, Advanced."""
    mission_create = MissionCreate(
        title="Test",
        short_description="Test",
        description="Test",
        creator_id="user123",
        level=valid_level,
        topics_to_cover=["Topic1"],
        learning_goal="Learn something",
        byte_size_checkpoints=["CP1", "CP2", "CP3", "CP4"],
    )

    assert mission_create.level == valid_level


def test_mission_create_invalid_level_raises():
    """Should reject invalid level values."""
    with pytest.raises(ValidationError) as exc_info:
        MissionCreate(
            title="Test",
            short_description="Test",
            description="Test",
            creator_id="user123",
            level="Expert",  # Invalid level
            topics_to_cover=["Topic1"],
            learning_goal="Learn something",
            byte_size_checkpoints=["CP1", "CP2", "CP3", "CP4"],
        )

    assert "level" in str(exc_info.value)
