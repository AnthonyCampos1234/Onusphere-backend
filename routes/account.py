from fastapi import APIRouter, Depends, HTTPException
from models.types import Account, Member
from utils.dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Models for request/response
class UserSettings(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: str

class CompanySettings(BaseModel):
    name: str
    email: str
    company_code: str

class MemberResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    date_created: str

# Get current user settings
@router.get("/me/settings")
def get_user_settings(current_user: Member = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role
    }

# Update current user settings
@router.put("/me/settings")
def update_user_settings(settings: UserSettings, current_user: Member = Depends(get_current_user)):
    current_user.name = settings.name
    current_user.phone = settings.phone
    current_user.save()
    return settings

# Get company settings
@router.get("/account/settings")
def get_company_settings(current_user: Member = Depends(get_current_user)):
    account = Account.objects(id=current_user.account.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {
        "name": account.name,
        "email": account.email,
        "company_code": account.company_code
    }

# Update company settings
@router.put("/account/settings")
def update_company_settings(settings: CompanySettings, current_user: Member = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update company settings")
    
    account = Account.objects(id=current_user.account.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account.name = settings.name
    account.email = settings.email
    account.save()
    
    return settings

# Get all members
@router.get("/members")
def get_members(current_user: Member = Depends(get_current_user)):
    members = Member.objects(account=current_user.account.id)
    return [
        {
            "id": str(member.id),
            "name": member.name,
            "email": member.email,
            "phone": member.phone,
            "role": member.role,
            "date_created": member.date_created.isoformat()
        }
        for member in members
    ] 