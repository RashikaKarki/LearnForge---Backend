"""Application factory"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

from app.core.config import settings
from app.core.initializer import startup_handler
from app.core.set_middleware import setup_middleware
from app.core.set_routes import setup_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    await startup_handler(app)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    CUR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    AGENT_DIR = os.path.join(CUR_DIR, settings.AGENTS_DIR)

    app: FastAPI = get_fast_api_app(
        agents_dir=AGENT_DIR,
        web=True,
        allow_origins=settings.cors_origins,
        lifespan=lifespan,
    )

    # Set metadata
    app.title = settings.APP_TITLE
    app.description = settings.APP_DESCRIPTION

    # Setup middleware
    setup_middleware(app)

    # Setup routes
    setup_routes(app)

    return app
