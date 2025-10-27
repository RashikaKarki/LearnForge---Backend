import logging
from datetime import datetime

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.enrollment import EnrollmentCreate
from app.models.mission import Mission, MissionCreate, MissionUpdate
from app.models.user import UserEnrolledMissionUpdate
from app.services.enrollment_service import EnrollmentService
from app.utils.firestore_exception import handle_firestore_exceptions

logger = logging.getLogger(__name__)


class MissionService:
    def __init__(self, db, user_service=None):
        self.db = db
        self.collection = db.collection("missions")
        self.enrollments_collection = db.collection("enrollments")

        # UserService dependency for denormalized user subcollection
        if user_service is None:
            from app.services.user_service import UserService

            self.user_service = UserService(db)
        else:
            self.user_service = user_service

    @handle_firestore_exceptions
    def create_mission(self, data: MissionCreate) -> Mission:
        doc_ref = self.collection.document()
        mission_data = data.model_dump()
        mission_data["id"] = doc_ref.id
        mission_data["created_at"] = datetime.today()
        mission_data["updated_at"] = datetime.today()
        doc_ref.set(mission_data)
        return Mission(**mission_data)

    @handle_firestore_exceptions
    def create_mission_with_enrollment(
        self, data: MissionCreate, user_id: str
    ) -> tuple[Mission, any]:
        """
        Create a mission and automatically enroll the creator.

        Args:
            data: Mission creation data
            user_id: ID of the user creating the mission (will be auto-enrolled)

        Returns:
            Tuple of (Mission, Enrollment) objects

        Raises:
            HTTPException: If mission or enrollment creation fails
        """
        # Create the mission first
        mission = self.create_mission(data)

        try:
            # Auto-enroll the creator in the mission
            enrollment_service = EnrollmentService(self.db)
            enrollment_data = EnrollmentCreate(user_id=user_id, mission_id=mission.id, progress=0.0)
            enrollment = enrollment_service.create_enrollment(enrollment_data)

            return mission, enrollment

        except Exception as e:
            # If enrollment fails, delete the created mission to maintain consistency
            try:
                self.delete_mission(mission.id)
            except Exception:
                pass  # Best effort cleanup

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create enrollment: {str(e)}",
            ) from e

    @handle_firestore_exceptions
    def get_mission(self, mission_id: str) -> Mission:
        doc = self.collection.document(mission_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{mission_id}' not found.",
            )
        return Mission(**doc.to_dict())

    @handle_firestore_exceptions
    def update_mission(self, mission_id: str, data: MissionUpdate) -> Mission:
        doc_ref = self.collection.document(mission_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{mission_id}' not found.",
            )

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_data:
            update_data["updated_at"] = datetime.today()
            doc_ref.update(update_data)

            if any(key in update_data for key in ["title", "short_description", "skills"]):
                self._propagate_mission_updates(mission_id, update_data)

        updated_doc = doc_ref.get()
        return Mission(**updated_doc.to_dict())

    def _propagate_mission_updates(self, mission_id: str, update_data: dict) -> None:
        """Propagate mission metadata updates to all enrolled users' subcollections.

        Args:
            mission_id: The mission's ID
            update_data: Mission fields that were updated
        """
        # Get all enrollments for this mission
        enrollments = self.enrollments_collection.where(
            filter=FieldFilter("mission_id", "==", mission_id)
        ).get()

        enrollments_list = list(enrollments)
        logger.info(
            f"Propagating mission updates for mission '{mission_id}' to {len(enrollments_list)} enrolled users. "
            f"Fields updated: {', '.join(update_data.keys())}"
        )

        success_count = 0
        error_count = 0

        # For each enrolled user, update their denormalized mission data
        for enrollment_doc in enrollments_list:
            enrollment_data = enrollment_doc.to_dict()
            user_id = enrollment_data.get("user_id")

            if not user_id:
                logger.warning(
                    f"Skipping enrollment '{enrollment_doc.id}' for mission '{mission_id}': "
                    f"missing user_id"
                )
                error_count += 1
                continue

            # Construct UserEnrolledMissionUpdate with only mission metadata fields
            user_update_data = UserEnrolledMissionUpdate()

            if "title" in update_data:
                user_update_data.mission_title = update_data["title"]
            if "short_description" in update_data:
                user_update_data.mission_short_description = update_data["short_description"]
            if "skills" in update_data:
                user_update_data.mission_skills = update_data["skills"]

            # Update the user's enrolled mission
            try:
                self.user_service.update_enrolled_mission(
                    user_id=user_id, mission_id=mission_id, data=user_update_data
                )
                success_count += 1
            except HTTPException as e:
                # If user's enrolled mission not found, skip (edge case)
                logger.warning(
                    f"Failed to update enrolled mission for user '{user_id}' and mission '{mission_id}': "
                    f"{e.detail}. This may indicate data inconsistency between enrollments and user subcollections."
                )
                error_count += 1
            except Exception as e:
                logger.error(
                    f"Unexpected error updating enrolled mission for user '{user_id}' and mission '{mission_id}': "
                    f"{str(e)}",
                    exc_info=True,
                )
                error_count += 1

        logger.info(
            f"Mission update propagation completed for mission '{mission_id}'. "
            f"Success: {success_count}, Errors: {error_count}"
        )

    @handle_firestore_exceptions
    def delete_mission(self, mission_id: str) -> dict:
        doc_ref = self.collection.document(mission_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{mission_id}' not found.",
            )

        # Delete all checkpoints subcollection
        checkpoints = doc_ref.collection("checkpoints").get()
        for checkpoint in checkpoints:
            checkpoint.reference.delete()

        doc_ref.delete()
        return {"message": f"Mission '{mission_id}' deleted successfully."}

    @handle_firestore_exceptions
    def get_missions_by_creator(self, creator_id: str, limit: int = 100) -> list[Mission]:
        """Get all missions created by a specific user."""
        docs = (
            self.collection.where(filter=FieldFilter("creator_id", "==", creator_id))
            .limit(limit)
            .get()
        )
        return [Mission(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def get_public_missions(self, limit: int = 100, offset: int = 0) -> list[Mission]:
        """Get all public missions with pagination."""
        query = self.collection.where(filter=FieldFilter("is_public", "==", True)).limit(limit)
        if offset > 0:
            docs = list(
                self.collection.where(filter=FieldFilter("is_public", "==", True))
                .limit(offset)
                .get()
            )
            if docs:
                query = query.start_after(docs[-1])

        docs = query.get()
        return [Mission(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def get_missions_by_creator_and_visibility(
        self, creator_id: str, is_public: bool, limit: int = 100
    ) -> list[Mission]:
        """Get missions by creator filtered by visibility (public/private)."""
        docs = (
            self.collection.where(filter=FieldFilter("creator_id", "==", creator_id))
            .where(filter=FieldFilter("is_public", "==", is_public))
            .limit(limit)
            .get()
        )
        return [Mission(**doc.to_dict()) for doc in docs]
