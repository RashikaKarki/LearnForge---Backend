from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field

class UserEnrolledMission(BaseModel):
    """Denormalized enrollment stored in users/{user_id}/enrolled_missions subcollection.
    
    This is optimized for fast dashboard reads - includes mission details to avoid joins.
    """

    mission_id: str = Field(..., description="ID of the mission")
    mission_title: str = Field(..., description="Mission title (denormalized from missions)")
    mission_short_description: str = Field(
        ..., description="Mission short description (denormalized from missions)"
    )
    mission_skills: list[str] = Field(
        default_factory=list, description="Mission skills (denormalized from missions)"
    )
    progress: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)"
    )
    enrolled_at: datetime = Field(default_factory=datetime.today)
    last_accessed_at: datetime = Field(default_factory=datetime.today)
    completed: bool = Field(default=False, description="Whether the mission is completed")
    updated_at: datetime = Field(default_factory=datetime.today)

class UserEnrolledMissionCreate(BaseModel):
    mission_id: str
    mission_title: str
    mission_short_description: str
    mission_skills: list[str] = []
    progress: float = 0.0
    enrolled_at: datetime = Field(default_factory=datetime.today)
    last_accessed_at: datetime = Field(default_factory=datetime.today)
    completed: bool = False


class UserEnrolledMissionUpdate(BaseModel):
    """Update schema for user enrolled missions - all fields optional."""
    
    # Mission metadata fields (updated when mission changes)
    mission_title: str | None = None
    mission_short_description: str | None = None
    mission_skills: list[str] | None = None
    
    # Progress tracking fields
    progress: float | None = Field(None, ge=0.0, le=100.0)
    last_accessed_at: datetime | None = None
    completed: bool | None = None


class User(BaseModel):
    id: str
    firebase_uid: str
    name: str
    email: EmailStr
    picture: AnyUrl | None = None
    enrolled_missions: list[UserEnrolledMission] = Field(
        default_factory=list,
        description="List of missions the user is enrolled in (denormalized, optional)"
    )
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class UserCreate(BaseModel):
    firebase_uid: str
    name: str
    email: EmailStr
    picture: AnyUrl | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    picture: AnyUrl | None = None
