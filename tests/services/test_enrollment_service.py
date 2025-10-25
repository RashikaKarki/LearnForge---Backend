"""Unit tests for EnrollmentService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.enrollment import (
    CheckpointProgressCreate,
    CheckpointProgressUpdate,
    EnrollmentCreate,
    EnrollmentUpdate,
)
from app.services.enrollment_service import EnrollmentService
from tests.mocks.firestore import FirestoreMocks


@pytest.fixture
def valid_enrollment_create_data():
    """Test data for creating an enrollment."""
    return EnrollmentCreate(user_id="user123", mission_id="mission123", progress=0.0)


@pytest.fixture
def existing_enrollment():
    """Existing enrollment dict as returned from Firestore."""
    return {
        "id": "user123_mission123",
        "user_id": "user123",
        "mission_id": "mission123",
        "enrolled_at": datetime(2025, 1, 1, 12, 0, 0),
        "progress": 50.0,
        "last_accessed_at": datetime(2025, 1, 1, 12, 0, 0),
        "completed": False,
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
        "updated_at": datetime(2025, 1, 1, 12, 0, 0),
    }


def test_create_enrollment_success(valid_enrollment_create_data):
    """Should create enrollment when user and mission exist."""
    enrollments_collection = FirestoreMocks.collection_empty()
    users_collection = MagicMock()
    missions_collection = MagicMock()

    # Mock user and mission exist
    user_doc = FirestoreMocks.document_exists("user123", {"id": "user123"})
    mission_doc = FirestoreMocks.document_exists("mission123", {"id": "mission123"})
    users_collection.document.return_value.get.return_value = user_doc
    missions_collection.document.return_value.get.return_value = mission_doc

    # Mock enrollment doesn't exist yet
    enrollment_doc = FirestoreMocks.document_not_found()
    enrollments_collection.document.return_value.get.return_value = enrollment_doc
    enrollments_collection.document.return_value.set = MagicMock()

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "enrollments": enrollments_collection,
        "users": users_collection,
        "missions": missions_collection,
    }[name]

    service = EnrollmentService(db)
    enrollment = service.create_enrollment(valid_enrollment_create_data)

    assert enrollment.user_id == "user123"
    assert enrollment.mission_id == "mission123"
    assert enrollment.id == "user123_mission123"
    enrollments_collection.document.return_value.set.assert_called_once()


def test_create_enrollment_user_not_found_raises_404(valid_enrollment_create_data):
    """Should raise 404 when user doesn't exist."""
    users_collection = MagicMock()
    user_doc = FirestoreMocks.document_not_found()
    users_collection.document.return_value.get.return_value = user_doc

    db = MagicMock()
    db.collection.return_value = users_collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_enrollment(valid_enrollment_create_data)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "User" in exc.value.detail


def test_create_enrollment_mission_not_found_raises_404(valid_enrollment_create_data):
    """Should raise 404 when mission doesn't exist."""
    enrollments_collection = MagicMock()
    users_collection = MagicMock()
    missions_collection = MagicMock()

    # User exists, mission doesn't
    user_doc = FirestoreMocks.document_exists("user123", {"id": "user123"})
    mission_doc = FirestoreMocks.document_not_found()
    users_collection.document.return_value.get.return_value = user_doc
    missions_collection.document.return_value.get.return_value = mission_doc

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "enrollments": enrollments_collection,
        "users": users_collection,
        "missions": missions_collection,
    }[name]

    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_enrollment(valid_enrollment_create_data)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Mission" in exc.value.detail


def test_create_enrollment_already_exists_raises_400(valid_enrollment_create_data):
    """Should raise 400 when enrollment already exists."""
    enrollments_collection = MagicMock()
    users_collection = MagicMock()
    missions_collection = MagicMock()

    # User and mission exist
    user_doc = FirestoreMocks.document_exists("user123", {"id": "user123"})
    mission_doc = FirestoreMocks.document_exists("mission123", {"id": "mission123"})
    users_collection.document.return_value.get.return_value = user_doc
    missions_collection.document.return_value.get.return_value = mission_doc

    # Enrollment already exists
    enrollment_doc = FirestoreMocks.document_exists(
        "user123_mission123", {"id": "user123_mission123"}
    )
    enrollments_collection.document.return_value.get.return_value = enrollment_doc

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "enrollments": enrollments_collection,
        "users": users_collection,
        "missions": missions_collection,
    }[name]

    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_enrollment(valid_enrollment_create_data)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already enrolled" in exc.value.detail


def test_get_enrollment_found_returns_enrollment(existing_enrollment):
    """Should return enrollment when it exists."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_exists("user123_mission123", existing_enrollment)
    collection.document.return_value.get.return_value = enrollment_doc

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    enrollment = service.get_enrollment("user123", "mission123")

    assert enrollment.id == existing_enrollment["id"]
    assert enrollment.progress == existing_enrollment["progress"]


def test_get_enrollment_not_found_raises_404():
    """Should raise 404 when enrollment doesn't exist."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = enrollment_doc

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_enrollment("user123", "mission123")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_update_enrollment_success(existing_enrollment):
    """Should update enrollment progress."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists("user123_mission123", existing_enrollment),
        FirestoreMocks.document_exists(
            "user123_mission123", {**existing_enrollment, "progress": 75.0}
        ),
    ]

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    update_data = EnrollmentUpdate(progress=75.0)
    enrollment = service.update_enrollment("user123", "mission123", update_data)

    assert enrollment.progress == 75.0
    doc_ref.update.assert_called_once()


def test_update_enrollment_not_found_raises_404():
    """Should raise 404 when updating non-existent enrollment."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_enrollment("user123", "mission123", EnrollmentUpdate(progress=50.0))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_delete_enrollment_success(existing_enrollment):
    """Should delete enrollment successfully."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_exists(
        "user123_mission123", existing_enrollment
    )

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    result = service.delete_enrollment("user123", "mission123")

    assert "deleted successfully" in result["message"]
    doc_ref.delete.assert_called_once()


def test_delete_enrollment_not_found_raises_404():
    """Should raise 404 when deleting non-existent enrollment."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.delete_enrollment("user123", "mission123")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_enrollments_by_user(existing_enrollment):
    """Should return all enrollments for a user."""
    enrollments_data = [
        existing_enrollment,
        {**existing_enrollment, "id": "user123_mission456", "mission_id": "mission456"},
    ]
    collection = FirestoreMocks.collection_with_items(enrollments_data)
    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    enrollments = service.get_enrollments_by_user("user123")

    assert len(enrollments) == 2
    assert all(e.user_id == "user123" for e in enrollments)


def test_get_enrollments_by_mission(existing_enrollment):
    """Should return all enrollments for a mission."""
    enrollments_data = [
        existing_enrollment,
        {**existing_enrollment, "id": "user456_mission123", "user_id": "user456"},
    ]
    collection = FirestoreMocks.collection_with_items(enrollments_data)
    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    enrollments = service.get_enrollments_by_mission("mission123")

    assert len(enrollments) == 2
    assert all(e.mission_id == "mission123" for e in enrollments)


def test_update_last_accessed(existing_enrollment):
    """Should update last_accessed_at timestamp."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists("user123_mission123", existing_enrollment),
        FirestoreMocks.document_exists("user123_mission123", existing_enrollment),
    ]

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    enrollment = service.update_last_accessed("user123", "mission123")

    assert enrollment is not None
    doc_ref.update.assert_called_once()
    # Verify last_accessed_at and updated_at were updated
    update_call_args = doc_ref.update.call_args[0][0]
    assert "last_accessed_at" in update_call_args
    assert "updated_at" in update_call_args


def test_create_enrollment_sets_completed_to_false(valid_enrollment_create_data):
    """Should set completed to False when creating enrollment."""
    enrollments_collection = FirestoreMocks.collection_empty()
    users_collection = MagicMock()
    missions_collection = MagicMock()

    # Mock user and mission exist
    user_doc = FirestoreMocks.document_exists("user123", {"id": "user123"})
    mission_doc = FirestoreMocks.document_exists("mission123", {"id": "mission123"})
    users_collection.document.return_value.get.return_value = user_doc
    missions_collection.document.return_value.get.return_value = mission_doc

    # Mock enrollment doesn't exist yet
    enrollment_doc = FirestoreMocks.document_not_found()
    enrollments_collection.document.return_value.get.return_value = enrollment_doc
    enrollments_collection.document.return_value.set = MagicMock()

    db = MagicMock()
    db.collection.side_effect = lambda name: {
        "enrollments": enrollments_collection,
        "users": users_collection,
        "missions": missions_collection,
    }[name]

    service = EnrollmentService(db)
    enrollment = service.create_enrollment(valid_enrollment_create_data)

    assert enrollment.completed is False
    assert enrollment.created_at is not None
    assert enrollment.updated_at is not None


def test_update_enrollment_updates_completed_field(existing_enrollment):
    """Should update completed field in enrollment."""
    collection = MagicMock()
    doc_ref = collection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists("user123_mission123", existing_enrollment),
        FirestoreMocks.document_exists(
            "user123_mission123", {**existing_enrollment, "completed": True}
        ),
    ]

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    update_data = EnrollmentUpdate(completed=True)
    enrollment = service.update_enrollment("user123", "mission123", update_data)

    assert enrollment.completed is True
    doc_ref.update.assert_called_once()
    # Verify updated_at was set
    update_call_args = doc_ref.update.call_args[0][0]
    assert "updated_at" in update_call_args


# Checkpoint Progress Tests


def test_create_checkpoint_progress_success(existing_enrollment):
    """Should create checkpoint progress entry successfully."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_exists("user123_mission123", existing_enrollment)
    collection.document.return_value.get.return_value = enrollment_doc

    # Mock subcollection
    subcollection = MagicMock()
    checkpoint_doc = FirestoreMocks.document_not_found()
    subcollection.document.return_value.get.return_value = checkpoint_doc
    subcollection.document.return_value.set = MagicMock()
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    checkpoint_progress_data = CheckpointProgressCreate(
        checkpoint_id="checkpoint123",
        completed=False,
    )
    checkpoint_progress = service.create_checkpoint_progress(
        "user123", "mission123", checkpoint_progress_data
    )

    assert checkpoint_progress.checkpoint_id == "checkpoint123"
    assert checkpoint_progress.completed is False
    assert checkpoint_progress.created_at is not None
    assert checkpoint_progress.updated_at is not None
    subcollection.document.return_value.set.assert_called_once()


def test_create_checkpoint_progress_enrollment_not_found():
    """Should raise 404 when enrollment doesn't exist."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = enrollment_doc

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    checkpoint_progress_data = CheckpointProgressCreate(
        checkpoint_id="checkpoint123",
        completed=False,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_checkpoint_progress("user123", "mission123", checkpoint_progress_data)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Enrollment not found" in exc.value.detail


def test_create_checkpoint_progress_already_exists(existing_enrollment):
    """Should raise 400 when checkpoint progress already exists."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_exists("user123_mission123", existing_enrollment)
    collection.document.return_value.get.return_value = enrollment_doc

    # Mock subcollection - checkpoint already exists
    subcollection = MagicMock()
    checkpoint_doc = FirestoreMocks.document_exists(
        "checkpoint123",
        {
            "checkpoint_id": "checkpoint123",
            "completed": False,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime(2025, 1, 1, 12, 0, 0),
        },
    )
    subcollection.document.return_value.get.return_value = checkpoint_doc
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    checkpoint_progress_data = CheckpointProgressCreate(
        checkpoint_id="checkpoint123",
        completed=False,
    )

    with pytest.raises(HTTPException) as exc:
        service.create_checkpoint_progress("user123", "mission123", checkpoint_progress_data)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in exc.value.detail


def test_get_checkpoint_progress_success():
    """Should retrieve checkpoint progress entry."""
    collection = MagicMock()

    # Mock subcollection
    subcollection = MagicMock()
    checkpoint_doc = FirestoreMocks.document_exists(
        "checkpoint123",
        {
            "checkpoint_id": "checkpoint123",
            "completed": True,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime(2025, 1, 1, 12, 0, 0),
        },
    )
    subcollection.document.return_value.get.return_value = checkpoint_doc
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    checkpoint_progress = service.get_checkpoint_progress("user123", "mission123", "checkpoint123")

    assert checkpoint_progress.checkpoint_id == "checkpoint123"
    assert checkpoint_progress.completed is True


def test_get_checkpoint_progress_not_found():
    """Should raise 404 when checkpoint progress doesn't exist."""
    collection = MagicMock()

    # Mock subcollection - checkpoint not found
    subcollection = MagicMock()
    checkpoint_doc = FirestoreMocks.document_not_found()
    subcollection.document.return_value.get.return_value = checkpoint_doc
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_checkpoint_progress("user123", "mission123", "checkpoint123")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Checkpoint progress not found" in exc.value.detail


def test_get_all_checkpoint_progress_success(existing_enrollment):
    """Should retrieve all checkpoint progress entries for enrollment."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_exists("user123_mission123", existing_enrollment)
    collection.document.return_value.get.return_value = enrollment_doc

    # Mock subcollection with multiple checkpoints
    checkpoint_data = [
        {
            "checkpoint_id": "checkpoint123",
            "completed": True,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime(2025, 1, 1, 12, 0, 0),
        },
        {
            "checkpoint_id": "checkpoint456",
            "completed": False,
            "created_at": datetime(2025, 1, 2, 12, 0, 0),
            "updated_at": datetime(2025, 1, 2, 12, 0, 0),
        },
    ]
    subcollection = FirestoreMocks.collection_with_items(checkpoint_data)
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    checkpoint_progress_list = service.get_all_checkpoint_progress("user123", "mission123")

    assert len(checkpoint_progress_list) == 2
    assert checkpoint_progress_list[0].checkpoint_id == "checkpoint123"
    assert checkpoint_progress_list[0].completed is True
    assert checkpoint_progress_list[1].checkpoint_id == "checkpoint456"
    assert checkpoint_progress_list[1].completed is False


def test_get_all_checkpoint_progress_enrollment_not_found():
    """Should raise 404 when enrollment doesn't exist."""
    collection = MagicMock()
    enrollment_doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = enrollment_doc

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_all_checkpoint_progress("user123", "mission123")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Enrollment not found" in exc.value.detail


def test_update_checkpoint_progress_success():
    """Should update checkpoint progress entry."""
    collection = MagicMock()

    # Mock subcollection
    subcollection = MagicMock()
    doc_ref = subcollection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists(
            "checkpoint123",
            {
                "checkpoint_id": "checkpoint123",
                "completed": False,
                "created_at": datetime(2025, 1, 1, 12, 0, 0),
                "updated_at": datetime(2025, 1, 1, 12, 0, 0),
            },
        ),
        FirestoreMocks.document_exists(
            "checkpoint123",
            {
                "checkpoint_id": "checkpoint123",
                "completed": True,
                "created_at": datetime(2025, 1, 1, 12, 0, 0),
                "updated_at": datetime(2025, 1, 2, 12, 0, 0),
            },
        ),
    ]
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    update_data = CheckpointProgressUpdate(completed=True)
    checkpoint_progress = service.update_checkpoint_progress(
        "user123", "mission123", "checkpoint123", update_data
    )

    assert checkpoint_progress.checkpoint_id == "checkpoint123"
    assert checkpoint_progress.completed is True
    doc_ref.update.assert_called_once()
    # Verify updated_at was set
    update_call_args = doc_ref.update.call_args[0][0]
    assert "updated_at" in update_call_args


def test_update_checkpoint_progress_not_found():
    """Should raise 404 when checkpoint progress doesn't exist."""
    collection = MagicMock()

    # Mock subcollection - checkpoint not found
    subcollection = MagicMock()
    doc_ref = subcollection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    update_data = CheckpointProgressUpdate(completed=True)

    with pytest.raises(HTTPException) as exc:
        service.update_checkpoint_progress("user123", "mission123", "checkpoint123", update_data)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Checkpoint progress not found" in exc.value.detail


def test_delete_checkpoint_progress_success():
    """Should delete checkpoint progress entry."""
    collection = MagicMock()

    # Mock subcollection
    subcollection = MagicMock()
    doc_ref = subcollection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_exists(
        "checkpoint123",
        {
            "checkpoint_id": "checkpoint123",
            "completed": True,
            "created_at": datetime(2025, 1, 1, 12, 0, 0),
            "updated_at": datetime(2025, 1, 1, 12, 0, 0),
        },
    )
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    result = service.delete_checkpoint_progress("user123", "mission123", "checkpoint123")

    assert "deleted successfully" in result["message"]
    doc_ref.delete.assert_called_once()


def test_delete_checkpoint_progress_not_found():
    """Should raise 404 when checkpoint progress doesn't exist."""
    collection = MagicMock()

    # Mock subcollection - checkpoint not found
    subcollection = MagicMock()
    doc_ref = subcollection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()
    collection.document.return_value.collection.return_value = subcollection

    db = MagicMock()
    db.collection.return_value = collection
    service = EnrollmentService(db)

    with pytest.raises(HTTPException) as exc:
        service.delete_checkpoint_progress("user123", "mission123", "checkpoint123")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Checkpoint progress not found" in exc.value.detail
