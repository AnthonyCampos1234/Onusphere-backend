from datetime import datetime, timezone
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.types import Account, Customer, Order, OrderBatch, Item
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
    account = Account(
    name="Test Account",
    email="test@account.com",
    company_code="ABC123"
    ).save()

    customer = Customer(
        account=account,
        name="Test Customer",
        email_domain="customer.com"
    ).save()

    item_with_dims = Item(
        item_number="1001",
        height=10, width=5, length=3,
        special_instructions="Standard",
        description="Test Item with dimensions",
        units_per_pallet=50
    ).save()

    item_missing_dims = Item(
        item_number="1002",
        height=0, width=4, length=2,
        special_instructions="Fragile",
        description="Test Item with zero height",
        units_per_pallet=30
    ).save()

    item_none_dims = Item(
        item_number="1003",
        height=0, width=0, length=0,
        special_instructions="N/A",
        description="Incomplete Item",
        units_per_pallet=0
    ).save()

    oi1 = OrderBatch(item_ids=[item_with_dims], number_pallets=1, order_date=datetime.now().date()).save()
    oi2 = OrderBatch(item_ids=[item_missing_dims], number_pallets=2, order_date=datetime.now().date()).save()
    oi3 = OrderBatch(item_ids=[item_none_dims], number_pallets=3, order_date=datetime.now().date()).save()

    order = Order(
        customer=customer, 
        order_item_ids=[oi1, oi2, oi3],
        order_date=datetime.now().date(),
        shipment_times=["9am", "1pm"],
        status="processing"
    ).save()

    missing = find_items_without_dimensions_from_order(order.id)

    assert "1002" in missing
    assert "1003" in missing
    assert "1001" not in missing

