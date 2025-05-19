from fastapi import APIRouter, HTTPException # type: ignore
from pydantic import BaseModel, Field # type: ignore
from models.types import Item

router = APIRouter()

class UpdateDimensionsRequest(BaseModel):
    height: float = Field(..., ge=0)
    width: float = Field(..., ge=0)
    length: float = Field(..., ge=0)

@router.post("/{item_id}/update")
def update_item_dimensions(item_id: str, payload: UpdateDimensionsRequest):
    item = Item.objects(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.height = payload.height
    item.width = payload.width
    item.length = payload.length
    item.save()

    return {
        "item_id": str(item.id),
        "item_number": item.item_number,
        "height": item.height,
        "width": item.width,
        "length": item.length
    }

