"""Unit tests for Checkpoint model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.checkpoint import Checkpoint, CheckpointCreate, CheckpointUpdate


def test_checkpoint_model_valid_creation():
    """Should create checkpoint with all required fields."""
    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Introduction to Variables",
        content="Learn about Python variables and data types",
        order=1,
        sources={"Python Documentation": "https://docs.python.org"},
    )

    assert checkpoint.id == "checkpoint123"
    assert checkpoint.mission_id == "mission123"
    assert checkpoint.title == "Introduction to Variables"
    assert checkpoint.content == "Learn about Python variables and data types"
    assert checkpoint.order == 1
    assert checkpoint.sources == {"Python Documentation": "https://docs.python.org"}


def test_checkpoint_model_sources_defaults_to_empty_list():
    """Should default sources to empty list when not provided."""
    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Test Checkpoint",
        content="Test content",
        order=1,
    )

    assert checkpoint.sources == {}


def test_checkpoint_model_timestamp_auto_generated():
    """Should auto-generate created_at timestamp."""
    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Test Checkpoint",
        content="Test content",
        order=1,
    )

    assert isinstance(checkpoint.created_at, datetime)


@pytest.mark.parametrize(
    "order_value",
    [0, 1, 5, 10, 100],
)
def test_checkpoint_order_accepts_positive_integers(order_value):
    """Should accept positive integers for order field."""
    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Test",
        content="Test",
        order=order_value,
    )

    assert checkpoint.order == order_value


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("id", {"mission_id": "m123", "title": "Title", "content": "Content", "order": 1}),
        ("mission_id", {"id": "c123", "title": "Title", "content": "Content", "order": 1}),
        ("title", {"id": "c123", "mission_id": "m123", "content": "Content", "order": 1}),
        ("content", {"id": "c123", "mission_id": "m123", "title": "Title", "order": 1}),
        ("order", {"id": "c123", "mission_id": "m123", "title": "Title", "content": "Content"}),
    ],
)
def test_checkpoint_model_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing."""
    with pytest.raises(ValidationError):
        Checkpoint(**data)


def test_checkpoint_create_valid():
    """Should create CheckpointCreate with required fields."""
    checkpoint_create = CheckpointCreate(
        title="Introduction",
        content="Content here",
        order=1,
        sources=["https://example.com"],
    )

    assert checkpoint_create.title == "Introduction"
    assert checkpoint_create.content == "Content here"
    assert checkpoint_create.order == 1
    assert checkpoint_create.sources == ["https://example.com"]


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("title", {"content": "Content", "order": 1}),
        ("content", {"title": "Title", "order": 1}),
        ("order", {"title": "Title", "content": "Content"}),
    ],
)
def test_checkpoint_create_missing_required_field_raises(missing_field, data):
    """Should raise ValidationError when required field is missing in CheckpointCreate."""
    with pytest.raises(ValidationError):
        CheckpointCreate(**data)


def test_checkpoint_update_all_fields_optional():
    """Should allow CheckpointUpdate with no fields."""
    checkpoint_update = CheckpointUpdate()

    assert checkpoint_update.title is None
    assert checkpoint_update.content is None
    assert checkpoint_update.order is None


def test_checkpoint_update_partial_fields():
    """Should allow CheckpointUpdate with only some fields."""
    checkpoint_update = CheckpointUpdate(title="Updated Title")

    assert checkpoint_update.title == "Updated Title"
    assert checkpoint_update.content is None
    assert checkpoint_update.order is None


def test_checkpoint_update_all_fields():
    """Should allow CheckpointUpdate with all fields."""
    checkpoint_update = CheckpointUpdate(
        title="Updated Title",
        content="Updated Content",
        order=5,
    )

    assert checkpoint_update.title == "Updated Title"
    assert checkpoint_update.content == "Updated Content"
    assert checkpoint_update.order == 5


def test_checkpoint_update_order_only():
    """Should allow updating only the order."""
    checkpoint_update = CheckpointUpdate(order=3)

    assert checkpoint_update.title is None
    assert checkpoint_update.content is None
    assert checkpoint_update.order == 3
