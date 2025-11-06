from datetime import datetime

from fastapi import HTTPException, status

from app.models.enrollment_session_log import (
    EnrollmentSessionLog,
    EnrollmentSessionLogCreate,
    EnrollmentSessionLogUpdate,
)
from app.utils.firestore_exception import handle_firestore_exceptions


class EnrollmentSessionLogService:
    """Service for managing enrollment session logs in Firestore"""

    def __init__(self, db):
        self.db = db
        self.collection = db.collection("enrollment_session_logs")

    @handle_firestore_exceptions
    def create_session_log(self, data: EnrollmentSessionLogCreate) -> EnrollmentSessionLog:
        """
        Create a new enrollment session log entry.

        Args:
            data: EnrollmentSessionLogCreate containing enrollment_id, user_id, mission_id

        Returns:
            EnrollmentSessionLog: Created session log with auto-generated id
        """
        doc_ref = self.collection.document()

        now = datetime.now()
        session_data = {
            **data.model_dump(mode="json"),
            "id": doc_ref.id,
            "status": "created",
            "created_at": now,
            "updated_at": now,
            "started_at": None,
            "completed_at": None,
        }

        doc_ref.set(session_data)

        return EnrollmentSessionLog(**session_data)

    @handle_firestore_exceptions
    def get_session_log(self, session_log_id: str) -> EnrollmentSessionLog:
        """
        Retrieve an enrollment session log by ID.

        Args:
            session_log_id: The unique session log identifier

        Returns:
            EnrollmentSessionLog: The session log

        Raises:
            HTTPException: 404 if session log not found
        """
        doc = self.collection.document(session_log_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment session log with ID '{session_log_id}' not found.",
            )

        return EnrollmentSessionLog(**doc.to_dict())

    @handle_firestore_exceptions
    def get_session_log_by_user_and_enrollment_and_mission(
        self, user_id: str, enrollment_id: str, mission_id: str
    ) -> EnrollmentSessionLog | None:
        """
        Retrieve an enrollment session log by user_id, enrollment_id, and mission_id.

        Args:
            user_id: The user ID
            enrollment_id: The enrollment ID (Firestore document ID)
            mission_id: The mission ID

        Returns:
            EnrollmentSessionLog or None if not found
        """
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = (
            self.collection.where(filter=FieldFilter("user_id", "==", user_id))
            .where(filter=FieldFilter("enrollment_id", "==", enrollment_id))
            .where(filter=FieldFilter("mission_id", "==", mission_id))
            .limit(1)
            .get()
        )

        for doc in docs:
            return EnrollmentSessionLog(**doc.to_dict())

        return None

    @handle_firestore_exceptions
    def update_session_log(
        self, session_log_id: str, data: EnrollmentSessionLogUpdate
    ) -> EnrollmentSessionLog:
        """
        Update an existing enrollment session log.

        Args:
            session_log_id: The session log ID to update
            data: EnrollmentSessionLogUpdate with fields to update

        Returns:
            EnrollmentSessionLog: Updated session log

        Raises:
            HTTPException: 404 if session log not found
        """
        doc_ref = self.collection.document(session_log_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Enrollment session log with ID '{session_log_id}' not found.",
            )

        update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}

        if update_data:
            update_data["updated_at"] = datetime.now()
            doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return EnrollmentSessionLog(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def mark_session_started(self, session_log_id: str) -> EnrollmentSessionLog:
        """
        Mark an enrollment session as started.

        Args:
            session_log_id: The session log ID to mark as started

        Returns:
            EnrollmentSessionLog: Updated session log
        """
        now = datetime.now()
        update_data = EnrollmentSessionLogUpdate(status="started", started_at=now)
        return self.update_session_log(session_log_id, update_data)

    @handle_firestore_exceptions
    def mark_session_completed(self, session_log_id: str) -> EnrollmentSessionLog:
        """
        Mark an enrollment session as completed.

        Args:
            session_log_id: The session log ID to mark as completed

        Returns:
            EnrollmentSessionLog: Updated session log
        """
        now = datetime.now()
        update_data = EnrollmentSessionLogUpdate(status="completed", completed_at=now)
        return self.update_session_log(session_log_id, update_data)
