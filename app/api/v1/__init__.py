from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.mission import router as mission_router
from .routes.mission_ally import router as mission_ally_router
from .routes.mission_commander import router as mission_commander_router
from .routes.session import router as session_router
from .routes.user import router as user_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(user_router, prefix="/user", tags=["user"])
router.include_router(session_router, prefix="/sessions", tags=["sessions"])
router.include_router(mission_router, prefix="/missions", tags=["missions"])
router.include_router(
    mission_commander_router, prefix="/mission-commander", tags=["mission-commander"]
)
router.include_router(mission_ally_router, prefix="/mission-ally", tags=["mission-ally"])
