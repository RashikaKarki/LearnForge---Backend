"""Middleware registration"""

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.firebase_session_middleware import FirebaseSessionMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Register all application middleware"""

    # Add CORS middleware with credentials support for session cookies
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,  # Required for cookies to work
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Add Firebase session authentication middleware
    app.add_middleware(FirebaseSessionMiddleware)
