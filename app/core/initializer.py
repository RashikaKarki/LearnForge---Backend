import json
import os
from tempfile import NamedTemporaryFile

from fastapi import FastAPI

from app.initializers.cloud_logging import setup_logging
from app.initializers.firebase import initialize_firebase
from app.initializers.firestore import initialize_firestore


async def startup_handler(app: FastAPI):
    # Normalize GOOGLE_APPLICATION_CREDENTIALS for libraries that expect a file path
    # If the env var contains inline JSON, write it to a temp file and point the env var to it
    creds_value = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_value and not os.path.exists(creds_value):
        try:
            json.loads(creds_value)
        except Exception:
            pass
        else:
            with NamedTemporaryFile(mode="w", delete=False, prefix="gcp-sa-", suffix=".json") as tf:
                tf.write(creds_value)
                tf.flush()
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tf.name

    initialize_firebase()
    app.state.db = initialize_firestore()
    setup_logging()
