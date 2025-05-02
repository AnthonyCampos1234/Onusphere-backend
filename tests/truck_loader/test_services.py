import os
import sys
import tempfile
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.item import Item
from scripts.truck_loader.ingestion import parse_csv
from scripts.truck_loader.services import find_new_items, store_customer_order_in_db

# Use test DB
TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
    connect(
        TEST_DB,
        host="mongodb://localhost:27017/" + TEST_DB,
        uuidRepresentation="standard"
    )
    yield
    Item.drop_collection()
    Customer.drop_collection()
    CustomerOrder.drop_collection()
    disconnect()

def test_find_new_items():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("Item,Quantity\n")
        tmp.write("123,5\n")
        tmp.write("456,10\n")
        tmp_path = tmp.name

    try:
        df = parse_csv(tmp_path)
    finally:
        os.remove(tmp_path)

    Item(item_number="123").save()
    Item(item_number="456").save()
    Item(item_number="789").save()  # not in CSV

    missing_items = find_new_items(df)

    assert isinstance(missing_items, list)
    assert "789" in missing_items
    assert "123" not in missing_items
    assert "456" not in missing_items

from models.customer import Customer
from models.customer_order import CustomerOrder
import pandas as pd
from types import SimpleNamespace

def test_store_customer_order_in_db():
    # Step 1: Create and save test items
    Item(item_number="1001").save()
    Item(item_number="1002").save()

    # Step 2: Create a fake receipt object
    receipt = SimpleNamespace(
        customer_id="Test Customer",
        date_ordered="01/01/24",
        order_details=pd.DataFrame({
            "Item": ["1001", "1002"],
            "Quantity": [5, 10]
        })
    )

    # Step 3: Call the function
    store_customer_order_in_db(receipt)

    # Step 4: Assertions
    assert CustomerOrder.objects.count() == 1
    saved_order = CustomerOrder.objects.first()

    assert saved_order.customer.name == "Test Customer"
    assert len(saved_order.item) == 2
    assert saved_order.item[0].item_number in ["1001", "1002"]
    assert saved_order.order_date.strftime("%m/%d/%y") == "01/01/24"
