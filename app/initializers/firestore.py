import json
import os

from dotenv import load_dotenv
from fastapi import Request
from google.cloud.firestore import Client
from google.oauth2 import service_account


load_dotenv()


def initialize_firestore():
    """Initializes Firestore client

    Handles credentials from:
    - File path (local development)
    - JSON string (Cloud Run --update-secrets)
    - Default credentials (Cloud Run service account)
    """
    database_id = os.getenv("FIRESTORE_DATABASE_ID", "(default)")
    cred_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Initialize with explicit credentials if provided
    if cred_value:
        if os.path.exists(cred_value):
            # File path - use it directly
            credentials = service_account.Credentials.from_service_account_file(cred_value)
            db = Client(database=database_id, credentials=credentials)
        else:
            # JSON string - parse and use
            try:
                cred_dict = json.loads(cred_value)
                credentials = service_account.Credentials.from_service_account_info(cred_dict)
                db = Client(database=database_id, credentials=credentials)
            except json.JSONDecodeError:
                db = Client(database=database_id)
    else:
        db = Client(database=database_id)

    return db


def get_db(request: Request):
    """FastAPI dependency to get Firestore database from app state"""
    return request.app.state.db
