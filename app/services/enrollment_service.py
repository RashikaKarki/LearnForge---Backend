from datetime import datetime

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.enrollment import Enrollment, EnrollmentCreate, EnrollmentUpdate
from app.utils.firestore_exception import handle_firestore_exceptions


class EnrollmentService:
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("enrollments")
        self.missions_collection = db.collection("missions")
        self.users_collection = db.collection("users")

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

        # Verify mission exists
        mission_doc = self.missions_collection.document(data.mission_id).get()
        if not mission_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{data.mission_id}' not found.",
            )

        # Check if enrollment already exists
        enrollment_id = self._generate_enrollment_id(data.user_id, data.mission_id)
        existing_doc = self.collection.document(enrollment_id).get()
        if existing_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already enrolled in this mission.",
            )

        enrollment_data = data.model_dump()
        enrollment_data["id"] = enrollment_id
        enrollment_data["enrolled_at"] = datetime.today()
        enrollment_data["last_accessed_at"] = datetime.today()
        enrollment_data["updated_at"] = datetime.today()

        self.collection.document(enrollment_id).set(enrollment_data)
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

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_data:
            # Always update last_accessed_at when updating enrollment
            if "last_accessed_at" not in update_data:
                update_data["last_accessed_at"] = datetime.today()
            doc_ref.update(update_data)

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

        doc_ref.delete()
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

        doc_ref.update({"last_accessed_at": datetime.today()})
        updated_doc = doc_ref.get()
        return Enrollment(**updated_doc.to_dict())
