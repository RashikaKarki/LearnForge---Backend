from datetime import datetime
import logging

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.user import (
    User,
    UserCreate,
    UserEnrolledMission,
    UserEnrolledMissionCreate,
    UserEnrolledMissionUpdate,
    UserUpdate,
)
from app.utils.firestore_exception import handle_firestore_exceptions


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("users")

    @handle_firestore_exceptions
    def create_user(self, data: UserCreate) -> User:
        logger.info(f"Attempting to create user with email: {data.email}")
        existing = None
        try:
            existing = self.get_user_by_email(data.email)
        except HTTPException as e:
            if e.status_code != status.HTTP_404_NOT_FOUND:
                logger.error(f"Error checking for existing user with email {data.email}: {e}")
                raise

        if existing:
            logger.warning(
                f"User creation failed: user with email '{data.email}' already exists (id: {existing.id})"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )

        doc_ref = self.collection.document()

        # Create User object with id and timestamps
        now = datetime.now()
        user_data = {
            **data.model_dump(mode="json"),
            "id": doc_ref.id,
            "created_at": now,
            "updated_at": now,
        }

        try:
            doc_ref.set(user_data)
            logger.info(f"User document saved to Firestore: id={doc_ref.id}")
        except Exception as e:
            logger.error(f"Failed to save user to Firestore: {e}, user_data={user_data}")
            raise

        try:
            user = User(**user_data)
            logger.info(
                f"Successfully created user: id={doc_ref.id}, email={data.email}, firebase_uid={data.firebase_uid}"
            )
            return user
        except Exception as e:
            logger.error(
                f"Failed to create User model from user_data: {e}, user_data={user_data}, "
                f"doc_id={doc_ref.id}"
            )
            raise

    @handle_firestore_exceptions
    def get_user(self, user_id: str) -> User:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            logger.warning(f"User not found: id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )

        user_data = doc.to_dict()
        user_data["id"] = doc.id
        return User(**user_data)

    @handle_firestore_exceptions
    def get_user_by_email(self, email: str) -> User:
        docs = self.collection.where(filter=FieldFilter("email", "==", email)).limit(1).get()
        for doc in docs:
            user_data = doc.to_dict()
            user_data["id"] = doc.id
            return User(**user_data)
        logger.warning(f"User not found by email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found.",
        )

    @handle_firestore_exceptions
    def get_or_create_user(self, data: UserCreate) -> User:
        logger.info(
            f"Getting or creating user with email: {data.email}, firebase_uid: {data.firebase_uid}"
        )
        try:
            user = self.get_user_by_email(data.email)
            logger.info(f"Found existing user: id={user.id}, email={data.email}")
            return user
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.info(f"User not found, creating new user: email={data.email}")
                return self.create_user(data)
            else:
                logger.error(f"Unexpected error getting user by email {data.email}: {e}")
                raise

    @handle_firestore_exceptions
    def get_enrolled_missions(self, user_id: str, limit: int = 100) -> list[UserEnrolledMission]:
        docs = self.collection.document(user_id).collection("enrolled_missions").limit(limit).get()
        missions = [UserEnrolledMission(**doc.to_dict()) for doc in docs]
        logger.info(f"Retrieved {len(missions)} enrolled missions for user: {user_id}")
        return missions

    @handle_firestore_exceptions
    def get_enrolled_mission(self, user_id: str, mission_id: str) -> UserEnrolledMission:
        doc = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(mission_id)
            .get()
        )

        if not doc.exists:
            logger.warning(
                f"Enrolled mission not found: user_id={user_id}, mission_id={mission_id}"
            )
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
        logger.info(f"Creating enrolled mission: user_id={user_id}, mission_id={data.mission_id}")
        # Check if already exists
        existing_doc = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(data.mission_id)
            .get()
        )

        if existing_doc.exists:
            logger.warning(
                f"Enrollment already exists: user_id={user_id}, mission_id={data.mission_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User is already enrolled in mission '{data.mission_id}'.",
            )

        # Prepare data with timestamps
        enrolled_data = data.model_dump(mode="json")
        enrolled_data["updated_at"] = datetime.today()

        # Create document
        user_enrolled_ref = (
            self.collection.document(user_id)
            .collection("enrolled_missions")
            .document(data.mission_id)
        )
        user_enrolled_ref.set(enrolled_data)
        logger.info(
            f"Successfully created enrolled mission: user_id={user_id}, mission_id={data.mission_id}"
        )

        return UserEnrolledMission(**enrolled_data)

    @handle_firestore_exceptions
    def update_enrolled_mission(
        self,
        user_id: str,
        mission_id: str,
        data: UserEnrolledMissionUpdate,
    ) -> UserEnrolledMission:
        logger.info(f"Updating enrolled mission: user_id={user_id}, mission_id={mission_id}")
        user_enrolled_ref = (
            self.collection.document(user_id).collection("enrolled_missions").document(mission_id)
        )

        doc = user_enrolled_ref.get()
        if not doc.exists:
            logger.warning(
                f"Enrolled mission not found for update: user_id={user_id}, mission_id={mission_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolled mission '{mission_id}' not found for user '{user_id}'.",
            )

        # Only include non-None fields
        update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}

        if update_data:
            update_data["updated_at"] = datetime.today()
            user_enrolled_ref.update(update_data)
            logger.info(
                f"Successfully updated enrolled mission: user_id={user_id}, mission_id={mission_id}, fields={list(update_data.keys())}"
            )

        # Fetch and return updated document
        updated_doc = user_enrolled_ref.get()
        return UserEnrolledMission(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def delete_enrolled_mission(
        self,
        user_id: str,
        mission_id: str,
    ) -> dict:
        logger.info(f"Deleting enrolled mission: user_id={user_id}, mission_id={mission_id}")
        user_enrolled_ref = (
            self.collection.document(user_id).collection("enrolled_missions").document(mission_id)
        )

        doc = user_enrolled_ref.get()
        if not doc.exists:
            logger.warning(
                f"Enrolled mission not found for deletion: user_id={user_id}, mission_id={mission_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrolled mission '{mission_id}' not found for user '{user_id}'.",
            )

        user_enrolled_ref.delete()
        logger.info(
            f"Successfully deleted enrolled mission: user_id={user_id}, mission_id={mission_id}"
        )

        return {
            "message": f"Enrolled mission '{mission_id}' deleted successfully for user '{user_id}'."
        }

    @handle_firestore_exceptions
    def update_user(self, user_id: str, data: UserUpdate) -> User:
        """Update user profile information."""
        logger.info(f"Updating user profile: user_id={user_id}")
        user_ref = self.collection.document(user_id)

        doc = user_ref.get()
        if not doc.exists:
            logger.warning(f"User not found for update: id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{user_id}' not found.",
            )

        # Only include non-None fields
        update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}

        if update_data:
            update_data["updated_at"] = datetime.now()
            user_ref.update(update_data)
            logger.info(
                f"Successfully updated user: id={user_id}, fields={list(update_data.keys())}"
            )

        # Fetch and return updated document
        updated_doc = user_ref.get()
        user_data = updated_doc.to_dict()
        user_data["id"] = updated_doc.id
        return User(**user_data)

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
