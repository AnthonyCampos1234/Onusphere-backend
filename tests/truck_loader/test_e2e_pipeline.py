import time
import sys
import os
from fastapi.testclient import TestClient
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.order import Order
from models.account import Account
from models.customer import Customer
from pipeline.truck_loader import app
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


def test_pipeline_end_to_end():
    account = Account(name="Account").save()

    customer = Customer(name="Customer").save()
    account.addCustomer(customer)





    # Create a mock OrderReceipt in the DB
    order = Order.objects.create(
        # Add whatever fields your OrderReceipt needs
    )

    # Trigger the pipeline
    response = client.post("/email-trigger", json={"order_id": str(order.id)})
    assert response.status_code == 200

    # Wait for the background pipeline to complete
    time.sleep(2)  # Adjust based on how long the pipeline takes

    # Check the result
    result = client.get("/result")
    assert result.status_code == 200
    assert result.json()["data"] is not None
    assert "response" in result.json()["data"]
