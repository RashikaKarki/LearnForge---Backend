from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.user import router as user_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(user_router, prefix="/user", tags=["user"])
