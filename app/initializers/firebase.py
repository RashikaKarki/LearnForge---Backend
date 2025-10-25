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
        
        # Check if the credential is a JSON string (from Secret Manager) or a file path
        if os.path.exists(cred_path):
            # It's a file path
            cred = credentials.Certificate(cred_path)
        else:
            # It's likely a JSON string from Secret Manager
            try:
                cred_dict = json.loads(cred_path)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                # Fallback to treating it as a file path
                cred = credentials.Certificate(cred_path)
        
        firebase_admin.initialize_app(
            cred, 
            {"projectId": os.getenv("FIREBASE_PROJECT_ID")}
        )
