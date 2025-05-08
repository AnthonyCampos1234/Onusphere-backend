from fastapi import APIRouter, HTTPException, Depends
from jose import jwt, JWTError
from bson import ObjectId

from models.account import Account
from models.request_bodies import Login, SignUp, TriggerRequest
from utils.auth import create_access_token, SECRET_KEY, ALGORITHM
from utils.security import hash_password, verify_password
from utils.dependencies import get_current_user

router = APIRouter()

order_id_holder = {"id": None}
truck_loader_response_holder = {"data": None}
pipeline_trigger_event = None

@router.get("/")
def read_root():
    return {"message": "API is running and waiting for email triggers."}

@router.post("/signup")
def signup(payload: SignUp):
    if Account.objects(email=payload.email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(payload.password)
    account = Account(name=payload.name, 
                      email=payload.email, 
                      hashed_password=hashed_pw).save()

    token = create_access_token({"sub": str(account.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(payload: Login):
    account = Account.objects(email=payload.email).first()
    if not account or not verify_password(payload.password, account.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": str(account.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/email-trigger")
def trigger_pipeline():
    pipeline_trigger_event.set()
    return {"status": "Pipeline trigger signal sent."}

@router.post("/pipeline-trigger")
def email_trigger(payload: TriggerRequest):
    order_id_holder["id"] = payload.order_id
    pipeline_trigger_event.set()
    return {"status": "Email event triggered.", "order_id": payload.order_id}

@router.get("/result")
def get_last_pipeline_result():
    return {"data": truck_loader_response_holder["data"]}

@router.get("/me")
def get_current_user_info(current_user: Account = Depends(get_current_user)):
    """Return information about the current logged-in user"""
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "company_name": current_user.company_name if hasattr(current_user, 'company_name') else None,
        "company_type": current_user.company_type if hasattr(current_user, 'company_type') else None,
        "phone": current_user.phone if hasattr(current_user, 'phone') else None,
        "job_title": current_user.job_title if hasattr(current_user, 'job_title') else None,
        "timezone": current_user.timezone if hasattr(current_user, 'timezone') else "America/New_York"
    }

@router.put("/me/update")
def update_current_user(update_data: dict, current_user: Account = Depends(get_current_user)):
    """Update information for the current logged-in user"""
    # Update allowed fields
    if 'name' in update_data:
        current_user.name = update_data.get('name')
    if 'company_name' in update_data:
        current_user.company_name = update_data.get('company_name')
    if 'company_type' in update_data:
        current_user.company_type = update_data.get('company_type')
    if 'phone' in update_data:
        current_user.phone = update_data.get('phone')
    if 'job_title' in update_data:
        current_user.job_title = update_data.get('job_title')
    if 'timezone' in update_data:
        current_user.timezone = update_data.get('timezone')
        
    # Save the updated user
    current_user.save()
    
    return {
        "status": "success",
        "message": "User profile updated successfully"
    }
