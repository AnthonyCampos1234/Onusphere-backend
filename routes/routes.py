from fastapi import APIRouter, HTTPException

from models.account import Account
from models.request_bodies import Login, SignUp, TriggerRequest
from utils.auth import create_access_token
from utils.security import hash_password, verify_password

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
