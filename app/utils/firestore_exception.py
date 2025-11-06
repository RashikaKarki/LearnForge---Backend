from functools import wraps
import logging

from fastapi import HTTPException, status


logger = logging.getLogger(__name__)


def handle_firestore_exceptions(func):
    """
    Decorator to catch Firestore exceptions and raise HTTPExceptions.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            # re-raise existing HTTPExceptions as-is
            raise
        except Exception as e:
            logger.exception(
                f"Unhandled exception in {func.__name__}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}",
            ) from e

    return wrapper
