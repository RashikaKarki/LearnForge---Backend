"""Unit tests for UserService."""

import pytest
from fastapi import HTTPException, status

from app.models.user import User
from app.services.user_service import UserService
from tests.mocks.firestore import FirestoreMocks


def test_create_user_success(valid_user_data):
    """Should create new user when email doesn't exist."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.create_user(valid_user_data)
    
    assert user.email == valid_user_data["email"]
    assert user.id == "auto_generated_id"
    collection.document().set.assert_called_once()


def test_create_user_duplicate_email_raises_400(valid_user_data, existing_user_dict):
    """Should raise 400 when email already exists."""
    collection = FirestoreMocks.collection_with_user(existing_user_dict)
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    with pytest.raises(HTTPException) as exc:
        service.create_user({"email": existing_user_dict["email"], "name": "New", "firebase_uid": "new"})
    
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_user_sets_timestamps(valid_user_data):
    """Should auto-set created_at and updated_at."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.create_user(valid_user_data)
    
    time_diff = abs((user.created_at - user.updated_at).total_seconds())
    assert time_diff < 1  # Should be set within 1 second of each other


def test_get_user_found_returns_user(existing_user_dict):
    """Should return user when document exists."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("user123", existing_user_dict)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.get_user("user123")
    
    assert user.id == existing_user_dict["id"]
    assert user.email == existing_user_dict["email"]


def test_get_user_not_found_raises_404():
    """Should raise 404 when user doesn't exist."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    with pytest.raises(HTTPException) as exc:
        service.get_user("missing")
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_by_email_found_returns_user(existing_user_dict):
    """Should return user when email exists."""
    collection = FirestoreMocks.collection_with_user(existing_user_dict)
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.get_user_by_email(existing_user_dict["email"])
    
    assert user.email == existing_user_dict["email"]
    collection.where.assert_called_once_with("email", "==", existing_user_dict["email"])


def test_get_user_by_email_not_found_raises_404():
    """Should raise 404 when email not found."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    with pytest.raises(HTTPException) as exc:
        service.get_user_by_email("missing@example.com")
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_by_email_limits_to_one():
    """Should limit query to 1 result."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    try:
        service.get_user_by_email("test@example.com")
    except HTTPException:
        pass
    
    collection.where.return_value.limit.assert_called_once_with(1)


def test_get_or_create_user_returns_existing(existing_user_dict):
    """Should return existing user without creating."""
    collection = FirestoreMocks.collection_with_user(existing_user_dict)
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.get_or_create_user({"email": existing_user_dict["email"], "name": "Other", "firebase_uid": "other"})
    
    assert user.id == existing_user_dict["id"]
    assert not collection.document().set.called


def test_get_or_create_user_creates_when_missing(valid_user_data):
    """Should create user when email not found."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    user = service.get_or_create_user(valid_user_data)
    
    assert user.email == valid_user_data["email"]
    assert user.id == "auto_generated_id"
    collection.document().set.assert_called_once()


def test_get_or_create_user_propagates_non_404_errors():
    """Should propagate non-404 exceptions."""
    collection = FirestoreMocks.collection_empty()
    collection.where.side_effect = HTTPException(status_code=500, detail="DB error")
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = UserService(db)
    
    with pytest.raises(HTTPException) as exc:
        service.get_or_create_user({"email": "test@example.com"})
    
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
