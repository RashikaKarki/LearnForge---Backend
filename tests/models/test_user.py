"""Unit tests for User model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.user import User


def test_user_model_valid_creation():
    """Should create user with all required fields."""
    user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
    )
    
    assert user.id == "user123"
    assert user.firebase_uid == "firebase_uid_123"
    assert user.name == "Test User"
    assert user.email == "test@example.com"


def test_user_model_optional_picture_defaults_to_none():
    """Should set picture to None when not provided."""
    user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
    )
    
    assert user.picture is None


def test_user_model_timestamps_auto_generated():
    """Should auto-generate created_at and updated_at timestamps."""
    user = User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
    )
    
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


@pytest.mark.parametrize("email", [
    "not-an-email",
    "missing-at-sign.com",
    "@no-local-part.com",
    "no-domain@",
    "",
])
def test_user_model_invalid_email_raises(email):
    """Should raise ValidationError for invalid email formats."""
    with pytest.raises(ValidationError):
        User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email=email,
        )


@pytest.mark.parametrize("picture", [
    "not-a-url",
    "missing-protocol.com",
])
def test_user_model_invalid_picture_raises(picture):
    """Should raise ValidationError for invalid picture URLs."""
    with pytest.raises(ValidationError):
        User(
            id="user123",
            firebase_uid="firebase_uid_123",
            name="Test User",
            email="test@example.com",
            picture=picture,
        )


@pytest.mark.parametrize("missing_field,data", [
    ("id", {"firebase_uid": "uid", "name": "Name", "email": "test@example.com"}),
    ("firebase_uid", {"id": "id123", "name": "Name", "email": "test@example.com"}),
    ("name", {"id": "id123", "firebase_uid": "uid", "email": "test@example.com"}),
    ("email", {"id": "id123", "firebase_uid": "uid", "name": "Name"}),
])
def test_user_model_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing."""
    with pytest.raises(ValidationError):
        User(**data)
