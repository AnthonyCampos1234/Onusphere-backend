import sys
import os
from fastapi.testclient import TestClient
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipeline.truck_loader.pipeline import start_truck_loader_thread
from models.order import Order
from models.account import Account
from models.customer import Customer
from pipeline.app import app
from mongoengine import connect, disconnect

client = TestClient(app)

TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
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
    
    signup_payload = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    signup_res = client.post("/signup", json=signup_payload)
    assert signup_res.status_code == 200

    email_data = {
        "csv_file_path": "data/example_order.csv",
        "pdf_file_path": "data/example_order.pdf",
        "email_body": "Warehouse team- please have loaded for below times\n7am\n9am\n11am"
    }

    headers = {
        "email": "testuser@example.com"
    }

    email_res = client.post("/email-trigger", json=email_data, headers=headers)
    assert email_res.status_code == 200

    # Issue now
    # Using on the Account info I need to find the order that was completed 