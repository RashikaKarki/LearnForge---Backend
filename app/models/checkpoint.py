from datetime import datetime

from pydantic import BaseModel, Field


class Checkpoint(BaseModel):
    id: str
    mission_id: str = Field(..., description="ID of the parent mission")
    title: str
    content: str
    order: int = Field(..., description="Order/sequence of checkpoint in the mission")
    sources: dict[str, str] | None = Field(
        default_factory=dict,
        description="Mapping of source names to URLs or references",
    )
    created_at: datetime = Field(default_factory=datetime.today)


class CheckpointCreate(BaseModel):
    title: str
    content: str
    order: int
    sources: list[str] | None = None


class CheckpointUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    order: int | None = None
