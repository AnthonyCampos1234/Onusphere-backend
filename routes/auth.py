
from fastapi import APIRouter, HTTPException
from models.account import Account
from models.request_bodies import SignUp, Login
from utils.security import hash_password, verify_password
from utils.auth import create_access_token

router = APIRouter()

@router.post("/signup")
def signup(payload: SignUp):
    if Account.objects(email=payload.email).first():  # type: ignore
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(payload.password)
    account = Account(name=payload.name, email=payload.email, hashed_password=hashed_pw).save()
    token = create_access_token({"sub": str(account.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(payload: Login):
    account = Account.objects(email=payload.email).first()  # type: ignore
    if not account or not verify_password(payload.password, account.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(account.id)})
    return {"access_token": token, "token_type": "bearer"}
