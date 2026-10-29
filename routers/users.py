from fastapi import APIRouter, Depends
from dependencies import get_current_user, require_admin

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me")
def get_profile(user=Depends(get_current_user)):
    return user


@router.get("/admin")
def admin_profile(user=Depends(require_admin)):
    return {
        "message": "Admin access granted",
        "user_id": user["id"]
    }
