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

        if os.path.exists(cred_path):
            with open(cred_path) as f:
                cred_dict = json.load(f)
            cred = credentials.Certificate(cred_dict)

        else:
            try:
                cred_dict = json.loads(cred_path)
                cred = credentials.Certificate(cred_dict)

            except json.JSONDecodeError:
                cred = credentials.Certificate(cred_path)

        firebase_admin.initialize_app(cred)
