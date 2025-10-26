"""Unit tests for SessionLogService."""

from datetime import datetime

import pytest
from fastapi import HTTPException, status

from app.models.session_log import SessionLogCreate, SessionLogUpdate
from app.services.session_log_service import SessionLogService
from tests.mocks.firestore import FirestoreMocks


# Test data fixtures (visible in test file per unit testing guide)
@pytest.fixture
def valid_session_create_data():
    """Valid session data for create operations."""
    return SessionLogCreate(user_id="user123")


@pytest.fixture
def existing_session():
    """Existing session dict as returned from Firestore."""
    return {
        "id": "session123",
        "user_id": "user123",
        "status": "active",
        "mission_id": None,
        "created_at": datetime(2025, 10, 25, 10, 0, 0),
        "updated_at": datetime(2025, 10, 25, 10, 0, 0),
        "completed_at": None,
    }


@pytest.fixture
def completed_session():
    """Completed session dict."""
    return {
        "id": "session456",
        "user_id": "user123",
        "status": "completed",
        "mission_id": "mission123",
        "created_at": datetime(2025, 10, 25, 10, 0, 0),
        "updated_at": datetime(2025, 10, 25, 10, 30, 0),
        "completed_at": datetime(2025, 10, 25, 10, 30, 0),
    }


# Create session tests
def test_create_session_success(valid_session_create_data):
    """Should create new session with auto-generated ID."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.create_session(valid_session_create_data)

    assert session.user_id == valid_session_create_data.user_id
    assert session.id == "auto_generated_id"
    collection.document().set.assert_called_once()


def test_create_session_sets_active_status(valid_session_create_data):
    """Should set status to 'active' by default."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.create_session(valid_session_create_data)

    assert session.status == "active"


def test_create_session_sets_null_mission_id(valid_session_create_data):
    """Should set mission_id to None initially."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.create_session(valid_session_create_data)

    assert session.mission_id is None


def test_create_session_sets_timestamps(valid_session_create_data):
    """Should auto-set created_at and updated_at."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.create_session(valid_session_create_data)

    time_diff = abs((session.created_at - session.updated_at).total_seconds())
    assert time_diff < 1


# Get session tests
def test_get_session_found_returns_session(existing_session):
    """Should return session when document exists."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session123", existing_session)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.get_session("session123")

    assert session.id == existing_session["id"]
    assert session.user_id == existing_session["user_id"]


def test_get_session_not_found_raises_404():
    """Should raise 404 when session doesn't exist."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_session("missing_session")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


# Update session tests
def test_update_session_changes_status(existing_session):
    """Should update session status."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated_session = existing_session.copy()
    updated_session["status"] = "completed"
    doc_after = FirestoreMocks.document_exists("session123", updated_session)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.update_session("session123", SessionLogUpdate(status="completed"))

    assert session.status == "completed"


def test_update_session_calls_firestore_update(existing_session):
    """Should call Firestore update method."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session123", existing_session)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    service.update_session("session123", SessionLogUpdate(status="completed"))

    collection.document.return_value.update.assert_called_once()


def test_update_session_not_found_raises_404():
    """Should raise 404 when updating non-existent session."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_session("missing", SessionLogUpdate(status="completed"))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


# Mark session completed tests
def test_mark_completed_sets_status(existing_session):
    """Should set status to 'completed'."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated = existing_session.copy()
    updated["status"] = "completed"
    doc_after = FirestoreMocks.document_exists("session123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.mark_session_completed("session123")

    assert session.status == "completed"


def test_mark_completed_with_mission_id(existing_session):
    """Should set mission_id when provided."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated = existing_session.copy()
    updated["mission_id"] = "mission123"
    updated["status"] = "completed"
    doc_after = FirestoreMocks.document_exists("session123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.mark_session_completed("session123", mission_id="mission123")

    assert session.mission_id == "mission123"


def test_mark_completed_sets_completed_at(existing_session):
    """Should set completed_at timestamp."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated = existing_session.copy()
    updated["completed_at"] = datetime.now()
    doc_after = FirestoreMocks.document_exists("session123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.mark_session_completed("session123")

    assert session.completed_at is not None


# Mark session error tests
def test_mark_error_sets_error_status(existing_session):
    """Should set status to 'error'."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated = existing_session.copy()
    updated["status"] = "error"
    doc_after = FirestoreMocks.document_exists("session123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.mark_session_error("session123")

    assert session.status == "error"


# Mark session abandoned tests
def test_mark_abandoned_sets_abandoned_status(existing_session):
    """Should set status to 'abandoned'."""
    collection = FirestoreMocks.collection_empty()
    doc_before = FirestoreMocks.document_exists("session123", existing_session)
    updated = existing_session.copy()
    updated["status"] = "abandoned"
    doc_after = FirestoreMocks.document_exists("session123", updated)

    collection.document.return_value.get.side_effect = [doc_before, doc_after]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    session = service.mark_session_abandoned("session123")

    assert session.status == "abandoned"


# Get user sessions tests
def test_get_user_sessions_returns_list(existing_session, completed_session):
    """Should return list of user sessions."""
    from unittest.mock import MagicMock

    collection = FirestoreMocks.collection_empty()
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query

    doc1 = MagicMock()
    doc1.to_dict.return_value = existing_session
    doc2 = MagicMock()
    doc2.to_dict.return_value = completed_session
    mock_query.get.return_value = [doc1, doc2]

    collection.where.return_value = mock_query
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    sessions = service.get_user_sessions("user123")

    assert len(sessions) == 2


def test_get_user_sessions_respects_limit():
    """Should respect the limit parameter."""
    from unittest.mock import MagicMock

    collection = FirestoreMocks.collection_empty()
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.get.return_value = []

    collection.where.return_value = mock_query
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    service.get_user_sessions("user123", limit=10)

    mock_query.limit.assert_called_with(10)


# Delete session tests
def test_delete_session_success(existing_session):
    """Should delete session successfully."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("session123", existing_session)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    result = service.delete_session("session123")

    assert "deleted successfully" in result["message"]
    collection.document.return_value.delete.assert_called_once()


def test_delete_session_not_found_raises_404():
    """Should raise 404 when deleting non-existent session."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = SessionLogService(db)

    with pytest.raises(HTTPException) as exc:
        service.delete_session("missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
