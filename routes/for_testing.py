from fastapi import APIRouter, HTTPException, Request
from models.account import Account
from models.request_bodies import TriggerRequest
from threading import Event
from shared_state import pipeline_trigger_event, email_data

router = APIRouter()

@router.post("/email-trigger")
async def trigger_pipeline(request: Request):
    payload = await request.json()
    email = request.headers.get("email")
    if email:
        account = Account.objects(email=email).first()  # type: ignore
        if account:
            email_data = payload
            return {"status": "Pipeline triggered"}
    raise HTTPException(status_code=400, detail="Email header missing or invalid")

@router.post("/pipeline-trigger")
def email_trigger(payload: TriggerRequest):
    pipeline_trigger_event = Event()
    return {"status": "Email event triggered", "order_id": payload.order_id}
