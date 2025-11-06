from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EnrollmentSessionLog(BaseModel):
    """Enrollment session log model for tracking learning sessions"""

    id: str = Field(..., description="Unique session identifier (auto-generated)")
    enrollment_id: str = Field(..., description="Enrollment ID")
    user_id: str = Field(..., description="User ID associated with this session")
    mission_id: str = Field(..., description="Mission ID for this enrollment")
    status: Literal["created", "started", "completed"] = Field(
        default="created", description="Current status of the learning session"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: datetime | None = Field(
        default=None, description="Timestamp when learning session was started"
    )
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when learning session was completed"
    )


class EnrollmentSessionLogCreate(BaseModel):
    """Data required to create a new enrollment session log"""

    enrollment_id: str = Field(..., description="Enrollment ID")
    user_id: str = Field(..., description="User ID for the session")
    mission_id: str = Field(..., description="Mission ID for the session")


class EnrollmentSessionLogUpdate(BaseModel):
    """Data for updating an existing enrollment session log"""

    status: Literal["created", "started", "completed"] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
