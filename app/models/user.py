from datetime import datetime
from typing import Optional

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class User(BaseModel):
    id: str
    firebase_uid: str
    name: str
    email: EmailStr
    picture: Optional[AnyUrl] = None
    updated_at: datetime = Field(default_factory=datetime.today)
    created_at: datetime = Field(default_factory=datetime.today)
