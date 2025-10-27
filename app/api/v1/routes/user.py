from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.user import User, UserEnrolledMission
from app.services.user_service import UserService

router = APIRouter()


@router.get("/profile", response_model=User)
async def get_profile(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
    include_enrollments: bool = False,
    limit: int = 100,
):
    """Get current user profile.
    
    Args:
        include_enrollments: If True, includes enrolled missions (2 queries).
                            If False, returns basic user info only (1 query, faster).
        limit: Maximum number of enrolled missions to return (only if include_enrollments=True)
    """
    if include_enrollments:
        # Get user with enrolled missions (2 queries)
        user_service = UserService(db)
        basic_user = user_service.get_user(user.id)
        enrolled_missions = user_service.get_enrolled_missions(user.id, limit=limit)
        
        # Combine user data with enrolled missions
        user_dict = basic_user.model_dump()
        user_dict["enrolled_missions"] = enrolled_missions
        return User(**user_dict)
    else:
        # Return basic user info (no additional query needed)
        return user

@router.get("/enrolled-missions", response_model=list[UserEnrolledMission])
async def get_enrolled_missions(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 100,
):
    """Get all enrolled missions for the current user."""
    user_service = UserService(db)
    return user_service.get_enrolled_missions(user.id, limit=limit)
