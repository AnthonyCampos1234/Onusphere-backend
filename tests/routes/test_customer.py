import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.account import Account
from models.customer import Customer
from main import app
from utils.dependencies import get_current_user

TEST_DB = "test_customer_routes_db"
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", alias="default")
    yield
    Account.drop_collection()
    Customer.drop_collection()
    disconnect()

@pytest.fixture
def account_and_customers():
    unique_email = f"test_{uuid.uuid4().hex}@example.com"
    account = Account(name="Test User", email=unique_email, hashed_password="test").save()
    cust1 = Customer(name="Customer A", email_domain="", account=account).save()
    cust2 = Customer(name="Customer B", email_domain="", account=account).save()
    return account, [cust1, cust2]

def test_get_all_customers(account_and_customers):
    account, customers = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: account

    response = client.get("/customers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Customer A", "Customer B"]

    app.dependency_overrides = {}

def test_get_single_customer(account_and_customers):
    account, customers = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: account

    customer_id = str(customers[0].id)
    response = client.get(f"/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["name"] == customers[0].name

    app.dependency_overrides = {}

def test_get_customer_not_found(account_and_customers):
    account, _ = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: account

    response = client.get("/customers/000000000000000000000000")  # non-existent ID
    assert response.status_code == 404

    app.dependency_overrides = {}
