from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
