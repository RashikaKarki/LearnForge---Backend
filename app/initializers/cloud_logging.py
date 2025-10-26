import logging
import sys

from google.cloud import logging as gcp_logging


def setup_logging():
    """Setup logging with Cloud Logging fallback to console"""
    try:
        # Try to setup Google Cloud Logging
        client = gcp_logging.Client()
        client.setup_logging()
        logging.getLogger().setLevel(logging.INFO)
    except Exception as e:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        logging.getLogger().setLevel(logging.INFO)
