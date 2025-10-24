from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    firebase_uid: str
    name: str
    email: str
    picture: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.today)
    created_at: datetime = Field(default_factory=datetime.today)
