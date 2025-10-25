import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials

load_dotenv()

cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
cred = credentials.Certificate(cred_path)


def initialize_firebase():
    """Initializes Firebase app if not already initialized"""
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"projectId": os.getenv("FIREBASE_PROJECT_ID")})
