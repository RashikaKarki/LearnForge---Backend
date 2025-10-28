from datetime import datetime

from pydantic import BaseModel, Field


class CheckpointProgress(BaseModel):
    """Model for checkpoint progress sub-collection."""

    checkpoint_id: str = Field(..., description="ID of the checkpoint")
    title: str
    completed: bool = Field(default=False, description="Whether the checkpoint is completed")
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class CheckpointProgressCreate(BaseModel):
    """Schema for creating checkpoint progress."""

    checkpoint_id: str
    title: str
    completed: bool = False


class CheckpointProgressUpdate(BaseModel):
    """Schema for updating checkpoint progress."""

    completed: bool


class Enrollment(BaseModel):
    id: str = Field(..., description="Composite key: {userId}_{missionId}")
    user_id: str = Field(..., description="ID of the enrolled user")
    mission_id: str = Field(..., description="ID of the mission")
    enrolled_at: datetime = Field(default_factory=datetime.today)
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)"
    )
    last_accessed_at: datetime = Field(default_factory=datetime.today)
    completed: bool = Field(default=False, description="Whether the mission is completed")
    checkpoint_progress: list[CheckpointProgress] = Field(
        default_factory=list, description="List of checkpoint progress"
    )
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class EnrollmentCreate(BaseModel):
    user_id: str
    mission_id: str
    progress: float = 0.0


class EnrollmentUpdate(BaseModel):
    progress: float | None = Field(None, ge=0.0, le=100.0)
    last_accessed_at: datetime | None = None
    completed: bool | None = None
