from datetime import datetime

from fastapi import HTTPException, status

from app.models.checkpoint import Checkpoint, CheckpointCreate, CheckpointUpdate
from app.utils.firestore_exception import handle_firestore_exceptions


class CheckpointService:
    def __init__(self, db):
        self.db = db
        self.missions_collection = db.collection("missions")

    def _get_checkpoints_collection(self, mission_id: str):
        """Get the checkpoints subcollection for a specific mission."""
        return self.missions_collection.document(mission_id).collection("checkpoints")

    @handle_firestore_exceptions
    def create_checkpoint(self, mission_id: str, data: CheckpointCreate) -> Checkpoint:
        # Verify mission exists
        mission_doc = self.missions_collection.document(mission_id).get()
        if not mission_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission with ID '{mission_id}' not found.",
            )

        checkpoints_col = self._get_checkpoints_collection(mission_id)
        doc_ref = checkpoints_col.document()

        checkpoint_data = data.model_dump()
        checkpoint_data["id"] = doc_ref.id
        checkpoint_data["mission_id"] = mission_id
        checkpoint_data["content"] = ""  # Default empty content
        checkpoint_data["sources"] = {}  # Default empty sources
        checkpoint_data["quiz_questions"] = []  # Default empty quiz questions
        checkpoint_data["created_at"] = datetime.today()

        doc_ref.set(checkpoint_data)
        return Checkpoint(**checkpoint_data)

    @handle_firestore_exceptions
    def get_checkpoint(self, mission_id: str, checkpoint_id: str) -> Checkpoint:
        checkpoints_col = self._get_checkpoints_collection(mission_id)
        doc = checkpoints_col.document(checkpoint_id).get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkpoint with ID '{checkpoint_id}' not found in mission '{mission_id}'.",
            )

        return Checkpoint(**doc.to_dict())

    @handle_firestore_exceptions
    def get_all_checkpoints(self, mission_id: str) -> list[Checkpoint]:
        """Get all checkpoints for a mission, ordered by 'order' field."""
        checkpoints_col = self._get_checkpoints_collection(mission_id)
        docs = checkpoints_col.order_by("order").get()
        return [Checkpoint(**doc.to_dict()) for doc in docs]

    @handle_firestore_exceptions
    def update_checkpoint(
        self, mission_id: str, checkpoint_id: str, data: CheckpointUpdate
    ) -> Checkpoint:
        checkpoints_col = self._get_checkpoints_collection(mission_id)
        doc_ref = checkpoints_col.document(checkpoint_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkpoint with ID '{checkpoint_id}' not found in mission '{mission_id}'.",
            )

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if update_data:
            doc_ref.update(update_data)

        updated_doc = doc_ref.get()
        return Checkpoint(**updated_doc.to_dict())

    @handle_firestore_exceptions
    def delete_checkpoint(self, mission_id: str, checkpoint_id: str) -> dict:
        checkpoints_col = self._get_checkpoints_collection(mission_id)
        doc_ref = checkpoints_col.document(checkpoint_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkpoint with ID '{checkpoint_id}' not found in mission '{mission_id}'.",
            )

        doc_ref.delete()
        return {"message": f"Checkpoint '{checkpoint_id}' deleted successfully."}

    @handle_firestore_exceptions
    def reorder_checkpoints(self, mission_id: str, checkpoint_orders: dict) -> list[Checkpoint]:
        """
        Update the order of multiple checkpoints.

        Args:
            mission_id: The mission ID
            checkpoint_orders: Dict mapping checkpoint_id to new order value

        Returns:
            List of updated checkpoints
        """
        checkpoints_col = self._get_checkpoints_collection(mission_id)

        # Update each checkpoint's order
        for checkpoint_id, new_order in checkpoint_orders.items():
            doc_ref = checkpoints_col.document(checkpoint_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_ref.update({"order": new_order})

        # Return updated list
        return self.get_all_checkpoints(mission_id)
