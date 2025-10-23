from fastapi import Depends, FastAPI

from app.api import router as api_router
from app.utils.auth import verify_token


def setup_routes(app: FastAPI) -> None:
    """Register all application routes"""
    app.include_router(
        api_router, 
        prefix="/api", 
        dependencies=[Depends(verify_token)]
    )