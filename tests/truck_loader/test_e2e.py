import sys
import os
import time
from fastapi.testclient import TestClient
import pytest
import io
import csv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipeline.loader_pipeline import start_truck_loader_thread
from models.types import Account, Customer, Item, Order, OrderBatch
from mongoengine import connect, disconnect
from main import app

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

def test_email_initiated_pipeline_no_missing_items():
    start_truck_loader_thread()

    # Step 1: Prepare CSV with only 3 items
    item_rows = [
        {"Item": "10202638", "Qty_Ord": "10", "Units_Per_Pallet": "2400", "SpecialInstructions": ""},
        {"Item": "10195770", "Qty_Ord": "20", "Units_Per_Pallet": "1600", "SpecialInstructions": ""},
        {"Item": "10202639", "Qty_Ord": "30", "Units_Per_Pallet": "1200", "SpecialInstructions": ""},
    ]
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=item_rows[0].keys())
    writer.writeheader()
    writer.writerows(item_rows)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    # Step 2: Load a valid PDF (same one you uploaded earlier)
    with open("data/example_order.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Step 3: Create business account
    payload = {
        "business_name": "Onusphere Inc",
        "business_email": "contact@onusphere.com",
        "full_name": "Will Anderson",
        "email": "will@onusphere.com",
        "password": "StrongPassword123!",
        "phone": "123-456-7890",
    }

    response = client.post("/auth/create-business-account", json=payload)
    assert response.status_code == 200
    account = Account.objects(name=payload["business_name"]).first()
    assert account

    # Step 5: Insert Items used in CSV
    items_to_create = [
        {"item_number": "10202638", "height": 10.0, "width": 5.0, "length": 3.0, "special_instructions": "none", "units_per_pallet": 2400},
        {"item_number": "10195770", "height": 8.0, "width": 4.0, "length": 2.0, "special_instructions": "none", "units_per_pallet": 1600},
        {"item_number": "10202639", "height": 6.0, "width": 4.0, "length": 3.0, "special_instructions": "none", "units_per_pallet": 1200},
    ]
    for item_data in items_to_create:
        Item(**item_data).save()

    # Step 6: Trigger pipeline
    email_res = client.post(
        "/testing/email-trigger",
        files={
            "csv_file": ("order.csv", csv_bytes, "text/csv"),
            "pdf_file": ("example_order.pdf", pdf_bytes, "application/pdf"),
        },
        data={
            "subject": account.company_code,
            "email_body": "Warehouse team- please have loaded for below times\n7am\n9am\n11am\n1pm"
        }
    )
    assert email_res.status_code == 200
    time.sleep(10)

    # Step 7: Validate order creation
    customer = Customer.objects(account=account).first()
    orders = Order.objects(customer=customer).order_by("-date_created")
    assert orders.count() > 0

    latest_order = orders.first()
    assert latest_order.status == "done"

    for order_batch in latest_order.order_item_ids:
        item = order_batch.item_id
        assert item is not None
        assert item.height > 0
        assert item.width > 0
        assert item.length > 0

    assert isinstance(latest_order.loading_instructions, list)
    assert len(latest_order.loading_instructions) == 4
    for instruction in latest_order.loading_instructions:
        assert instruction.strip() != ""


def test_email_initiated_pipeline_missing_items():
    start_truck_loader_thread()

    with open("data/example_order.pdf", "rb") as f:
        pdf_bytes = f.read()
    with open("data/example_order.csv", "rb") as f:
        csv_bytes = f.read()

    payload = {
        "business_name": "Onusphere Inc",
        "business_email": "contact@onusphere.com",
        "full_name": "Will Anderson",
        "email": "will@onusphere.com",
        "password": "StrongPassword123!",
        "phone": "123-456-7890",
    }

    response = client.post("/auth/create-business-account", json=payload)
    assert response.status_code == 200

    account = Account.objects(name=payload["business_name"]).first() # type: ignore

    email_res = client.post(
        "/testing/email-trigger",
        files={
            "csv_file": ("example_order.csv", csv_bytes, "text/csv"),
            "pdf_file": ("example_order.pdf", pdf_bytes, "application/pdf"),
        },
        data={
            "subject": account.company_code,
            "email_body": "Warehouse team- please have loaded for below times\n7am\n9am\n11am"
        }
    )
    assert email_res.status_code == 200
    time.sleep(10)

    # Get all customers related to the account
    customers = Customer.objects(account=account) # type: ignore
    assert customers.count() > 0

    # Get the most recent order for the customer
    customer = customers.first()
    orders = Order.objects(customer=customer).order_by("-date_created") # type: ignore
    assert orders.count() > 0

    latest_order = orders.first()

    assert latest_order.status == "incomplete"
    for order_batch in latest_order.order_item_ids:
        item = order_batch.item_id
        assert item is not None
        assert isinstance(item.item_number, str)
        assert item.height == 0
        assert item.width == 0
        assert item.length == 0
        assert item.units_per_pallet > 0
        assert isinstance(item.special_instructions, str)

    # Make sure loading instructions have not been processed
    assert latest_order.loading_instructions is None


def test_user_initiated_pipeline_no_missing_items():
    start_truck_loader_thread()

    # Create business account
    payload = {
        "business_name": "Onusphere Inc",
        "business_email": "contact@onusphere.com",
        "full_name": "Will Anderson",
        "email": "will@onusphere.com",
        "password": "StrongPassword123!",
        "phone": "123-456-7890",
    }

    response = client.post("/auth/create-business-account", json=payload)
    assert response.status_code == 200
    account = Account.objects(name=payload["business_name"]).first()
    assert account

    # Step 4: Insert Customer (email domain must match PDF)
    customer = Customer(name="York Target", email_domain="shorr.com", account=account).save()

    # Step 5: Insert Items used in CSV
    items_to_create = [
        {"item_number": "10202638", "height": 10.0, "width": 5.0, "length": 3.0, "special_instructions": "none", "units_per_pallet": 2400},
        {"item_number": "10195770", "height": 8.0, "width": 4.0, "length": 2.0, "special_instructions": "none", "units_per_pallet": 1600},
        {"item_number": "10202639", "height": 0.0, "width": 4.0, "length": 3.0, "special_instructions": "none", "units_per_pallet": 1200},
    ]
    for item_data in items_to_create:
        Item(**item_data).save()

    # Step 6: Trigger pipeline
  #   user_res = 
#assert email_res.status_code == 200
    time.sleep(10)

    # Step 7: Validate order creation
    customer = Customer.objects(account=account).first()
    orders = Order.objects(customer=customer).order_by("-date_created")
    assert orders.count() > 0

    latest_order = orders.first()
    assert latest_order.status == "done"

    for order_batch in latest_order.order_item_ids:
        item = order_batch.item_id
        assert item is not None
        assert item.height > 0
        assert item.width > 0
        assert item.length > 0

    assert isinstance(latest_order.loading_instructions, list)
    assert len(latest_order.loading_instructions) == 4
    for instruction in latest_order.loading_instructions:
        assert instruction.strip() != ""


