from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class User(BaseModel):
    id: str
    firebase_uid: str
    name: str
    email: EmailStr
    picture: Optional[AnyUrl] = None
    created_at: datetime = Field(default_factory=datetime.today)
    updated_at: datetime = Field(default_factory=datetime.today)


class UserCreate(BaseModel):
    firebase_uid: str
    name: str
    email: EmailStr
    picture: Optional[AnyUrl] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    picture: Optional[AnyUrl] = None
