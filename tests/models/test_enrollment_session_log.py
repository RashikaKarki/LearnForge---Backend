"""Unit tests for EnrollmentSessionLog model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.enrollment_session_log import (
    EnrollmentSessionLog,
    EnrollmentSessionLogCreate,
    EnrollmentSessionLogUpdate,
)


@pytest.fixture
def valid_enrollment_session_log():
    """Valid enrollment session log."""
    return EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        status="created",
    )


def test_enrollment_session_log_model_valid_creation(valid_enrollment_session_log):
    """Should create enrollment session log with all required fields."""
    assert valid_enrollment_session_log.id == "session_log123"
    assert valid_enrollment_session_log.enrollment_id == "user123_mission123"
    assert valid_enrollment_session_log.user_id == "user123"
    assert valid_enrollment_session_log.mission_id == "mission123"
    assert valid_enrollment_session_log.status == "created"


def test_enrollment_session_log_status_defaults_to_created():
    """Should default status to 'created' when not provided."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert session_log.status == "created"


def test_enrollment_session_log_timestamps_auto_generated():
    """Should auto-generate created_at and updated_at timestamps."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert isinstance(session_log.created_at, datetime)
    assert isinstance(session_log.updated_at, datetime)


def test_enrollment_session_log_started_at_defaults_to_none():
    """Should default started_at to None when not provided."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert session_log.started_at is None


def test_enrollment_session_log_completed_at_defaults_to_none():
    """Should default completed_at to None when not provided."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert session_log.completed_at is None


@pytest.mark.parametrize(
    "status_value",
    ["created", "started", "completed"],
)
def test_enrollment_session_log_status_accepts_valid_values(status_value):
    """Should accept valid status values."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        status=status_value,
    )

    assert session_log.status == status_value


@pytest.mark.parametrize(
    "invalid_status",
    ["active", "pending", "error", "abandoned", ""],
)
def test_enrollment_session_log_status_rejects_invalid_values(invalid_status):
    """Should raise ValidationError for invalid status values."""
    with pytest.raises(ValidationError):
        EnrollmentSessionLog(
            id="session_log123",
            enrollment_id="user123_mission123",
            user_id="user123",
            mission_id="mission123",
            status=invalid_status,
        )


@pytest.mark.parametrize(
    "missing_field,data",
    [
        (
            "id",
            {
                "enrollment_id": "user123_mission123",
                "user_id": "user123",
                "mission_id": "mission123",
            },
        ),
        (
            "enrollment_id",
            {"id": "session_log123", "user_id": "user123", "mission_id": "mission123"},
        ),
        (
            "user_id",
            {
                "id": "session_log123",
                "enrollment_id": "user123_mission123",
                "mission_id": "mission123",
            },
        ),
        (
            "mission_id",
            {"id": "session_log123", "enrollment_id": "user123_mission123", "user_id": "user123"},
        ),
    ],
)
def test_enrollment_session_log_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing."""
    with pytest.raises(ValidationError):
        EnrollmentSessionLog(**data)


def test_enrollment_session_log_with_started_at():
    """Should accept started_at timestamp."""
    started_at = datetime.now()
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        status="started",
        started_at=started_at,
    )

    assert session_log.started_at == started_at


def test_enrollment_session_log_with_completed_at():
    """Should accept completed_at timestamp."""
    completed_at = datetime.now()
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        status="completed",
        completed_at=completed_at,
    )

    assert session_log.completed_at == completed_at


# EnrollmentSessionLogCreate tests
def test_enrollment_session_log_create_valid():
    """Should create EnrollmentSessionLogCreate with required fields."""
    create_data = EnrollmentSessionLogCreate(
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert create_data.enrollment_id == "user123_mission123"
    assert create_data.user_id == "user123"
    assert create_data.mission_id == "mission123"


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("enrollment_id", {"user_id": "user123", "mission_id": "mission123"}),
        ("user_id", {"enrollment_id": "user123_mission123", "mission_id": "mission123"}),
        ("mission_id", {"enrollment_id": "user123_mission123", "user_id": "user123"}),
    ],
)
def test_enrollment_session_log_create_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing in EnrollmentSessionLogCreate."""
    with pytest.raises(ValidationError):
        EnrollmentSessionLogCreate(**data)


# EnrollmentSessionLogUpdate tests
def test_enrollment_session_log_update_all_fields_optional():
    """Should allow EnrollmentSessionLogUpdate with no fields."""
    update_data = EnrollmentSessionLogUpdate()

    assert update_data.status is None
    assert update_data.started_at is None
    assert update_data.completed_at is None


def test_enrollment_session_log_update_status_only():
    """Should allow updating only status."""
    update_data = EnrollmentSessionLogUpdate(status="started")

    assert update_data.status == "started"
    assert update_data.started_at is None
    assert update_data.completed_at is None


def test_enrollment_session_log_update_started_at_only():
    """Should allow updating only started_at."""
    now = datetime.now()
    update_data = EnrollmentSessionLogUpdate(started_at=now)

    assert update_data.status is None
    assert update_data.started_at == now
    assert update_data.completed_at is None


def test_enrollment_session_log_update_completed_at_only():
    """Should allow updating only completed_at."""
    now = datetime.now()
    update_data = EnrollmentSessionLogUpdate(completed_at=now)

    assert update_data.status is None
    assert update_data.started_at is None
    assert update_data.completed_at == now


def test_enrollment_session_log_update_all_fields():
    """Should allow EnrollmentSessionLogUpdate with all fields."""
    now = datetime.now()
    update_data = EnrollmentSessionLogUpdate(
        status="completed",
        started_at=now,
        completed_at=now,
    )

    assert update_data.status == "completed"
    assert update_data.started_at == now
    assert update_data.completed_at == now


@pytest.mark.parametrize(
    "invalid_status",
    ["active", "pending", "error", ""],
)
def test_enrollment_session_log_update_status_rejects_invalid_values(invalid_status):
    """Should raise ValidationError for invalid status values in update."""
    with pytest.raises(ValidationError):
        EnrollmentSessionLogUpdate(status=invalid_status)


def test_enrollment_session_log_composite_enrollment_id_format():
    """Should accept enrollment_id in user_id_mission_id format."""
    session_log = EnrollmentSessionLog(
        id="session_log123",
        enrollment_id="user456_mission789",
        user_id="user456",
        mission_id="mission789",
    )

    assert session_log.enrollment_id == "user456_mission789"
    assert session_log.user_id == "user456"
    assert session_log.mission_id == "mission789"
