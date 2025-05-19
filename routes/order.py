from models.types import Order
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/{order_id}/missing-items")
def get_items_with_missing_dimensions(order_id: str):
    order = Order.objects(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    missing_items = []

    for batch in order.order_item_ids:
        item = batch.item_id
        if (
            item.height == 0 or
            item.width == 0 or
            item.length == 0
        ):
            missing_items.append({
                "item_id": str(item.id),
                "item_number": item.item_number,
                "height": item.height,
                "width": item.width,
                "length": item.length
            })

    return {
        "order_id": str(order.id),
        "missing_items": missing_items
    }
