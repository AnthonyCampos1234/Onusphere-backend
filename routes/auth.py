from datetime import timezone
import string
import random
from os import name
from fastapi import APIRouter, HTTPException
from models.types import Account, Member
from models.request_bodies import AddNewMember, CreateBusinessAccount, Login
from utils.security import hash_password, verify_password
from utils.auth import create_access_token

router = APIRouter()

@router.post("/create-business-account")
def create_business_account(payload: CreateBusinessAccount):
    if Account.objects(email=payload.business_email).first():  # type: ignore
        raise HTTPException(status_code=400, detail="Account already exists")

    company_code = ''.join(random.choices(string.ascii_uppercase, k=6))

    account = Account(name=payload.business_name, 
                      email=payload.business_email,
                      company_code=company_code).save()

    hashed_pw = hash_password(payload.password)
    member = Member(account=account.pk,
                    name=payload.full_name, 
                    email=payload.email, 
                    phone=payload.phone,
                    hashed_password=hashed_pw,
                    role="admin").save()
    token = create_access_token({"sub": str(member.id)})

    return {"access_token": token, "token_type": "bearer"}

@router.post("/add-new-member")
def add_new_member(payload: AddNewMember):
    account = Account.objects(company_code=payload.company_code).first()  # type: ignore
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    existing_member = Member.objects(email=payload.email, account=account.pk).first()  # type: ignore
    if existing_member:
        raise HTTPException(status_code=400, detail="Member already exists")

    hashed_pw = hash_password(payload.password)
    member = Member(
        account=account.pk,
        name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hashed_pw,
        role="member"
    ).save()

    token = create_access_token({"sub": str(member.id)})

    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(payload: Login):
    member = Member.objects(email=payload.email).first()  # type: ignore

    if not member or not verify_password(payload.password, member.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(member.id)})

    return {"access_token": token, "token_type": "bearer"}




