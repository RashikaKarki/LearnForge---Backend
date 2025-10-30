from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Mission(BaseModel):
    id: str
    title: str
    short_description: str
    description: str
    creator_id: str = Field(..., description="User ID of the mission creator")
    level: Literal["Beginner", "Intermediate", "Advanced"] = Field(
        ..., description="Beginner, Intermediate, or Advanced"
    )
    topics_to_cover: list[str] = Field(..., description="List of topics covered in the mission")
    learning_goal: str = Field(..., description="User's learning goal and objectives")
    byte_size_checkpoints: list[str] = Field(..., description="List of checkpoint names in order")
    skills: list[str] | None = Field(
        default_factory=list, description="List of skills associated with the mission"
    )
    is_public: bool = Field(default=True, description="Whether the mission is publicly accessible")
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class MissionCreate(BaseModel):
    title: str
    short_description: str
    description: str
    creator_id: str
    level: Literal["Beginner", "Intermediate", "Advanced"] = Field(
        ..., description="Beginner, Intermediate, or Advanced"
    )
    topics_to_cover: list[str] = Field(
        ..., description="List of topics covered in the mission including prerequisites"
    )
    learning_goal: str = Field(..., description="User's learning goal and objectives")
    byte_size_checkpoints: list[str] = Field(
        ..., description="List of 4-6 checkpoint names in order", min_length=4, max_length=6
    )
    skills: list[str] | None = Field(
        default_factory=list, description="List of skills associated with the mission"
    )
    is_public: bool = True


class MissionUpdate(BaseModel):
    title: str | None = None
    short_description: str | None = None
    description: str | None = None
    is_public: bool | None = None
    level: Literal["Beginner", "Intermediate", "Advanced"] | None = None
    skills: list[str] | None = None
