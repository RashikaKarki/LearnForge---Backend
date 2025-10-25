import os

from dotenv import load_dotenv
from google.cloud.firestore import Client

load_dotenv()


def initialize_firestore():
    """Initializes Firestore client"""
    database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")

    db = Client(database=database_id)
    return db
