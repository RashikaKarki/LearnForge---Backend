from fastapi import FastAPI

from app.initializers.firebase import initialize_firebase
from app.initializers.firestore import initialize_firestore


async def startup_handler(app: FastAPI):
    initialize_firebase()
    app.state.db = initialize_firestore()
