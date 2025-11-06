"""Unit tests for EnrollmentSessionLogService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.enrollment_session_log import EnrollmentSessionLogCreate, EnrollmentSessionLogUpdate
from app.services.enrollment_session_log_service import EnrollmentSessionLogService
from tests.mocks.firestore import FirestoreMocks


# Test data fixtures (visible in test file per unit testing guide)
@pytest.fixture
def valid_session_log_create_data():
    """Valid enrollment session log data for create operations."""
    return EnrollmentSessionLogCreate(
        enrollment_id="user123_mission123",
        user_id="user123",
        mission_id="mission123",
    )


@pytest.fixture
def existing_session_log():
    """Existing enrollment session log dict as returned from Firestore."""
    return {
        "id": "session_log123",
        "enrollment_id": "user123_mission123",
        "user_id": "user123",
        "mission_id": "mission123",
        "status": "created",
        "created_at": datetime(2025, 10, 25, 10, 0, 0),
        "updated_at": datetime(2025, 10, 25, 10, 0, 0),
        "started_at": None,
        "completed_at": None,
    }


@pytest.fixture
def started_session_log():
    """Started enrollment session log dict."""
    return {
        "id": "session_log123",
        "enrollment_id": "user123_mission123",
        "user_id": "user123",
        "mission_id": "mission123",
        "status": "started",
        "created_at": datetime(2025, 10, 25, 10, 0, 0),
        "updated_at": datetime(2025, 10, 25, 10, 15, 0),
        "started_at": datetime(2025, 10, 25, 10, 15, 0),
        "completed_at": None,
    }


@pytest.fixture
def completed_session_log():
    """Completed enrollment session log dict."""
    return {
        "id": "session_log123",
        "enrollment_id": "user123_mission123",
        "user_id": "user123",
        "mission_id": "mission123",
        "status": "completed",
        "created_at": datetime(2025, 10, 25, 10, 0, 0),
        "updated_at": datetime(2025, 10, 25, 10, 30, 0),
        "started_at": datetime(2025, 10, 25, 10, 15, 0),
        "completed_at": datetime(2025, 10, 25, 10, 30, 0),
    }


# Create session log tests
def test_create_session_log_success(valid_session_log_create_data):
    """Should create new enrollment session log with auto-generated ID."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.create_session_log(valid_session_log_create_data)

    assert session_log.enrollment_id == valid_session_log_create_data.enrollment_id
    assert session_log.user_id == valid_session_log_create_data.user_id
    assert session_log.mission_id == valid_session_log_create_data.mission_id
    assert session_log.id == "auto_generated_id"
    collection.document().set.assert_called_once()


def test_create_session_log_sets_created_status(valid_session_log_create_data):
    """Should set status to 'created' by default."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.create_session_log(valid_session_log_create_data)

    assert session_log.status == "created"


def test_create_session_log_sets_null_timestamps(valid_session_log_create_data):
    """Should set started_at and completed_at to None initially."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.create_session_log(valid_session_log_create_data)

    assert session_log.started_at is None
    assert session_log.completed_at is None


def test_create_session_log_sets_timestamps(valid_session_log_create_data):
    """Should auto-set created_at and updated_at."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.create_session_log(valid_session_log_create_data)

    time_diff = abs((session_log.created_at - session_log.updated_at).total_seconds())
    assert time_diff < 1


# Get session log tests
def test_get_session_log_found_returns_session_log(existing_session_log):
    """Should return enrollment session log when document exists."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session_log123", existing_session_log)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.get_session_log("session_log123")

    assert session_log.id == existing_session_log["id"]
    assert session_log.enrollment_id == existing_session_log["enrollment_id"]
    assert session_log.user_id == existing_session_log["user_id"]


def test_get_session_log_not_found_raises_404():
    """Should raise 404 when enrollment session log doesn't exist."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_session_log("missing_session_log")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc.value.detail.lower()


# Get session log by enrollment_id tests
def test_get_session_log_by_user_and_enrollment_and_mission_found_returns_session_log(
    existing_session_log,
):
    """Should return enrollment session log when found by user_id, enrollment_id, and mission_id."""
    collection = FirestoreMocks.collection_empty()
    mock_query = MagicMock()
    mock_query.limit.return_value = mock_query

    doc = MagicMock()
    doc.to_dict.return_value = existing_session_log
    mock_query.get.return_value = [doc]

    mock_query_1 = MagicMock()
    mock_query_2 = MagicMock()
    mock_query_3 = mock_query
    mock_query_1.where.return_value = mock_query_2
    mock_query_2.where.return_value = mock_query_3
    mock_query_3.limit.return_value = mock_query_3
    mock_query_3.get.return_value = [doc]
    collection.where.return_value = mock_query_1
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.get_session_log_by_user_and_enrollment_and_mission(
        "user123", "user123_mission123", "mission123"
    )

    assert session_log is not None
    assert session_log.enrollment_id == "user123_mission123"
    assert session_log.user_id == "user123"
    assert session_log.mission_id == "mission123"
    assert session_log.id == existing_session_log["id"]


def test_get_session_log_by_user_and_enrollment_and_mission_not_found_returns_none():
    """Should return None when enrollment session log doesn't exist for user_id, enrollment_id, and mission_id."""
    collection = FirestoreMocks.collection_empty()
    mock_query = MagicMock()
    mock_query.limit.return_value = mock_query
    mock_query.get.return_value = []

    mock_query_1 = MagicMock()
    mock_query_2 = MagicMock()
    mock_query_3 = mock_query
    mock_query_1.where.return_value = mock_query_2
    mock_query_2.where.return_value = mock_query_3
    mock_query_3.limit.return_value = mock_query_3
    mock_query_3.get.return_value = []
    collection.where.return_value = mock_query_1
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.get_session_log_by_user_and_enrollment_and_mission(
        "user123", "user123_mission123", "mission123"
    )

    assert session_log is None


# Update session log tests
def test_update_session_log_changes_status(existing_session_log):
    """Should update enrollment session log status."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", existing_session_log)
    updated_session_log = existing_session_log.copy()
    updated_session_log["status"] = "started"
    doc_after = FirestoreMocks.document_exists("session_log123", updated_session_log)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.update_session_log(
        "session_log123", EnrollmentSessionLogUpdate(status="started")
    )

    assert session_log.status == "started"


def test_update_session_log_calls_firestore_update(existing_session_log):
    """Should call Firestore update method."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session_log123", existing_session_log)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    service.update_session_log("session_log123", EnrollmentSessionLogUpdate(status="started"))

    collection.document.return_value.update.assert_called_once()


def test_update_session_log_updates_updated_at(existing_session_log):
    """Should update updated_at timestamp when updating."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", existing_session_log)
    updated_session_log = existing_session_log.copy()
    updated_session_log["updated_at"] = datetime(2025, 10, 25, 10, 30, 0)
    doc_after = FirestoreMocks.document_exists("session_log123", updated_session_log)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.update_session_log(
        "session_log123", EnrollmentSessionLogUpdate(status="started")
    )

    assert session_log.updated_at != existing_session_log["updated_at"]


def test_update_session_log_not_found_raises_404():
    """Should raise 404 when updating non-existent enrollment session log."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_session_log("missing", EnrollmentSessionLogUpdate(status="started"))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_update_session_log_with_empty_update_data(existing_session_log):
    """Should handle empty update data gracefully."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session_log123", existing_session_log)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.update_session_log("session_log123", EnrollmentSessionLogUpdate())

    assert session_log.id == existing_session_log["id"]
    collection.document.return_value.update.assert_not_called()


# Mark session started tests
def test_mark_session_started_sets_status(existing_session_log):
    """Should set status to 'started'."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", existing_session_log)
    updated = existing_session_log.copy()
    updated["status"] = "started"
    updated["started_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.mark_session_started("session_log123")

    assert session_log.status == "started"


def test_mark_session_started_sets_started_at(existing_session_log):
    """Should set started_at timestamp."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", existing_session_log)
    updated = existing_session_log.copy()
    updated["status"] = "started"
    updated["started_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.mark_session_started("session_log123")

    assert session_log.started_at is not None


def test_mark_session_started_calls_update(existing_session_log):
    """Should call update_session_log internally."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", existing_session_log)
    updated = existing_session_log.copy()
    updated["status"] = "started"
    updated["started_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    service.mark_session_started("session_log123")

    collection.document.return_value.update.assert_called_once()


# Mark session completed tests
def test_mark_session_completed_sets_status(started_session_log):
    """Should set status to 'completed'."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", started_session_log)
    updated = started_session_log.copy()
    updated["status"] = "completed"
    updated["completed_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.mark_session_completed("session_log123")

    assert session_log.status == "completed"


def test_mark_session_completed_sets_completed_at(started_session_log):
    """Should set completed_at timestamp."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", started_session_log)
    updated = started_session_log.copy()
    updated["status"] = "completed"
    updated["completed_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    session_log = service.mark_session_completed("session_log123")

    assert session_log.completed_at is not None


def test_mark_session_completed_calls_update(started_session_log):
    """Should call update_session_log internally."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session_log123", started_session_log)
    updated = started_session_log.copy()
    updated["status"] = "completed"
    updated["completed_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session_log123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    service.mark_session_completed("session_log123")

    collection.document.return_value.update.assert_called_once()


def test_mark_session_completed_not_found_raises_404():
    """Should raise 404 when marking non-existent session as completed."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.mark_session_completed("missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_mark_session_started_not_found_raises_404():
    """Should raise 404 when marking non-existent session as started."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.mark_session_started("missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_session_log_by_user_and_enrollment_and_mission_uses_correct_filter(
    existing_session_log,
):
    """Should use correct FieldFilter when querying by user_id, mission_id, and enrollment_id."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    collection = FirestoreMocks.collection_empty()
    mock_query = MagicMock()
    mock_query.limit.return_value = mock_query

    doc = MagicMock()
    doc.to_dict.return_value = existing_session_log
    mock_query.get.return_value = [doc]

    mock_query_1 = MagicMock()
    mock_query_2 = MagicMock()
    mock_query_3 = mock_query
    mock_query_1.where.return_value = mock_query_2
    mock_query_2.where.return_value = mock_query_3
    mock_query_3.limit.return_value = mock_query_3
    mock_query_3.get.return_value = [doc]
    collection.where.return_value = mock_query_1
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = EnrollmentSessionLogService(db)

    service.get_session_log_by_user_and_enrollment_and_mission(
        "user123", "user123_mission123", "mission123"
    )

    assert collection.where.call_count == 1
    assert mock_query_1.where.call_count == 1
    assert mock_query_2.where.call_count == 1

    first_call = collection.where.call_args.kwargs["filter"]
    second_call = mock_query_1.where.call_args.kwargs["filter"]
    third_call = mock_query_2.where.call_args.kwargs["filter"]

    assert first_call.field_path == "user_id"
    assert first_call.value == "user123"
    assert second_call.field_path == "enrollment_id"
    assert second_call.value == "user123_mission123"
    assert third_call.field_path == "mission_id"
    assert third_call.value == "mission123"
