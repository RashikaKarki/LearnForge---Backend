from fastapi import APIRouter, Depends

from app.utils.auth import verify_token

router = APIRouter()


@router.get("/profile")
async def get_profile(user=Depends(verify_token)):
    return {
        "uid": user["uid"], 
        "email": user.get("email"), 
        "name": user.get("name"), 
        "picture": user.get("picture")}
