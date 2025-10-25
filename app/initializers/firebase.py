import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv()


def initialize_firebase():
    """Initializes Firebase app if not already initialized"""
    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
        firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")

        # Load credentials
        if os.path.exists(cred_path):
            # It's a file path - load the JSON to get project_id from the credential itself
            with open(cred_path) as f:
                cred_dict = json.load(f)
            cred = credentials.Certificate(cred_dict)

            # Use project_id from the credential file if not provided via env var
            if not firebase_project_id:
                firebase_project_id = cred_dict.get("project_id")
        else:
            # Try to parse as JSON string (shouldn't happen with --set-secrets as file)
            try:
                cred_dict = json.loads(cred_path)
                cred = credentials.Certificate(cred_dict)

                # Use project_id from the credential if not provided via env var
                if not firebase_project_id:
                    firebase_project_id = cred_dict.get("project_id")
            except json.JSONDecodeError:
                # Fallback to treating it as a file path
                cred = credentials.Certificate(cred_path)

        # Initialize with explicit project ID
        if firebase_project_id:
            firebase_admin.initialize_app(cred, {"projectId": firebase_project_id})
        else:
            # Let Firebase Admin SDK infer from credentials
            firebase_admin.initialize_app(cred)
