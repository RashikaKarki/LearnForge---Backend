"""Unit tests for auth dependencies"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from app.dependencies.auth import get_current_user, get_current_user_optional
from app.models.user import User


@pytest.fixture
def mock_user():
    """Test user data"""
    return User(
        id="user123",
        firebase_uid="firebase123",
        email="test@example.com",
        name="Test User",
        picture="http://example.com/pic.jpg",
    )


@pytest.fixture
def mock_request_with_user(mock_user):
    """Request with authenticated user"""
    request = MagicMock(spec=Request)
    request.state.current_user = mock_user
    return request


@pytest.fixture
def mock_request_without_user():
    """Request without authenticated user"""
    request = MagicMock(spec=Request)
    request.state = MagicMock()
    del request.state.current_user
    return request


def test_get_current_user_success(mock_request_with_user, mock_user):
    """Should return user when authenticated"""
    user = get_current_user(mock_request_with_user)

    assert user.id == mock_user.id
    assert user.email == mock_user.email


def test_get_current_user_not_authenticated_raises_401(mock_request_without_user):
    """Should raise 401 when user not authenticated"""
    with pytest.raises(HTTPException) as exc:
        get_current_user(mock_request_without_user)

    assert exc.value.status_code == 401
    assert "Not authenticated" in exc.value.detail


def test_get_current_user_optional_returns_user(mock_request_with_user, mock_user):
    """Should return user when authenticated"""
    user = get_current_user_optional(mock_request_with_user)

    assert user.id == mock_user.id
    assert user.email == mock_user.email


def test_get_current_user_optional_returns_none(mock_request_without_user):
    """Should return None when not authenticated"""
    user = get_current_user_optional(mock_request_without_user)

    assert user is None
