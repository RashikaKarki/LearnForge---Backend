import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials


load_dotenv()


def initialize_firebase():
    """Initializes Firebase app if not already initialized"""
    if not firebase_admin._apps:
        cred_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase_key.json")

        # Determine if it's a file path or JSON content
        if os.path.exists(cred_value):
            # It's a file path - use it directly
            cred = credentials.Certificate(cred_value)
        else:
            # It's JSON content - parse and use directly
            try:
                cred_dict = json.loads(cred_value)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                raise

        firebase_admin.initialize_app(cred)
