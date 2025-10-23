"""Middleware registration"""
from fastapi import FastAPI

from app.middleware.firebase_middleware import FirebaseAuthMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Register all application middleware"""
    app.add_middleware(FirebaseAuthMiddleware)