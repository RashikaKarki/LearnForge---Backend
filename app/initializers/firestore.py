import os

from dotenv import load_dotenv
from google.cloud.firestore import Client

load_dotenv()


def initialize_firestore():
    """Initializes Firestore client"""
    DATABASE_NAME = os.getenv("FIRESTORE_DATABASE_NAME", "(default)")

    db = Client(database=DATABASE_NAME)
    return db
