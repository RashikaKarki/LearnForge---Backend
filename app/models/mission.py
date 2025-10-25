from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Mission(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str = Field(..., description="User ID of the mission creator")
    skills: Optional[list[str]] = Field(
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
    skills: Optional[list[str]] = None


class MissionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
