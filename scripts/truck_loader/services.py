from typing import List
from bson import ObjectId
from models.order import Order

def find_items_without_dimensions_from_order(order_id) -> List:
    """
    Returns a list of item_numbers that are a part of the Order but
    do not have completed dimensions.
    """
    order = Order.objects(id=ObjectId(order_id)).first()

    if not order:
        raise ValueError(f"No order found with id {order_id}")
    
    missing_items = []

    for order_item in order.items:
        item = order_item.item
        if not item or not all([item.height, item.width, item.length]):
            missing_items.append(item.item_number if item else "Unknown Item")

    return missing_items
