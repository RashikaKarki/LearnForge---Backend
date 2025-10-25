"""Authentication dependencies for route handlers"""

from fastapi import Depends, HTTPException, Request, status

from app.models.user import User


def get_current_user(request: Request) -> User:
    """
    Get the current authenticated user.

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: 401 if user is not authenticated
    """
    user = getattr(request.state, "current_user", None)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(request: Request) -> User | None:
    """
    Get the current user if authenticated, None otherwise.

    Returns:
        User | None: The authenticated user object or None
    """
    return getattr(request.state, "current_user", None)
