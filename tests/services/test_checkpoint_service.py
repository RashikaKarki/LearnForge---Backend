"""Unit tests for CheckpointService."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.models.checkpoint import CheckpointCreate, CheckpointUpdate
from app.services.checkpoint_service import CheckpointService
from tests.mocks.firestore import FirestoreMocks


@pytest.fixture
def valid_checkpoint_create_data():
    """Test data for creating a checkpoint."""
    return CheckpointCreate(
        title="Introduction to Variables",
        content="Learn about Python variables and data types",
        order=1,
    )


@pytest.fixture
def existing_checkpoint():
    """Existing checkpoint dict as returned from Firestore."""
    return {
        "id": "checkpoint123",
        "mission_id": "mission123",
        "title": "Introduction to Variables",
        "content": "Learn about Python variables and data types",
        "order": 1,
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
    }


def test_create_checkpoint_success(valid_checkpoint_create_data):
    """Should create checkpoint when mission exists."""
    missions_collection = MagicMock()
    checkpoints_collection = FirestoreMocks.collection_empty()

    # Mock mission exists
    mission_doc = FirestoreMocks.document_exists("mission123", {"id": "mission123"})
    missions_collection.document.return_value.get.return_value = mission_doc
    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    checkpoint = service.create_checkpoint("mission123", valid_checkpoint_create_data)

    assert checkpoint.title == valid_checkpoint_create_data.title
    assert checkpoint.mission_id == "mission123"
    assert checkpoint.id == "auto_generated_id"
    checkpoints_collection.document().set.assert_called_once()


def test_create_checkpoint_mission_not_found_raises_404(valid_checkpoint_create_data):
    """Should raise 404 when mission doesn't exist."""
    missions_collection = MagicMock()
    mission_doc = FirestoreMocks.document_not_found()
    missions_collection.document.return_value.get.return_value = mission_doc

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    with pytest.raises(HTTPException) as exc:
        service.create_checkpoint("missing", valid_checkpoint_create_data)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_checkpoint_found_returns_checkpoint(existing_checkpoint):
    """Should return checkpoint when it exists."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    checkpoint_doc = FirestoreMocks.document_exists("checkpoint123", existing_checkpoint)
    checkpoints_collection.document.return_value.get.return_value = checkpoint_doc
    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    checkpoint = service.get_checkpoint("mission123", "checkpoint123")

    assert checkpoint.id == existing_checkpoint["id"]
    assert checkpoint.title == existing_checkpoint["title"]


def test_get_checkpoint_not_found_raises_404():
    """Should raise 404 when checkpoint doesn't exist."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    checkpoint_doc = FirestoreMocks.document_not_found()
    checkpoints_collection.document.return_value.get.return_value = checkpoint_doc
    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    with pytest.raises(HTTPException) as exc:
        service.get_checkpoint("mission123", "missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_all_checkpoints(existing_checkpoint):
    """Should return all checkpoints ordered by 'order' field."""
    checkpoints_data = [
        existing_checkpoint,
        {**existing_checkpoint, "id": "checkpoint456", "order": 2, "title": "Checkpoint 2"},
    ]

    missions_collection = MagicMock()
    checkpoints_collection = FirestoreMocks.collection_with_items(checkpoints_data)
    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    checkpoints = service.get_all_checkpoints("mission123")

    assert len(checkpoints) == 2
    assert checkpoints[0].order == 1
    checkpoints_collection.order_by.assert_called_with("order")


def test_update_checkpoint_success(existing_checkpoint):
    """Should update checkpoint successfully."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    doc_ref = checkpoints_collection.document.return_value
    doc_ref.get.side_effect = [
        FirestoreMocks.document_exists("checkpoint123", existing_checkpoint),
        FirestoreMocks.document_exists(
            "checkpoint123", {**existing_checkpoint, "title": "Updated"}
        ),
    ]

    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    update_data = CheckpointUpdate(title="Updated")
    checkpoint = service.update_checkpoint("mission123", "checkpoint123", update_data)

    assert checkpoint.title == "Updated"
    doc_ref.update.assert_called_once()


def test_update_checkpoint_not_found_raises_404():
    """Should raise 404 when updating non-existent checkpoint."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    doc_ref = checkpoints_collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()

    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    with pytest.raises(HTTPException) as exc:
        service.update_checkpoint("mission123", "missing", CheckpointUpdate(title="New"))

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_delete_checkpoint_success(existing_checkpoint):
    """Should delete checkpoint successfully."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    doc_ref = checkpoints_collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_exists("checkpoint123", existing_checkpoint)

    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    result = service.delete_checkpoint("mission123", "checkpoint123")

    assert "deleted successfully" in result["message"]
    doc_ref.delete.assert_called_once()


def test_delete_checkpoint_not_found_raises_404():
    """Should raise 404 when deleting non-existent checkpoint."""
    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    doc_ref = checkpoints_collection.document.return_value
    doc_ref.get.return_value = FirestoreMocks.document_not_found()

    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    with pytest.raises(HTTPException) as exc:
        service.delete_checkpoint("mission123", "missing")

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


def test_reorder_checkpoints(existing_checkpoint):
    """Should update order of multiple checkpoints."""
    checkpoints_data = [
        existing_checkpoint,
        {**existing_checkpoint, "id": "checkpoint456", "order": 2},
    ]

    missions_collection = MagicMock()
    checkpoints_collection = MagicMock()

    # Mock individual checkpoint documents
    checkpoint1_doc = MagicMock()
    checkpoint1_doc.exists = True
    checkpoint2_doc = MagicMock()
    checkpoint2_doc.exists = True

    def mock_document(checkpoint_id):
        doc = MagicMock()
        doc.get.return_value = (
            checkpoint1_doc if checkpoint_id == "checkpoint123" else checkpoint2_doc
        )
        return doc

    checkpoints_collection.document = mock_document

    # Mock order_by for get_all_checkpoints
    checkpoints_collection.order_by.return_value.get.return_value = [
        MagicMock(to_dict=MagicMock(return_value=checkpoints_data[0])),
        MagicMock(to_dict=MagicMock(return_value=checkpoints_data[1])),
    ]

    missions_collection.document.return_value.collection.return_value = checkpoints_collection

    db = MagicMock()
    db.collection.return_value = missions_collection
    service = CheckpointService(db)

    new_orders = {"checkpoint123": 2, "checkpoint456": 1}
    checkpoints = service.reorder_checkpoints("mission123", new_orders)

    assert len(checkpoints) == 2
