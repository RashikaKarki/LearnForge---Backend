from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionLog(BaseModel):
    """Session log model for tracking WebSocket sessions"""

    id: str = Field(..., description="Unique session identifier (auto-generated)")
    user_id: str = Field(..., description="User ID associated with this session")
    status: Literal["active", "completed", "abandoned", "error"] = Field(
        default="active", description="Current status of the session"
    )
    mission_id: str | None = Field(
        default=None, description="ID of the mission created in this session (if completed)"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when session was completed"
    )


class SessionLogCreate(BaseModel):
    """Data required to create a new session"""

    user_id: str = Field(..., description="User ID for the session")


class SessionLogUpdate(BaseModel):
    """Data for updating an existing session"""

    status: Literal["active", "completed", "abandoned", "error"] | None = None
    mission_id: str | None = None
    completed_at: datetime | None = None


class SessionResponse(BaseModel):
    """Response model for session creation"""

    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="User ID associated with this session")
    status: str = Field(default="active", description="Session status")
    created_at: datetime = Field(..., description="Session creation timestamp")
