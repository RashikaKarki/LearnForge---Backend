from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/profile")
async def get_profile(request: Request):
    user = request.state.current_user

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
