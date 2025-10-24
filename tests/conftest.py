"""Shared pytest fixtures for all tests."""

import sys
from datetime import datetime
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def valid_user_data():
    """Valid user data for create operations."""
    return {
        "email": "test@example.com",
        "firebase_uid": "firebase_uid_123",
        "name": "Test User",
    }


@pytest.fixture
def existing_user_dict():
    """Existing user dict as returned from Firestore."""
    return {
        "id": "user123",
        "firebase_uid": "firebase_uid_123",
        "email": "existing@example.com",
        "name": "Existing User",
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
        "updated_at": datetime(2025, 1, 1, 12, 0, 0),
    }
