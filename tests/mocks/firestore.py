"""Centralized Firestore mock factories."""

from unittest.mock import MagicMock


class FirestoreMocks:
    """Reusable mock factories for Firestore operations."""

    @staticmethod
    def collection_empty():
        """Empty collection for create operations."""
        collection = MagicMock()
        
        # Mock document creation with auto-generated ID
        doc = MagicMock()
        doc.id = "auto_generated_id"
        doc.set = MagicMock()
        collection.document.return_value = doc
        
        # Mock where queries returning no results
        collection.where.return_value.limit.return_value.get.return_value = []
        
        return collection

    @staticmethod
    def collection_with_user(user_data):
        """Collection with existing user for query operations."""
        collection = MagicMock()
        
        # Mock document with user data
        doc = MagicMock()
        doc.to_dict.return_value = user_data
        
        # Mock where queries returning the user
        collection.where.return_value.limit.return_value.get.return_value = [doc]
        
        return collection

    @staticmethod
    def document_exists(doc_id, data):
        """Document that exists with given data."""
        doc = MagicMock()
        doc.exists = True
        doc.id = doc_id
        doc.to_dict.return_value = data
        return doc

    @staticmethod
    def document_not_found():
        """Document that doesn't exist."""
        doc = MagicMock()
        doc.exists = False
        return doc

    @staticmethod
    def mock_db_with_collection(collection):
        """Create mock database with specified collection."""
        db = MagicMock()
        db.collection.return_value = collection
        return db
