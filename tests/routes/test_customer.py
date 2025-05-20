
import sys
import os
import uuid
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from types import SimpleNamespace

# Ensure we can import from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.types import Account, Member, Customer, Order, OrderBatch, Item
from main import app
from utils.dependencies import get_current_user

TEST_DB = "test_customer_routes_db"
client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", alias="default")
    yield
    Account.drop_collection()
    Member.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    Item.drop_collection()
    disconnect()

@pytest.fixture
def account_and_customers():
    unique_email = f"test_{uuid.uuid4().hex}@example.com"

    account = Account(
        email=unique_email,
        name="Corp Account",
        company_code="ABCDEF"
    ).save()

    cust1 = Customer(name="Customer A", email_domain="", account=account).save()
    cust2 = Customer(name="Customer B", email_domain="", account=account).save()
    return account, [cust1, cust2]

@pytest.fixture
def account_customer_order():
    unique_email = f"test_{uuid.uuid4().hex}@example.com"

    account = Account(
        email=unique_email,
        name="Corp Account",
        company_code="ABCDEF"
    ).save()

    customer = Customer(
        name="OrderCust",
        email_domain="cust.com",
        account=account
    ).save()

    item = Item(
        item_number="1234",
        height=10.0,
        width=5.0,
        length=3.0,
        special_instructions="Handle with care",
        description="Square thing",
        units_per_pallet=12
    ).save()

    order_batch = OrderBatch(
        item_id=item,
        number_pallets=3
    ).save()

    order = Order(
        customer=customer,
        order_item_ids=[order_batch],
        order_date=datetime.now().date(),
        shipment_times=["7am"],
        status="processing",
        loading_instructions=["Load special instructions"]
    ).save()

    return account, customer, order

def test_get_all_customers(account_and_customers):
    account, customers = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    response = client.get("/customer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Customer A", "Customer B"]

    app.dependency_overrides = {}

def test_get_single_customer(account_and_customers):
    account, customers = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    customer_id = str(customers[0].id)
    response = client.get(f"/customer/{customer_id}")
    assert response.status_code == 200
    assert response.json()["name"] == customers[0].name

    app.dependency_overrides = {}

def test_get_customer_not_found(account_and_customers):
    account, _ = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    response = client.get("/customer/000000000000000000000000")
    assert response.status_code == 404

    app.dependency_overrides = {}

def test_get_unique_items_for_customer(account_customer_order):
    account, customer, _ = account_customer_order
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    response = client.get(f"/customer/{customer.id}/unique-items")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    item = data[0]
    assert "item_id" in item
    assert "item_number" in item
    assert "description" in item
    assert "units_per_pallet" in item

    app.dependency_overrides = {}

def test_create_customer(account_and_customers):
    account, _ = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    payload = {
        "name": "New Customer",
        "email_domain": "newcustomer.com"
    }

    response = client.post("/customer", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "New Customer"
    assert data["email_domain"] == "newcustomer.com"
    assert "id" in data

    customer_in_db = Customer.objects(id=data["id"]).first()
    assert customer_in_db is not None
    assert customer_in_db.name == "New Customer"

    app.dependency_overrides = {}

def test_create_customer_missing_field(account_and_customers):
    account, _ = account_and_customers
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(account=account)

    payload = {
        "name": "Missing Email"
    }

    response = client.post("/customer", json=payload)
    assert response.status_code == 422

    app.dependency_overrides = {}

