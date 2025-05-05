from pydantic import BaseModel

class TriggerRequest(BaseModel):
    order_id: str
