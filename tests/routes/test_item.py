import os
import sys
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.types import Account, Customer, Order, OrderBatch, Item
from main import app
from mongoengine import connect, disconnect

client = TestClient(app)

TEST_DB = "customer_item_test_db"

@pytest.fixture(scope="function", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", uuidRepresentation='standard')

    Account.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    OrderBatch.drop_collection()
    Item.drop_collection()

    yield

    Account.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    OrderBatch.drop_collection()
    Item.drop_collection()
    disconnect()


def create_test_order_with_items(dimensions_list):
    account = Account(name="TestAcc", email=f"{uuid.uuid4().hex}@example.com", company_code=uuid.uuid4().hex).save()
    customer = Customer(name="UpdateItemCustomer", email_domain="test.com", account=account).save()

    order_batches = []
    for i, (h, w, l) in enumerate(dimensions_list):
        item = Item(
            item_number=str(20000000 + i),
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
        shipment_times=["8am"],
        status="processing",
        loading_instructions=None
    ).save()

    return order


def test_update_item_dimensions_success():
    order = create_test_order_with_items([(0, 0, 0)])
    item = order.order_item_ids[0].item_id

    res = client.post(
        f"/item/{item.id}/update",
        json={"height": 10.5, "width": 5.0, "length": 3.2}
    )
    assert res.status_code == 200

    data = res.json()
    assert data["item_id"] == str(item.id)
    assert data["height"] == 10.5
    assert data["width"] == 5.0
    assert data["length"] == 3.2

    item.reload()
    assert item.height == 10.5
    assert item.width == 5.0
    assert item.length == 3.2


def test_update_item_dimensions_invalid_item_id():
    res = client.post(
        "/item/000000000000000000000000/update",
        json={"height": 10, "width": 10, "length": 10}
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Item not found"


def test_update_item_dimensions_invalid_payload():
    order = create_test_order_with_items([(0, 0, 0)])
    item = order.order_item_ids[0].item_id

    # Try to update with invalid negative height
    res = client.post(
        f"/item/{item.id}/update",
        json={"height": -1, "width": 5, "length": 5}
    )

    assert res.status_code == 422
    error_data = res.json()
    assert error_data["detail"][0]["msg"] == "ensure this value is greater than or equal to 0"
    assert error_data["detail"][0]["loc"][-1] == "height"

