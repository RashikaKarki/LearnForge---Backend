"""Unit tests for Enrollment model."""

from datetime import datetime

from pydantic import ValidationError
import pytest

from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate


@pytest.fixture
def valid_enrollment():
    return Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        progress=50.0,
    )


def test_enrollment_model_valid_creation(valid_enrollment):
    """Should create enrollment with all required fields."""
    assert valid_enrollment.id == "user123_mission123"
    assert valid_enrollment.user_id == "user123"
    assert valid_enrollment.mission_id == "mission123"
    assert valid_enrollment.progress == 50.0


def test_enrollment_model_progress_defaults_to_zero():
    """Should default progress to 0.0 when not provided."""
    enrollment = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert enrollment.progress == 0.0


def test_enrollment_model_timestamps_auto_generated():
    """Should auto-generate enrolled_at, last_accessed_at, created_at, and updated_at timestamps."""
    enrollment = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert isinstance(enrollment.enrolled_at, datetime)
    assert isinstance(enrollment.last_accessed_at, datetime)
    assert isinstance(enrollment.created_at, datetime)
    assert isinstance(enrollment.updated_at, datetime)


def test_enrollment_model_completed_defaults_to_false():
    """Should default completed to False when not provided."""
    enrollment = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )

    assert enrollment.completed is False


@pytest.mark.parametrize(
    "progress_value",
    [0.0, 25.5, 50.0, 75.9, 100.0],
)
def test_enrollment_progress_accepts_valid_range(progress_value):
    """Should accept progress values between 0.0 and 100.0."""
    enrollment = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        progress=progress_value,
    )

    assert enrollment.progress == progress_value


@pytest.mark.parametrize(
    "invalid_progress",
    [-1.0, -0.1, 100.1, 101.0, 200.0],
)
def test_enrollment_progress_rejects_out_of_range(invalid_progress):
    """Should raise ValidationError for progress outside 0-100 range."""
    with pytest.raises(ValidationError):
        Enrollment(
            id="user123_mission123",
            user_id="user123",
            mission_id="mission123",
            progress=invalid_progress,
        )


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("id", {"user_id": "user123", "mission_id": "mission123"}),
        ("user_id", {"id": "user123_mission123", "mission_id": "mission123"}),
        ("mission_id", {"id": "user123_mission123", "user_id": "user123"}),
    ],
)
def test_enrollment_model_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing."""
    with pytest.raises(ValidationError):
        Enrollment(**data)


def test_enrollment_create_valid():
    """Should create EnrollmentCreate with required fields."""
    enrollment_create = EnrollmentCreate(
        user_id="user123",
        mission_id="mission123",
    )

    assert enrollment_create.user_id == "user123"
    assert enrollment_create.mission_id == "mission123"
    assert enrollment_create.progress == 0.0


def test_enrollment_create_with_progress():
    """Should create EnrollmentCreate with custom progress."""
    enrollment_create = EnrollmentCreate(
        user_id="user123",
        mission_id="mission123",
        progress=50.0,
    )

    assert enrollment_create.progress == 50.0


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("user_id", {"mission_id": "mission123"}),
        ("mission_id", {"user_id": "user123"}),
    ],
)
def test_enrollment_create_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing in EnrollmentCreate."""
    with pytest.raises(ValidationError):
        EnrollmentCreate(**data)


def test_enrollment_update_all_fields_optional():
    """Should allow EnrollmentUpdate with no fields."""
    enrollment_update = EnrollmentUpdate()

    assert enrollment_update.progress is None
    assert enrollment_update.last_accessed_at is None
    assert enrollment_update.completed is None


def test_enrollment_update_progress_only():
    """Should allow updating only progress."""
    enrollment_update = EnrollmentUpdate(progress=75.0)

    assert enrollment_update.progress == 75.0
    assert enrollment_update.last_accessed_at is None


def test_enrollment_update_last_accessed_only():
    """Should allow updating only last_accessed_at."""
    now = datetime.now()
    enrollment_update = EnrollmentUpdate(last_accessed_at=now)

    assert enrollment_update.progress is None
    assert enrollment_update.last_accessed_at == now


def test_enrollment_update_all_fields():
    """Should allow EnrollmentUpdate with all fields."""
    now = datetime.now()
    enrollment_update = EnrollmentUpdate(
        progress=90.0,
        last_accessed_at=now,
        completed=True,
    )

    assert enrollment_update.progress == 90.0
    assert enrollment_update.last_accessed_at == now
    assert enrollment_update.completed is True


@pytest.mark.parametrize(
    "invalid_progress",
    [-5.0, -0.01, 100.01, 150.0],
)
def test_enrollment_update_progress_rejects_out_of_range(invalid_progress):
    """Should raise ValidationError for progress outside 0-100 range in update."""
    with pytest.raises(ValidationError):
        EnrollmentUpdate(progress=invalid_progress)


def test_enrollment_composite_id_format():
    """Should accept composite ID in user_id_mission_id format."""
    enrollment = Enrollment(
        id="user456_mission789",
        user_id="user456",
        mission_id="mission789",
    )

    assert enrollment.id == "user456_mission789"
    assert enrollment.user_id == "user456"
    assert enrollment.mission_id == "mission789"


def test_enrollment_update_completed_only():
    """Should allow updating only completed field."""
    enrollment_update = EnrollmentUpdate(completed=True)

    assert enrollment_update.completed is True
    assert enrollment_update.progress is None
    assert enrollment_update.last_accessed_at is None


def test_enrollment_completed_accepts_boolean():
    """Should accept boolean values for completed field."""
    enrollment_true = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        completed=True,
    )
    enrollment_false = Enrollment(
        id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
        completed=False,
    )

    assert enrollment_true.completed is True
    assert enrollment_false.completed is False
