from datetime import datetime
from typing import List

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.mission import Mission, MissionCreate, MissionUpdate
from app.utils.firestore_exception import handle_firestore_exceptions


class MissionService:
    def __init__(self, db):
        self.db = db
        self.collection = db.collection("missions")

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

        updated_doc = doc_ref.get()
        return Mission(**updated_doc.to_dict())

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
    def get_missions_by_creator(
        self, creator_id: str, limit: int = 100
    ) -> List[Mission]:
        """Get all missions created by a specific user."""
        docs = (
            self.collection.where(filter=FieldFilter("creator_id", "==", creator_id))
            .limit(limit)
            .get()
        )
        return [Mission(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def get_public_missions(self, limit: int = 100, offset: int = 0) -> List[Mission]:
        """Get all public missions with pagination."""
        query = self.collection.where(
            filter=FieldFilter("is_public", "==", True)
        ).limit(limit)
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
    ) -> List[Mission]:
        """Get missions by creator filtered by visibility (public/private)."""
        docs = (
            self.collection.where(filter=FieldFilter("creator_id", "==", creator_id))
            .where(filter=FieldFilter("is_public", "==", is_public))
            .limit(limit)
            .get()
        )
        return [Mission(**doc.to_dict()) for doc in docs]
