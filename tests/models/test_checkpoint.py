"""Unit tests for Checkpoint model."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.checkpoint import Checkpoint, CheckpointCreate, CheckpointUpdate, QuizQuestion


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
    """Should default sources to empty dict when not provided."""
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
        order=1,
    )

    assert checkpoint_create.title == "Introduction"
    assert checkpoint_create.order == 1


@pytest.mark.parametrize(
    "missing_field,data",
    [
        ("title", {"order": 1}),
        ("order", {"title": "Title"}),
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


# QuizQuestion Tests


def test_quiz_question_valid_creation():
    """Should create valid quiz question with all required fields."""
    quiz = QuizQuestion(
        question="What is Python?",
        options={
            "a": "A programming language",
            "b": "A type of snake",
            "c": "A web framework",
            "d": "An operating system",
        },
        right_option_key="a",
        explanation="Python is a high-level, interpreted programming language.",
    )

    assert quiz.question == "What is Python?"
    assert len(quiz.options) == 4
    assert quiz.options["a"] == "A programming language"
    assert quiz.right_option_key == "a"
    assert "programming language" in quiz.explanation


def test_quiz_question_invalid_option_key_raises():
    """Should raise ValidationError when right_option_key is not a, b, c, or d."""
    with pytest.raises(ValidationError) as exc:
        QuizQuestion(
            question="Test?",
            options={"a": "1", "b": "2", "c": "3", "d": "4"},
            right_option_key="e",  # Invalid
            explanation="Test",
        )

    assert "right_option_key" in str(exc.value)


def test_quiz_question_uppercase_option_key_raises():
    """Should raise ValidationError when right_option_key is uppercase."""
    with pytest.raises(ValidationError) as exc:
        QuizQuestion(
            question="Test?",
            options={"a": "1", "b": "2", "c": "3", "d": "4"},
            right_option_key="A",  # Invalid - must be lowercase
            explanation="Test",
        )

    assert "right_option_key" in str(exc.value)


def test_quiz_question_extra_fields_forbidden():
    """Should reject extra fields due to ConfigDict(extra='forbid')."""
    with pytest.raises(ValidationError) as exc:
        QuizQuestion(
            question="Test?",
            options={"a": "1", "b": "2", "c": "3", "d": "4"},
            right_option_key="a",
            explanation="Test",
            extra_field="Not allowed",
        )

    assert "extra_field" in str(exc.value)


def test_checkpoint_with_quiz_questions():
    """Should create checkpoint with quiz questions."""
    quiz = QuizQuestion(
        question="What is Python?",
        options={
            "a": "A programming language",
            "b": "A snake",
            "c": "A framework",
            "d": "An OS",
        },
        right_option_key="a",
        explanation="Python is a programming language.",
    )

    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Python Basics",
        content="Learn Python",
        order=1,
        sources={"Python Official": "https://python.org"},
        quiz_questions=[quiz],
    )

    assert len(checkpoint.quiz_questions) == 1
    assert checkpoint.quiz_questions[0].question == "What is Python?"
    assert checkpoint.quiz_questions[0].right_option_key == "a"


def test_checkpoint_quiz_questions_defaults_to_empty_list():
    """Should default quiz_questions to empty list when not provided."""
    checkpoint = Checkpoint(
        id="checkpoint123",
        mission_id="mission123",
        title="Test",
        content="Test",
        order=1,
    )

    assert checkpoint.quiz_questions == []


def test_checkpoint_create_with_quiz_questions():
    """Should create CheckpointCreate with only title and order."""
    checkpoint_create = CheckpointCreate(
        title="AI Introduction",
        order=1,
    )

    assert checkpoint_create.title == "AI Introduction"
    assert checkpoint_create.order == 1


def test_checkpoint_update_with_quiz_questions():
    """Should allow updating quiz_questions."""
    quiz = QuizQuestion(
        question="Updated question?",
        options={"a": "Yes", "b": "No", "c": "Maybe", "d": "Not sure"},
        right_option_key="a",
        explanation="It's yes.",
    )

    checkpoint_update = CheckpointUpdate(quiz_questions=[quiz])

    assert checkpoint_update.title is None
    assert len(checkpoint_update.quiz_questions) == 1
    assert checkpoint_update.quiz_questions[0].question == "Updated question?"
