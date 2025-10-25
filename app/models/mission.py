from datetime import datetime

from pydantic import BaseModel, Field


class Mission(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str = Field(..., description="User ID of the mission creator")
    skills: list[str] | None = Field(
        default_factory=list, description="List of skills associated with the mission"
    )
    is_public: bool = Field(default=True, description="Whether the mission is publicly accessible")
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class MissionCreate(BaseModel):
    title: str
    description: str
    creator_id: str
    is_public: bool = True
    skills: list[str] | None = None


class MissionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_public: bool | None = None
