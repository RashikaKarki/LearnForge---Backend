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
        doc.get = MagicMock(return_value=MagicMock(exists=False))
        collection.document.return_value = doc

        # Mock where queries returning no results
        where_mock = MagicMock()
        where_mock.get.return_value = []
        where_mock.limit.return_value.get.return_value = []
        collection.where.return_value = where_mock
        collection.order_by.return_value.get.return_value = []

        return collection

    @staticmethod
    def collection_with_item(item_data):
        """Collection with existing item for query operations."""
        collection = MagicMock()

        # Mock document with item data
        doc = MagicMock()
        doc.to_dict.return_value = item_data

        # Mock where queries returning the item
        collection.where.return_value.limit.return_value.get.return_value = [doc]
        collection.where.return_value.where.return_value.limit.return_value.get.return_value = [doc]

        return collection

    @staticmethod
    def collection_with_user(user_data):
        """Collection with existing user for query operations."""
        return FirestoreMocks.collection_with_item(user_data)

    @staticmethod
    def collection_with_items(items_data):
        """Collection with multiple items."""
        collection = MagicMock()

        # Mock documents with items data
        docs = [MagicMock(to_dict=MagicMock(return_value=item)) for item in items_data]

        # Mock queries returning the items
        collection.where.return_value.limit.return_value.get.return_value = docs
        collection.order_by.return_value.get.return_value = docs
        collection.limit.return_value.get.return_value = docs
        collection.get.return_value = docs

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

    @staticmethod
    def mock_db_with_subcollection(parent_collection, subcollection):
        """Create mock database with parent collection and subcollection."""
        db = MagicMock()

        # Parent collection returns a document that has a subcollection
        parent_doc = MagicMock()
        parent_doc.collection.return_value = subcollection
        parent_collection.document.return_value = parent_doc

        db.collection.return_value = parent_collection
        return db
