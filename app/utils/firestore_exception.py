from functools import wraps

from fastapi import HTTPException, status


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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}",
            ) from e

    return wrapper
