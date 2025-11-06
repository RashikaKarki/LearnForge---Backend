from datetime import datetime

from fastapi import HTTPException, status

from app.models.session_log import SessionLog, SessionLogCreate, SessionLogUpdate
from app.utils.firestore_exception import handle_firestore_exceptions


class SessionLogService:
    """Service for managing session logs in Firestore"""

    def __init__(self, db):
        self.db = db
        self.collection = db.collection("session_logs")

    @handle_firestore_exceptions
    def create_session(self, data: SessionLogCreate) -> SessionLog:
        """
        Create a new session log entry.

        Args:
            data: SessionLogCreate containing user_id

        Returns:
            SessionLog: Created session log with auto-generated session_id

        Example:
            >>> service = SessionLogService(db)
            >>> session = service.create_session(SessionLogCreate(user_id="user123"))
            >>> print(session.id)  # Auto-generated session ID
        """
        doc_ref = self.collection.document()

        # Create session log with auto-generated ID
        now = datetime.now()
        session_data = {
            **data.model_dump(mode="json"),
            "id": doc_ref.id,
            "status": "active",
            "mission_id": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }

        doc_ref.set(session_data)

        return SessionLog(**session_data)

    @handle_firestore_exceptions
    def get_session(self, session_id: str) -> SessionLog:
        """
        Retrieve a session log by session ID.

        Args:
            session_id: The unique session identifier

        Returns:
            SessionLog: The session log

        Raises:
            HTTPException: 404 if session not found
        """
        doc = self.collection.document(session_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        return SessionLog(**doc.to_dict())

    @handle_firestore_exceptions
    def update_session(self, session_id: str, data: SessionLogUpdate) -> SessionLog:
        """
        Update an existing session log.

        Args:
            session_id: The session ID to update
            data: SessionLogUpdate with fields to update

        Returns:
            SessionLog: Updated session log

        Raises:
            HTTPException: 404 if session not found
        """
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        # Build update data (only include non-None values)
        update_data = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}

        if update_data:
            update_data["updated_at"] = datetime.now()
            doc_ref.update(update_data)

        # Get updated document
        updated_doc = doc_ref.get()
        return SessionLog(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def mark_session_completed(self, session_id: str, mission_id: str | None = None) -> SessionLog:
        """
        Mark a session as completed.

        Args:
            session_id: The session ID to mark as completed
            mission_id: Optional mission ID created during this session

        Returns:
            SessionLog: Updated session log
        """
        update_data = SessionLogUpdate(
            status="completed", mission_id=mission_id, completed_at=datetime.now()
        )
        return self.update_session(session_id, update_data)

    @handle_firestore_exceptions
    def mark_session_error(self, session_id: str) -> SessionLog:
        """
        Mark a session as having encountered an error.

        Args:
            session_id: The session ID to mark as error

        Returns:
            SessionLog: Updated session log
        """
        update_data = SessionLogUpdate(status="error")
        return self.update_session(session_id, update_data)

    @handle_firestore_exceptions
    def mark_session_abandoned(self, session_id: str) -> SessionLog:
        """
        Mark a session as abandoned (user disconnected without completing).

        Args:
            session_id: The session ID to mark as abandoned

        Returns:
            SessionLog: Updated session log
        """
        update_data = SessionLogUpdate(status="abandoned")
        return self.update_session(session_id, update_data)

    @handle_firestore_exceptions
    def get_user_sessions(self, user_id: str, limit: int = 50) -> list[SessionLog]:
        """
        Get all sessions for a specific user.

        Args:
            user_id: The user ID
            limit: Maximum number of sessions to return (default: 50)

        Returns:
            list[SessionLog]: List of session logs
        """
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = (
            self.collection.where(filter=FieldFilter("user_id", "==", user_id))
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .get()
        )

        return [SessionLog(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def delete_session(self, session_id: str) -> dict:
        """
        Delete a session log (use sparingly, prefer marking as completed/abandoned).

        Args:
            session_id: The session ID to delete

        Returns:
            dict: Confirmation message

        Raises:
            HTTPException: 404 if session not found
        """
        doc_ref = self.collection.document(session_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID '{session_id}' not found.",
            )

        doc_ref.delete()
        return {"message": f"Session '{session_id}' deleted successfully."}
