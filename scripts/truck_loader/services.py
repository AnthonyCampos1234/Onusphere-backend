from typing import List
from bson import ObjectId
from models.types import Order

def find_items_without_dimensions_from_order(order_id) -> List[str]:
    """
    Returns a list of item_numbers that are a part of the Order but
    do not have completed dimensions.
    """
    order = Order.objects(id=ObjectId(order_id)).first()

    if not order:
        raise ValueError(f"No order found with id {order_id}")
    
    missing_items = []

    for order_batch in order.order_item_ids:
        for item in order_batch.item_ids:
            if not item or not all([item.height > 0, item.width > 0, item.length > 0]):
                missing_items.append(item.item_number if item else "Unknown Item")

    return missing_items
