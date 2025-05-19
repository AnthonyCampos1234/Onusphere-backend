import uuid
import os 
import sys
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.types import Account, Customer, Order, OrderBatch, Item
from main import app
from mongoengine import connect, disconnect
import pytest

client = TestClient(app)

TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="function", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", uuidRepresentation='standard')

    # Ensure clean slate before each test
    Account.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    OrderBatch.drop_collection()
    Item.drop_collection()

    yield

    # Clean up again after test
    Account.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    OrderBatch.drop_collection()
    Item.drop_collection()

    disconnect()


def create_test_order_with_items(dimensions_list):
    """
    Create a test order with items based on dimension tuples.
    :param dimensions_list: List of tuples (height, width, length)
    :return: order object
    """
    account = Account(name="TestAcc", email=f"{uuid.uuid4().hex}@example.com", company_code=uuid.uuid4().hex).save()
    customer = Customer(name="MissingItemCustomer", email_domain="test.com", account=account).save()

    order_batches = []
    for i, (h, w, l) in enumerate(dimensions_list):
        item = Item(
            item_number=str(10000000 + i),
            height=h,
            width=w,
            length=l,
            special_instructions="",
            units_per_pallet=100
        ).save()
        batch = OrderBatch(item_id=item, number_pallets=1).save()
        order_batches.append(batch)

    order = Order(
        customer=customer,
        order_item_ids=order_batches,
        order_date=datetime.utcnow(),
        shipment_times=["7am"],
        status="processing",
        loading_instructions=None
    ).save()

    return order


def test_missing_items_none():
    order = create_test_order_with_items([
        (10, 20, 30),
        (5, 5, 5)
    ])

    res = client.get(f"/order/{order.id}/missing-items")
    assert res.status_code == 200
    data = res.json()
    assert data["order_id"] == str(order.id)
    assert data["missing_items"] == []


def test_missing_items_some():
    order = create_test_order_with_items([
        (0, 20, 30),
        (5, 0, 5),
        (5, 5, 0),
        (10, 10, 10)
    ])

    res = client.get(f"/order/{order.id}/missing-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data["missing_items"]) == 3
    for item in data["missing_items"]:
        assert item["height"] == 0 or item["width"] == 0 or item["length"] == 0


def test_missing_items_all():
    order = create_test_order_with_items([
        (0, 0, 0),
        (0, 0, 0)
    ])

    res = client.get(f"/order/{order.id}/missing-items")
    assert res.status_code == 200
    data = res.json()
    assert len(data["missing_items"]) == 2


def test_missing_items_invalid_order():
    res = client.get("/order/000000000000000000000000/missing-items")
    assert res.status_code == 404
    assert res.json()["detail"] == "Order not found"
