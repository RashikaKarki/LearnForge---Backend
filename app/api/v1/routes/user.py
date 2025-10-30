from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.user import User, UserEnrolledMission
from app.services.user_service import UserService

router = APIRouter()


@router.get("/profile", response_model=User)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 100,
):
    """Get current user profile.

    Args:
        limit: Maximum number of enrolled missions to return (only if include_enrollments=True)
    """
    # Get user with enrolled missions (2 queries)
    user_service = UserService(db)
    basic_user = user_service.get_user(current_user.id)

    # Combine user data with enrolled missions
    user_dict = basic_user.model_dump()
    return User(**user_dict)


@router.get("/enrolled-missions", response_model=list[UserEnrolledMission])
async def get_user_enrolled_missions(
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 100,
):
    """
    Get all enrolled missions for the current user.

    Args:
        limit: Maximum number of enrolled missions to return

    Returns:
        List of UserEnrolledMission objects with mission details and progress
    """
    user_service = UserService(db)
    return user_service.get_enrolled_missions(current_user.id, limit=limit)
