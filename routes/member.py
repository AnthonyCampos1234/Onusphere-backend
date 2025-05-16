from fastapi import APIRouter, Depends
from models.types import Member
from utils.dependencies import get_current_user

router = APIRouter()

@router.get("/me")
def get_current_user_info(current_user: Member = Depends(get_current_user)):
    return {
        "id": str(current_user.pk),
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "account_id": str(current_user.account.pk)
    }


@router.put("/me/update")
def update_current_user(update_data: dict, current_user: Member = Depends(get_current_user)):
    for field in ["name", "phone"]:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    current_user.save()
    return {"status": "success", "message": "Member profile updated successfully"}
