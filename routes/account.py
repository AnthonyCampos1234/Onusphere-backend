from fastapi import APIRouter, Depends
from models.types import Account
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("/me")
def get_current_user_info(current_user: Account = Depends(get_current_user)):
    return {
        "id": str(current_user.pk),
        "name": current_user.name,
        "email": current_user.email,
        "company_name": getattr(current_user, "company_name", None),
        "phone": getattr(current_user, "phone", None),
        "job_title": getattr(current_user, "job_title", None),
        "timezone": getattr(current_user, "timezone", "America/New_York")
    }

@router.put("/me/update")
def update_current_user(update_data: dict, current_user: Account = Depends(get_current_user)):
    for field in ["name", "company_name", "phone", "job_title", "timezone"]:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    current_user.save()
    return {"status": "success", "message": "User profile updated successfully"}
