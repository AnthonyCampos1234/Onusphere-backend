from datetime import datetime, timezone
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.account import Account
from models.order import Order, OrderItem
from models.item import Item
from scripts.truck_loader.services import find_items_without_dimensions_from_order

# Use test DB
TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(
        TEST_DB,
        host="mongodb://localhost:27017/" + TEST_DB,
        uuidRepresentation="standard"
    )
    yield
    Item.drop_collection()
    Account.drop_collection()
    Order.drop_collection()
    disconnect()

def test_find_items_without_dimensions_from_order():
    # Step 1: Create items
    item_with_dims = Item(item_number="1001", height=10, width=5, length=3).save()
    item_missing_dims = Item(item_number="1002", height=0, width=4, length=2).save()
    item_none_dims = Item(item_number="1003").save()

    # Step 2: Create order items
    oi1 = OrderItem(item=item_with_dims, number_pallets=1)
    oi2 = OrderItem(item=item_missing_dims, number_pallets=2)
    oi3 = OrderItem(item=item_none_dims, number_pallets=3)

    # Step 3: Create order
    order = Order(
        items=[oi1, oi2, oi3],
        order_date=datetime.now(timezone.utc),
        upcoming_shipment_times=["9am, 1pm"]
    ).save()

    # Step 4: Run the function
    missing = find_items_without_dimensions_from_order(order.id)

    # Step 5: Assertions
    assert "1002" in missing
    assert "1003" in missing
    assert "1001" not in missing
