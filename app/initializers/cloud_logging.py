import logging
import sys

from google.cloud import logging as gcp_logging

from app.core.config import settings


def setup_logging():
    """Setup logging with Cloud Logging fallback to console"""
    try:
        # Try to setup Google Cloud Logging
        client = gcp_logging.Client()
        client.setup_logging()
        logging.getLogger().setLevel(logging.INFO)

        allowed_cors = settings.cors_origins
        logging.debug(f"Allowed CORS origins: {allowed_cors}")
    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        logging.getLogger().setLevel(logging.INFO)
