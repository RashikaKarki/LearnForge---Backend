from datetime import datetime
import logging

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate
from app.models.user import UserEnrolledMissionCreate, UserEnrolledMissionUpdate
from app.utils.firestore_exception import handle_firestore_exceptions


logger = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(self, db, user_service=None):
        self.db = db
        self.collection = db.collection("enrollments")
        self.missions_collection = db.collection("missions")
        self.users_collection = db.collection("users")

        # UserService dependency for denormalized user subcollection
        if user_service is None:
            from app.services.user_service import UserService

            self.user_service = UserService(db)
        else:
            self.user_service = user_service

    def _generate_enrollment_id(self, user_id: str, mission_id: str) -> str:
        """Generate composite key for enrollment."""
        return f"{user_id}_{mission_id}"

    @handle_firestore_exceptions
    def create_enrollment(self, data: EnrollmentCreate) -> Enrollment:
        # Verify user exists
        user_doc = self.users_collection.document(data.user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID '{data.user_id}' not found.",
            )

        # Verify mission exists and get mission data for denormalization
        mission_doc = self.missions_collection.document(data.mission_id).get()
        if not mission_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{data.mission_id}' not found.",
            )

        mission_data = mission_doc.to_dict()

        # Check if enrollment already exists
        enrollment_id = self._generate_enrollment_id(data.user_id, data.mission_id)
        existing_doc = self.collection.document(enrollment_id).get()
        if existing_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already enrolled in this mission.",
            )

        enrollment_data = data.model_dump(mode="json")
        enrollment_data["id"] = enrollment_id
        enrollment_data["enrolled_at"] = datetime.today()
        enrollment_data["last_accessed_at"] = datetime.today()
        enrollment_data["completed"] = False
        enrollment_data["created_at"] = datetime.today()
        enrollment_data["updated_at"] = datetime.today()

        # Create in global enrollments collection
        self.collection.document(enrollment_id).set(enrollment_data)

        # Create in user's enrolled_missions subcollection (denormalized)
        user_enrolled_create = UserEnrolledMissionCreate(
            mission_id=data.mission_id,
            mission_title=mission_data.get("title", ""),
            mission_short_description=mission_data.get("short_description", ""),
            mission_skills=mission_data.get("skills", []),
            progress=data.progress,
            byte_size_checkpoints=mission_data.get("byte_size_checkpoints", []),
            completed_checkpoints=[],
            enrolled_at=enrollment_data["enrolled_at"],
            last_accessed_at=enrollment_data["last_accessed_at"],
            completed=False,
        )

        try:
            self.user_service.create_enrolled_mission(
                user_id=data.user_id, data=user_enrolled_create
            )
            logger.info(
                f"Successfully created enrollment '{enrollment_id}' for user '{data.user_id}' "
                f"in mission '{data.mission_id}' (dual-write to global and user subcollection)"
            )
        except Exception as e:
            logger.error(
                f"Failed to create enrolled mission in user subcollection for user '{data.user_id}' "
                f"and mission '{data.mission_id}'. Global enrollment created but user subcollection failed: {str(e)}",
                exc_info=True,
            )
            # Roll back global enrollment
            self.collection.document(enrollment_id).delete()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create enrollment: {str(e)}",
            ) from e

        return Enrollment(**enrollment_data)

    @handle_firestore_exceptions
    def get_enrollment(self, user_id: str, mission_id: str) -> Enrollment:
        enrollment_id = self._generate_enrollment_id(user_id, mission_id)
        doc = self.collection.document(enrollment_id).get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment not found for user '{user_id}' in mission '{mission_id}'.",
            )

        return Enrollment(**doc.to_dict())

    @handle_firestore_exceptions
    def get_enrollment_by_id(self, enrollment_id: str) -> Enrollment:
        doc = self.collection.document(enrollment_id).get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment with ID '{enrollment_id}' not found.",
            )

        return Enrollment(**doc.to_dict())

    @handle_firestore_exceptions
    def update_enrollment(
        self, user_id: str, mission_id: str, data: EnrollmentUpdate
    ) -> Enrollment:
        enrollment_id = self._generate_enrollment_id(user_id, mission_id)
        doc_ref = self.collection.document(enrollment_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment not found for user '{user_id}' in mission '{mission_id}'.",
            )

        update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
        if update_data:
            # Always update updated_at and last_accessed_at when updating enrollment
            update_data["updated_at"] = datetime.today()
            if "last_accessed_at" not in update_data:
                update_data["last_accessed_at"] = datetime.today()

            # Update global enrollments collection
            doc_ref.update(update_data)

            # Update user's enrolled_missions subcollection (denormalized)
            user_enrolled_update = UserEnrolledMissionUpdate(
                progress=data.progress,
                completed=data.completed,
                completed_checkpoints=data.completed_checkpoints,
                last_accessed_at=update_data["last_accessed_at"],
            )

            try:
                self.user_service.update_enrolled_mission(
                    user_id=user_id, mission_id=mission_id, data=user_enrolled_update
                )
                logger.info(
                    f"Successfully updated enrollment for user '{user_id}' in mission '{mission_id}' "
                    f"(dual-write to global and user subcollection)"
                )
            except Exception as e:
                logger.error(
                    f"Failed to update enrolled mission in user subcollection for user '{user_id}' "
                    f"and mission '{mission_id}'. Global enrollment updated but user subcollection failed: {str(e)}",
                    exc_info=True,
                )

        updated_doc = doc_ref.get()
        return Enrollment(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def delete_enrollment(self, user_id: str, mission_id: str) -> dict:
        enrollment_id = self._generate_enrollment_id(user_id, mission_id)
        doc_ref = self.collection.document(enrollment_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment not found for user '{user_id}' in mission '{mission_id}'.",
            )

        # Delete from global enrollments collection
        doc_ref.delete()

        try:
            self.user_service.delete_enrolled_mission(user_id=user_id, mission_id=mission_id)
            logger.info(
                f"Successfully deleted enrollment '{enrollment_id}' for user '{user_id}' "
                f"in mission '{mission_id}' (dual-delete from global and user subcollection)"
            )
        except Exception as e:
            logger.error(
                f"Failed to delete enrolled mission from user subcollection for user '{user_id}' "
                f"and mission '{mission_id}'. Global enrollment deleted but user subcollection failed: {str(e)}",
                exc_info=True,
            )
        return {"message": f"Enrollment '{enrollment_id}' deleted successfully."}

    @handle_firestore_exceptions
    def get_enrollments_by_user(self, user_id: str, limit: int = 100) -> list[Enrollment]:
        """Get all enrollments for a specific user."""
        docs = (
            self.collection.where(filter=FieldFilter("user_id", "==", user_id)).limit(limit).get()
        )
        return [Enrollment(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def get_enrollments_by_mission(self, mission_id: str, limit: int = 100) -> list[Enrollment]:
        """Get all enrollments for a specific mission."""
        docs = (
            self.collection.where(filter=FieldFilter("mission_id", "==", mission_id))
            .limit(limit)
            .get()
        )
        return [Enrollment(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def update_last_accessed(self, user_id: str, mission_id: str) -> Enrollment:
        """Update the last_accessed_at timestamp for an enrollment."""
        enrollment_id = self._generate_enrollment_id(user_id, mission_id)
        doc_ref = self.collection.document(enrollment_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment not found for user '{user_id}' in mission '{mission_id}'.",
            )

        update_data = {"last_accessed_at": datetime.today(), "updated_at": datetime.today()}

        # Update global enrollments collection
        doc_ref.update(update_data)

        # Update user's enrolled_missions subcollection (denormalized)
        user_enrolled_update = UserEnrolledMissionUpdate(last_accessed_at=datetime.today())

        try:
            self.user_service.update_enrolled_mission(
                user_id=user_id, mission_id=mission_id, data=user_enrolled_update
            )
        except Exception as e:
            logger.error(
                f"Failed to update last_accessed_at in user subcollection for user '{user_id}' "
                f"and mission '{mission_id}': {str(e)}",
                exc_info=True,
            )

        updated_doc = doc_ref.get()
        return Enrollment(**updated_doc.to_dict())
