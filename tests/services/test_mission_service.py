"""Unit tests for MissionService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.mission import MissionCreate, MissionUpdate
from app.services.mission_service import MissionService
from tests.mocks.firestore import FirestoreMocks


@pytest.fixture
def valid_mission_create_data():
    """Test data for creating a mission."""
    return MissionCreate(
        title="Learn Python Basics",
        short_description="An introductory course on Python",
        description="A comprehensive guide to Python fundamentals",
        creator_id="user123",
        level="Beginner",
        topics_to_cover=["Variables", "Functions", "Data Types"],
        learning_goal="Master Python fundamentals for programming",
        byte_size_checkpoints=[
            "Introduction",
            "Variables and Data Types",
            "Functions",
            "Conclusion",
        ],
        is_public=True,
    )


@pytest.fixture
def existing_mission():
    """Existing mission dict as returned from Firestore."""
    return {
        "id": "mission123",
        "title": "Learn Python Basics",
        "short_description": "An introductory course on Python",
        "description": "A comprehensive guide to Python fundamentals",
        "creator_id": "user123",
        "level": "Beginner",
        "topics_to_cover": ["Variables", "Functions", "Data Types"],
        "learning_goal": "Master Python fundamentals for programming",
        "byte_size_checkpoints": [
            "Introduction",
            "Variables and Data Types",
            "Functions",
            "Conclusion",
        ],
        "skills": [],
        "is_public": True,
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
        "updated_at": datetime(2025, 1, 1, 12, 0, 0),
    }


def test_create_mission_success(valid_mission_create_data):
    """Should create new mission successfully."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    mission = service.create_mission(valid_mission_create_data)

    assert mission.title == valid_mission_create_data.title
    assert mission.id == "auto_generated_id"
    assert mission.creator_id == valid_mission_create_data.creator_id
    collection.document().set.assert_called_once()


def test_create_mission_sets_timestamps(valid_mission_create_data):
    """Should auto-set created_at and updated_at."""
    collection = FirestoreMocks.collection_empty()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    mission = service.create_mission(valid_mission_create_data)

    time_diff = abs((mission.created_at - mission.updated_at).total_seconds())
    assert time_diff < 1


def test_get_mission_found_returns_mission(existing_mission):
    """Should return mission when document exists."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_exists("mission123", existing_mission)
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    mission = service.get_mission("mission123")

    assert mission.id == existing_mission["id"]
    assert mission.title == existing_mission["title"]


def test_get_mission_not_found_raises_404():
    """Should raise 404 when mission doesn't exist."""
    collection = FirestoreMocks.collection_empty()
    doc = FirestoreMocks.document_not_found()
    collection.document.return_value.get.return_value = doc
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_mission("missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_update_mission_success(existing_mission):
    """Should update mission successfully."""
    collection = FirestoreMocks.collection_empty()
    doc_ref = collection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists("mission123", existing_mission),
        FirestoreMocks.document_exists(
            "mission123", {**existing_mission, "title": "Updated Title"}
        ),
    ]
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    update_data = MissionUpdate(title="Updated Title")
    mission = service.update_mission("mission123", update_data)

    assert mission.title == "Updated Title"
    doc_ref.update.assert_called_once()


def test_update_mission_not_found_raises_404():
    """Should raise 404 when updating non-existent mission."""
    collection = FirestoreMocks.collection_empty()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_mission("missing", MissionUpdate(title="New"))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_delete_mission_success(existing_mission):
    """Should delete mission and its checkpoints."""
    collection = FirestoreMocks.collection_empty()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_exists("mission123", existing_mission)

    # Mock checkpoints subcollection
    checkpoint_docs = []
    doc_ref.collection.return_value.get.return_value = checkpoint_docs

    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    result = service.delete_mission("mission123")

    assert "deleted successfully" in result["message"]
    doc_ref.delete.assert_called_once()


def test_delete_mission_not_found_raises_404():
    """Should raise 404 when deleting non-existent mission."""
    collection = FirestoreMocks.collection_empty()
    doc_ref = collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    with pytest.raises(HTTPException) as exc:
        service.delete_mission("missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_missions_by_creator(existing_mission):
    """Should return all missions by creator."""
    missions_data = [
        existing_mission,
        {**existing_mission, "id": "mission456", "title": "Another Mission"},
    ]
    collection = FirestoreMocks.collection_with_items(missions_data)
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    missions = service.get_missions_by_creator("user123")

    assert len(missions) == 2
    assert missions[0].creator_id == "user123"
    collection.where.assert_called()


def test_get_public_missions(existing_mission):
    """Should return all public missions."""
    missions_data = [existing_mission]
    collection = FirestoreMocks.collection_with_items(missions_data)
    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    missions = service.get_public_missions()

    assert len(missions) == 1
    assert missions[0].is_public is True


def test_get_missions_by_creator_and_visibility():
    """Should return missions filtered by creator and visibility."""
    missions_data = [
        {
            "id": "mission123",
            "title": "Public Mission",
            "short_description": "Public Mission",
            "description": "Test",
            "creator_id": "user123",
            "level": "Beginner",
            "topics_to_cover": ["Python Basics"],
            "learning_goal": "Learn Python programming",
            "byte_size_checkpoints": ["Introduction", "Variables", "Functions", "Conclusion"],
            "skills": [],
            "is_public": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    ]
    collection = MagicMock()

    # Mock chained where calls
    mock_doc = MagicMock(to_dict=MagicMock(return_value=missions_data[0]))
    collection.where.return_value.where.return_value.limit.return_value.get.return_value = [
        mock_doc
    ]

    db = FirestoreMocks.mock_db_with_collection(collection)
    service = MissionService(db)

    missions = service.get_missions_by_creator_and_visibility("user123", True)

    assert len(missions) == 1
    assert missions[0].creator_id == "user123"
    assert missions[0].is_public is True


def test_create_mission_with_enrollment_success(valid_mission_create_data):
    """Should create mission and auto-enroll creator."""
    from app.services.enrollment_service import EnrollmentService

    # Mock mission collection
    mission_collection = FirestoreMocks.collection_empty()
    mission_doc_ref = mission_collection.document.return_value
    mission_doc_ref.id = "mission123"

    # Mock enrollment collection
    enrollment_collection = MagicMock()
    enrollment_doc_ref = enrollment_collection.document.return_value
    enrollment_doc_ref.get.return_value = MagicMock(exists=False)  # Enrollment doesn't exist yet

    # Mock users collection
    users_collection = MagicMock()
    users_collection.document.return_value.get.return_value = MagicMock(exists=True)

    # Mock missions collection for enrollment service verification
    missions_collection = MagicMock()
    missions_collection.document.return_value.get.return_value = MagicMock(exists=True)

    # Mock database
    db = MagicMock()
    collection_map = {
        "missions": missions_collection,
        "enrollments": enrollment_collection,
        "users": users_collection,
    }

    def mock_collection(name):
        if name == "missions" and not hasattr(mock_collection, "_first_call"):
            mock_collection._first_call = True
            return mission_collection
        return collection_map.get(name, mission_collection)

    db.collection = mock_collection

    service = MissionService(db)

    mission, enrollment = service.create_mission_with_enrollment(
        valid_mission_create_data, "user123"
    )

    assert mission.title == valid_mission_create_data.title
    assert enrollment.user_id == "user123"
    assert enrollment.mission_id == mission.id


def test_create_mission_with_enrollment_rolls_back_on_failure(valid_mission_create_data):
    """Should delete mission if enrollment fails."""
    # Mock mission collection
    mission_collection = FirestoreMocks.collection_empty()
    mission_doc_ref = mission_collection.document.return_value
    mission_doc_ref.id = "mission123"

    # Mock enrollment collection
    enrollment_collection = MagicMock()

    # Mock users collection - user doesn't exist
    users_collection = MagicMock()
    users_collection.document.return_value.get.return_value = MagicMock(exists=False)

    # Mock database
    db = MagicMock()
    collection_map = {
        "missions": mission_collection,
        "enrollments": enrollment_collection,
        "users": users_collection,
    }

    def mock_collection(name):
        if name == "missions" and not hasattr(mock_collection, "_first_call"):
            mock_collection._first_call = True
            return mission_collection
        return collection_map.get(name, mission_collection)

    db.collection = mock_collection

    service = MissionService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_mission_with_enrollment(valid_mission_create_data, "nonexistent_user")

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_create_mission_with_enrollment_returns_both_objects(valid_mission_create_data):
    """Should return tuple with mission and enrollment."""
    # Mock mission collection
    mission_collection = FirestoreMocks.collection_empty()
    mission_doc_ref = mission_collection.document.return_value
    mission_doc_ref.id = "mission123"

    # Mock enrollment collection
    enrollment_collection = MagicMock()
    enrollment_collection.document.return_value.get.return_value = MagicMock(exists=False)

    # Mock users collection
    users_collection = MagicMock()
    users_collection.document.return_value.get.return_value = MagicMock(exists=True)

    # Mock missions collection for enrollment verification
    missions_collection = MagicMock()
    missions_collection.document.return_value.get.return_value = MagicMock(exists=True)

    # Mock database
    db = MagicMock()
    collection_map = {
        "missions": missions_collection,
        "enrollments": enrollment_collection,
        "users": users_collection,
    }

    def mock_collection(name):
        if name == "missions" and not hasattr(mock_collection, "_first_call"):
            mock_collection._first_call = True
            return mission_collection
        return collection_map.get(name, mission_collection)

    db.collection = mock_collection

    service = MissionService(db)

    result = service.create_mission_with_enrollment(valid_mission_create_data, "user123")

    assert isinstance(result, tuple)
    assert len(result) == 2
