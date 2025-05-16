import sys
import os
from fastapi.testclient import TestClient
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipeline.loader_pipeline import start_truck_loader_thread
from models.types import Account, Customer, Order
from mongoengine import connect, disconnect
from main import app

client = TestClient(app)

TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(
        TEST_DB,
        host="mongodb://localhost:27017/" + TEST_DB,
        uuidRepresentation='standard'
    )
    yield
    Account.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    disconnect()


def test_pipeline_email_initiation_no_missing_items():
    start_truck_loader_thread()

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

    email_data = {
        "csv_file_path": "data/example_order.csv",
        "pdf_file_path": "data/example_order.pdf",
        "email_body": "Warehouse team- please have loaded for below times\n7am\n9am\n11am"
    }

    headers = {
        "email": "testuser@example.com"
    }

    email_res = client.post("/testing/email-trigger", json=email_data, headers=headers)

    # Issue now
    # Using on Account info I need to find the order that was completed 
