from app.services.firebase import initialize_firebase

async def startup_handler():
    initialize_firebase()