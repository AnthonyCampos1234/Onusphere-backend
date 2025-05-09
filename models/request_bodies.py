from pydantic import BaseModel

class TriggerRequest(BaseModel):
    order_id: str

class SignUp(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

class EmailData(BaseModel):
    csv_file_path: str
    pdf_file_path: str
    email_body: str