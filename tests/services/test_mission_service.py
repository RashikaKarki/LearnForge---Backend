"""Comprehensive tests for MissionService.

Tests mission CRUD operations, update propagation, and edge cases.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.mission import MissionCreate, MissionUpdate
from app.services.mission_service import MissionService
from tests.mocks.firestore import FirestoreMocks

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_db():
    """Generic database mock."""
    return MagicMock()


@pytest.fixture
def mock_user_service():
    """Mock UserService."""
    return MagicMock()


@pytest.fixture
def valid_mission_create():
    """Valid mission creation data."""
    return MissionCreate(
        title="Test Mission",
        short_description="A test mission",
        description="A longer description of the test mission",
        level="Beginner",
        topics_to_cover=["Python Basics", "API Design", "Testing"],
        learning_goal="Learn to build REST APIs with FastAPI",
        byte_size_checkpoints=["Setup", "First Endpoint", "Database", "Testing"],
        skills=["Python", "FastAPI"],
        creator_id="creator123",
        is_public=True,
    )


@pytest.fixture
def existing_mission_data():
    """Existing mission data."""
    return {
        "id": "mission123",
        "title": "Existing Mission",
        "short_description": "Short desc",
        "description": "Long description",
        "level": "Intermediate",
        "topics_to_cover": ["Python", "Testing"],
        "learning_goal": "Master testing in Python",
        "learning_style": ["examples", "step-by-step"],
        "byte_size_checkpoints": ["Intro", "Unit Tests", "Integration", "Advanced"],
        "skills": ["Python"],
        "creator_id": "creator123",
        "is_public": True,
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 1),
    }


@pytest.fixture
def enrollment_data():
    """Enrollment data for propagation tests."""
    return {
        "id": "user123_mission123",
        "user_id": "user123",
        "mission_id": "mission123",
        "progress": 50.0,
        "enrolled_at": datetime(2025, 1, 1),
        "last_accessed_at": datetime(2025, 1, 5),
        "completed": False,
        "created_at": datetime(2025, 1, 1),
        "updated_at": datetime(2025, 1, 5),
    }


# ============================================================================
# CREATE MISSION TESTS
# ============================================================================


class TestCreateMission:
    """Test mission creation."""

    def test_create_mission_success(self, mock_db, mock_user_service, valid_mission_create):
        """Successfully create a mission."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        doc_ref.id = "auto_generated_id"
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        with patch("app.services.mission_service.datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2025, 1, 15)

            mission = service.create_mission(valid_mission_create)

            assert mission.title == "Test Mission"
            assert mission.id == "auto_generated_id"
            assert mission.creator_id == "creator123"
            assert len(mission.skills) == 2
            doc_ref.set.assert_called_once()

    def test_create_mission_without_optional_fields(self, mock_db, mock_user_service):
        """Create mission with minimal required fields."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        doc_ref.id = "mission_id"
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        minimal_mission = MissionCreate(
            title="Minimal Mission",
            short_description="Short desc",
            description="Minimal description",
            level="Beginner",
            topics_to_cover=["Basics"],
            learning_goal="Learn basics",
            byte_size_checkpoints=["Step 1", "Step 2", "Step 3", "Step 4"],
            creator_id="creator123",
        )

        mission = service.create_mission(minimal_mission)

        assert mission.title == "Minimal Mission"
        assert mission.id == "mission_id"


# ============================================================================
# GET MISSION TESTS
# ============================================================================


class TestGetMission:
    """Test retrieving missions."""

    def test_get_mission_success(self, mock_db, mock_user_service, existing_mission_data):
        """Successfully retrieve a mission."""
        missions_collection = MagicMock()
        doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        missions_collection.document.return_value.get.return_value = doc

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        mission = service.get_mission("mission123")

        assert mission.id == "mission123"
        assert mission.title == "Existing Mission"

    def test_get_mission_not_found_raises_404(self, mock_db, mock_user_service):
        """Get non-existent mission raises 404."""
        missions_collection = MagicMock()
        doc = FirestoreMocks.document_not_found()
        missions_collection.document.return_value.get.return_value = doc

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        with pytest.raises(HTTPException) as exc:
            service.get_mission("nonexistent")

        assert exc.value.status_code == 404
        assert "not found" in exc.value.detail


# ============================================================================
# UPDATE MISSION TESTS
# ============================================================================


class TestUpdateMission:
    """Test mission updates."""

    def test_update_mission_success_without_propagation(
        self, mock_db, mock_user_service, existing_mission_data
    ):
        """Successfully update mission without triggering propagation."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        # Update non-metadata field (won't trigger propagation)
        update_data = MissionUpdate(is_public=False)

        with patch("app.services.mission_service.datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2025, 1, 20)

            mission = service.update_mission("mission123", update_data)

            assert mission.id == "mission123"
            doc_ref.update.assert_called_once()
            # Should not call user service for non-metadata updates
            mock_user_service.update_enrolled_mission.assert_not_called()

    def test_update_mission_metadata_triggers_propagation(
        self, mock_db, mock_user_service, existing_mission_data, enrollment_data
    ):
        """Updating mission metadata triggers propagation to enrolled users."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        # Mock enrollments collection with proper where().get() chain
        enrollments_collection = MagicMock()
        enrollment_doc = MagicMock()
        enrollment_doc.id = "user123_mission123"
        enrollment_doc.to_dict.return_value = enrollment_data

        where_mock = MagicMock()
        where_mock.get.return_value = [enrollment_doc]
        enrollments_collection.where.return_value = where_mock

        def collection_side_effect(name):
            if name == "missions":
                return missions_collection
            elif name == "enrollments":
                return enrollments_collection

        mock_db.collection.side_effect = collection_side_effect
        service = MissionService(mock_db, mock_user_service)

        # Update metadata field (triggers propagation)
        update_data = MissionUpdate(
            title="Updated Mission Title",
            short_description="Updated description",
        )

        with patch("app.services.mission_service.datetime") as mock_datetime:
            mock_datetime.today.return_value = datetime(2025, 1, 20)
            with patch("app.services.mission_service.logger"):
                mission = service.update_mission("mission123", update_data)

                assert mission.id == "mission123"
                # Should call user service to propagate updates
                mock_user_service.update_enrolled_mission.assert_called_once()

    def test_update_mission_not_found_raises_404(self, mock_db, mock_user_service):
        """Update non-existent mission raises 404."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        not_found = FirestoreMocks.document_not_found()
        doc_ref.get.return_value = not_found
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        update_data = MissionUpdate(title="New Title")

        with pytest.raises(HTTPException) as exc:
            service.update_mission("nonexistent", update_data)

        assert exc.value.status_code == 404


# ============================================================================
# DELETE MISSION TESTS
# ============================================================================


class TestDeleteMission:
    """Test mission deletion."""

    def test_delete_mission_success(self, mock_db, mock_user_service, existing_mission_data):
        """Successfully delete mission and its checkpoints."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.return_value = existing_doc

        # Mock checkpoints subcollection
        checkpoint1 = MagicMock()
        checkpoint2 = MagicMock()
        doc_ref.collection.return_value.get.return_value = [checkpoint1, checkpoint2]

        missions_collection.document.return_value = doc_ref
        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        result = service.delete_mission("mission123")

        assert "deleted successfully" in result["message"]
        doc_ref.delete.assert_called_once()
        # Verify checkpoints were deleted
        checkpoint1.reference.delete.assert_called_once()
        checkpoint2.reference.delete.assert_called_once()

    def test_delete_mission_not_found_raises_404(self, mock_db, mock_user_service):
        """Delete non-existent mission raises 404."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        not_found = FirestoreMocks.document_not_found()
        doc_ref.get.return_value = not_found
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        with pytest.raises(HTTPException) as exc:
            service.delete_mission("nonexistent")

        assert exc.value.status_code == 404


# ============================================================================
# QUERY MISSION TESTS
# ============================================================================


class TestGetMissionsByCreator:
    """Test retrieving missions by creator."""

    def test_get_missions_by_creator_success(self, mock_db, mock_user_service):
        """Successfully retrieve creator's missions."""
        missions_data = [
            {
                "id": f"mission{i}",
                "title": f"Mission {i}",
                "short_description": f"Description {i}",
                "description": f"Long description for mission {i}",
                "level": "Beginner",
                "topics_to_cover": ["Topic 1", "Topic 2"],
                "learning_goal": f"Learn mission {i}",
                "learning_style": [],
                "byte_size_checkpoints": ["Step 1", "Step 2", "Step 3", "Step 4"],
                "skills": [],
                "creator_id": "creator123",
                "is_public": True,
                "created_at": datetime(2025, 1, i),
                "updated_at": datetime(2025, 1, i),
            }
            for i in range(1, 4)
        ]

        missions_collection = FirestoreMocks.collection_with_items(missions_data)
        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        missions = service.get_missions_by_creator("creator123")

        assert len(missions) == 3
        assert missions[0].creator_id == "creator123"

    def test_get_missions_by_creator_empty(self, mock_db, mock_user_service):
        """Get missions for creator with no missions returns empty list."""
        missions_collection = FirestoreMocks.collection_empty()
        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        missions = service.get_missions_by_creator("creator123")

        assert missions == []


class TestGetPublicMissions:
    """Test retrieving public missions."""

    def test_get_public_missions_success(self, mock_db, mock_user_service):
        """Successfully retrieve public missions."""
        missions_data = [
            {
                "id": f"mission{i}",
                "title": f"Public Mission {i}",
                "short_description": f"Description {i}",
                "description": f"Long description for mission {i}",
                "level": "Intermediate",
                "topics_to_cover": ["Topic A", "Topic B"],
                "learning_goal": f"Master mission {i}",
                "learning_style": ["examples"],
                "byte_size_checkpoints": ["Intro", "Step 1", "Step 2", "Final"],
                "skills": ["Skill 1"],
                "creator_id": f"creator{i}",
                "is_public": True,
                "created_at": datetime(2025, 1, i),
                "updated_at": datetime(2025, 1, i),
            }
            for i in range(1, 4)
        ]

        missions_collection = FirestoreMocks.collection_with_items(missions_data)
        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        missions = service.get_public_missions(limit=10)

        assert len(missions) == 3
        assert all(m.is_public for m in missions)


# ============================================================================
# PROPAGATION TESTS
# ============================================================================


class TestPropagationEdgeCases:
    """Test mission update propagation edge cases."""

    def test_propagation_handles_no_enrollments(
        self, mock_db, mock_user_service, existing_mission_data
    ):
        """Propagation handles missions with no enrollments."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        # Empty enrollments collection
        enrollments_collection = FirestoreMocks.collection_empty()

        def collection_side_effect(name):
            if name == "missions":
                return missions_collection
            elif name == "enrollments":
                return enrollments_collection

        mock_db.collection.side_effect = collection_side_effect
        service = MissionService(mock_db, mock_user_service)

        update_data = MissionUpdate(title="Updated Title")

        with patch("app.services.mission_service.logger") as mock_logger:
            mission = service.update_mission("mission123", update_data)

            assert mission.id == "mission123"
            # Should log that propagation started but no users to update
            assert mock_logger.info.called

    def test_propagation_handles_missing_user_id(
        self, mock_db, mock_user_service, existing_mission_data
    ):
        """Propagation skips enrollments with missing user_id."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        # Enrollment missing user_id
        bad_enrollment = {
            "id": "mission123_missing",
            "mission_id": "mission123",
            # "user_id": missing!
            "progress": 50.0,
        }

        # Mock enrollments collection with proper where().get() chain
        enrollments_collection = MagicMock()
        enrollment_doc = MagicMock()
        enrollment_doc.id = "mission123_missing"
        enrollment_doc.to_dict.return_value = bad_enrollment

        where_mock = MagicMock()
        where_mock.get.return_value = [enrollment_doc]
        enrollments_collection.where.return_value = where_mock

        def collection_side_effect(name):
            if name == "missions":
                return missions_collection
            elif name == "enrollments":
                return enrollments_collection

        mock_db.collection.side_effect = collection_side_effect
        service = MissionService(mock_db, mock_user_service)

        update_data = MissionUpdate(title="Updated Title")

        with patch("app.services.mission_service.logger") as mock_logger:
            mission = service.update_mission("mission123", update_data)

            # Should log warning about missing user_id
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0

    def test_propagation_continues_on_individual_failure(
        self, mock_db, mock_user_service, existing_mission_data, enrollment_data
    ):
        """Propagation continues even if one user update fails."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        # Two enrollments
        enrollment2 = enrollment_data.copy()
        enrollment2["user_id"] = "user456"

        # Mock enrollments collection with proper where().get() chain
        enrollments_collection = MagicMock()

        enrollment_doc1 = MagicMock()
        enrollment_doc1.id = "user123_mission123"
        enrollment_doc1.to_dict.return_value = enrollment_data

        enrollment_doc2 = MagicMock()
        enrollment_doc2.id = "user456_mission123"
        enrollment_doc2.to_dict.return_value = enrollment2

        where_mock = MagicMock()
        where_mock.get.return_value = [enrollment_doc1, enrollment_doc2]
        enrollments_collection.where.return_value = where_mock

        def collection_side_effect(name):
            if name == "missions":
                return missions_collection
            elif name == "enrollments":
                return enrollments_collection

        mock_db.collection.side_effect = collection_side_effect

        # First user update fails, second succeeds
        call_count = [0]

        def update_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise HTTPException(status_code=404, detail="Not found")
            return None

        mock_user_service.update_enrolled_mission.side_effect = update_side_effect
        service = MissionService(mock_db, mock_user_service)

        update_data = MissionUpdate(title="Updated Title")

        with patch("app.services.mission_service.logger") as mock_logger:
            mission = service.update_mission("mission123", update_data)

            # Should have called user service twice
            assert mock_user_service.update_enrolled_mission.call_count == 2
            # Should have logged warnings
            assert mock_logger.warning.called


# ============================================================================
# EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_create_mission_with_enrollment_success(
        self, mock_db, mock_user_service, valid_mission_create
    ):
        """Create mission with auto-enrollment for creator."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        doc_ref.id = "new_mission_id"
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection

        # Mock enrollment service
        from app.services.enrollment_service import EnrollmentService

        with patch.object(EnrollmentService, "create_enrollment") as mock_create_enrollment:
            from app.models.enrollment import Enrollment

            mock_create_enrollment.return_value = Enrollment(
                id="creator123_new_mission_id",
                user_id="creator123",
                mission_id="new_mission_id",
                progress=0.0,
                enrolled_at=datetime(2025, 1, 15),
                last_accessed_at=datetime(2025, 1, 15),
                completed=False,
                created_at=datetime(2025, 1, 15),
                updated_at=datetime(2025, 1, 15),
            )

            service = MissionService(mock_db, mock_user_service)

            mission, enrollment = service.create_mission_with_enrollment(
                valid_mission_create, user_id="creator123"
            )

            assert mission.id == "new_mission_id"
            assert enrollment.user_id == "creator123"
            assert enrollment.mission_id == "new_mission_id"

    def test_partial_mission_update(self, mock_db, mock_user_service, existing_mission_data):
        """Partial update only changes specified fields."""
        missions_collection = MagicMock()
        doc_ref = MagicMock()
        existing_doc = FirestoreMocks.document_exists("mission123", existing_mission_data)
        doc_ref.get.side_effect = [existing_doc, existing_doc]
        missions_collection.document.return_value = doc_ref

        mock_db.collection.return_value = missions_collection
        service = MissionService(mock_db, mock_user_service)

        # Only update is_public
        update_data = MissionUpdate(is_public=False)

        service.update_mission("mission123", update_data)

        # Verify only non-None fields are updated
        call_args = doc_ref.update.call_args[0][0]
        assert "is_public" in call_args
        assert call_args["is_public"] is False
        assert "updated_at" in call_args
