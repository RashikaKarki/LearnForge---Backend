from datetime import datetime

from fastapi import HTTPException, status

from app.models.user import User
from app.utils.firestore_exception import handle_firestore_exceptions


class UserService:
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("users")

    @handle_firestore_exceptions
    def create_user(self, data: dict) -> User:
        existing = None
        try:
            existing = self.get_user_by_email(data["email"])
        except HTTPException as e:
            if e.status_code != status.HTTP_404_NOT_FOUND:
                raise

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        doc_ref = self.collection.document()
        data["id"] = doc_ref.id
        data["created_at"] = datetime.today()
        data["updated_at"] = datetime.today()
        doc_ref.set(data)
        return User(**data)

    @handle_firestore_exceptions
    def get_user(self, user_id: str) -> User:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )
        return User(**doc.to_dict())

    @handle_firestore_exceptions
    def get_user_by_email(self, email: str) -> User:
        docs = self.collection.where("email", "==", email).limit(1).get()
        for doc in docs:
            return User(**doc.to_dict())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found.",
        )

    @handle_firestore_exceptions
    def get_or_create_user(self, data: dict) -> User:
        try:
            return self.get_user_by_email(data["email"])
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                return self.create_user(data)
            else:
                raise
