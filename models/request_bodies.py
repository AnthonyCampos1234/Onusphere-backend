from pydantic import BaseModel
from typing import Optional

class TriggerRequest(BaseModel):
    order_id: str

class CreateBusinessAccount(BaseModel):
    business_name: str
    business_email: str
    full_name: str
    email: str
    password: str
    phone: str

class AddNewMember(BaseModel):
    company_code: str
    full_name: str
    email: str
    password: str
    phone: str

class Login(BaseModel):
    email: str
    password: str
    remember_me: Optional[bool] = False

class EmailData(BaseModel):
    csv_file_path: str
    pdf_file_path: str
    email_body: str

class SendInvitation(BaseModel):
    email: str
    role: str = "member"
    message: Optional[str] = None

class ResendInvitation(BaseModel):
    invitation_id: str

class DeleteInvitation(BaseModel):
    invitation_id: str
