from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuizQuestion(BaseModel):
    """Structure for a single quiz question with multiple choice options."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., description="Clear, concise question text")
    options: dict[str, str] = Field(
        ...,
        description="Dictionary with exactly 4 keys ('a', 'b', 'c', 'd') mapping to option text",
    )
    right_option_key: str = Field(
        ...,
        description="The correct answer key: must be one of 'a', 'b', 'c', or 'd'",
        pattern="^[a-d]$",
    )
    explanation: str = Field(
        ..., description="Detailed explanation of why the correct answer is right"
    )


class Checkpoint(BaseModel):
    id: str
    mission_id: str = Field(..., description="ID of the parent mission")
    title: str
    content: str
    order: int = Field(..., description="Order/sequence of checkpoint in the mission")
    sources: dict[str, str] | None = Field(
        default_factory=dict,
        description="Mapping of source names to URLs (e.g., {'Python Docs': 'https://docs.python.org'})",
    )
    quiz_questions: list[QuizQuestion] | None = Field(
        default_factory=list,
        description="List of quiz questions for this checkpoint",
    )
    created_at: datetime = Field(default_factory=datetime.today)


class CheckpointCreate(BaseModel):
    title: str
    content: str
    order: int
    sources: dict[str, str] | None = Field(
        default_factory=dict,
        description="Mapping of source names to URLs (e.g., {'Python Docs': 'https://docs.python.org'})",
    )
    quiz_questions: list[QuizQuestion] | None = Field(
        default_factory=list, description="List of quiz questions for this checkpoint"
    )


class CheckpointUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    order: int | None = None
    sources: dict[str, str] | None = None
    quiz_questions: list[QuizQuestion] | None = None
