from fastapi import FastAPI

from app.api import router as api_router


def setup_routes(app: FastAPI) -> None:
    """Register all application routes"""
    app.include_router(api_router, prefix="/api")
