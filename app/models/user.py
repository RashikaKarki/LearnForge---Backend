from datetime import datetime

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class User(BaseModel):
    id: str
    firebase_uid: str
    name: str
    email: EmailStr
    picture: AnyUrl | None = None
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
