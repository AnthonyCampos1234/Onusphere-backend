from pydantic import BaseModel

class TriggerRequest(BaseModel):
    order_id: str

class CreateBusinessAccount(BaseModel):
    business_name: str
    business_email: str
    full_name: str
    email: str
    password: str
    phone: str

class Login(BaseModel):
    email: str
    password: str

class EmailData(BaseModel):
    csv_file_path: str
    pdf_file_path: str
    email_body: str
