from datetime import datetime

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.user import (
    User,
    UserCreate,
    UserEnrolledMission,
    UserEnrolledMissionCreate,
    UserEnrolledMissionUpdate,
)
from app.utils.firestore_exception import handle_firestore_exceptions


class UserService:
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("users")

    @handle_firestore_exceptions
    def create_user(self, data: UserCreate) -> User:
        existing = None
        try:
            existing = self.get_user_by_email(data.email)
        except HTTPException as e:
            if e.status_code != status.HTTP_404_NOT_FOUND:
                raise

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        doc_ref = self.collection.document()

        # Create User object with id and timestamps
        now = datetime.now()
        user_data = {
            **data.model_dump(),
            "id": doc_ref.id,
            "created_at": now,
            "updated_at": now,
        }

        doc_ref.set(user_data)

        return User(**user_data)

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
        docs = self.collection.where(filter=FieldFilter("email", "==", email)).limit(1).get()
        for doc in docs:
            return User(**doc.to_dict())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found.",
        )

    @handle_firestore_exceptions
    def get_or_create_user(self, data: UserCreate) -> User:
        try:
            return self.get_user_by_email(data.email)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                return self.create_user(data)
            else:
                raise

    @handle_firestore_exceptions
    def get_enrolled_missions(self, user_id: str, limit: int = 100) -> list[UserEnrolledMission]:
        docs = self.collection.document(user_id).collection("enrolled_missions").limit(limit).get()
        return [UserEnrolledMission(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def get_enrolled_mission(self, user_id: str, mission_id: str) -> UserEnrolledMission:
        doc = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(mission_id)
            .get()
        )

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolled mission '{mission_id}' not found for user '{user_id}'.",
            )

        return UserEnrolledMission(**doc.to_dict())

    @handle_firestore_exceptions
    def create_enrolled_mission(
        self,
        user_id: str,
        data: UserEnrolledMissionCreate,
    ) -> UserEnrolledMission:
        # Check if already exists
        existing_doc = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(data.mission_id)
            .get()
        )

        if existing_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is already enrolled in mission '{data.mission_id}'.",
            )

        # Prepare data with timestamps
        enrolled_data = data.model_dump()
        enrolled_data["updated_at"] = datetime.today()

        # Create document
        user_enrolled_ref = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(data.mission_id)
        )
        user_enrolled_ref.set(enrolled_data)

        return UserEnrolledMission(**enrolled_data)

    @handle_firestore_exceptions
    def update_enrolled_mission(
        self,
        user_id: str,
        mission_id: str,
        data: UserEnrolledMissionUpdate,
    ) -> UserEnrolledMission:
        user_enrolled_ref = (
            self.collection.document(user_id).collection("enrolled_missions").document(mission_id)
        )

        doc = user_enrolled_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolled mission '{mission_id}' not found for user '{user_id}'.",
            )

        # Only include non-None fields
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        if update_data:
            update_data["updated_at"] = datetime.today()
            user_enrolled_ref.update(update_data)

        # Fetch and return updated document
        updated_doc = user_enrolled_ref.get()
        return UserEnrolledMission(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def delete_enrolled_mission(
        self,
        user_id: str,
        mission_id: str,
    ) -> dict:
        user_enrolled_ref = (
            self.collection.document(user_id).collection("enrolled_missions").document(mission_id)
        )

        doc = user_enrolled_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolled mission '{mission_id}' not found for user '{user_id}'.",
            )

        user_enrolled_ref.delete()

        return {
            "message": f"Enrolled mission '{mission_id}' deleted successfully for user '{user_id}'."
        }

    @handle_firestore_exceptions
    def get_first_user(self) -> User | None:
        """
        TEMP: Get the first user from the database (for testing purposes only).
        This should be removed when proper authentication is implemented.
        """
        docs = self.collection.limit(1).get()
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            return User(**user_data)
        return None
