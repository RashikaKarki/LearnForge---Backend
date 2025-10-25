from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Checkpoint(BaseModel):
    id: str
    mission_id: str = Field(..., description="ID of the parent mission")
    title: str
    content: str
    order: int = Field(..., description="Order/sequence of checkpoint in the mission")
    sources: Optional[dict[str, str]] = Field(
        default_factory=dict,
        description="Mapping of source names to URLs or references",
    )
    created_at: datetime = Field(default_factory=datetime.today)


class CheckpointCreate(BaseModel):
    title: str
    content: str
    order: int
    sources: Optional[list[str]] = None


class CheckpointUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    order: Optional[int] = None
