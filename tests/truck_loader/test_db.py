import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from datetime import datetime
from mongoengine import connect, disconnect
from models.item import Item
from models.customer import Customer
from models.customer_order import CustomerOrder

TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
    connect(
      TEST_DB,
      host="mongodb://localhost:27017/" + TEST_DB,
      uuidRepresentation='standard'
    )
    yield
    # Cleanup: Drop DB and disconnect
    Item.drop_collection()
    Customer.drop_collection()
    CustomerOrder.drop_collection()
    disconnect()

def test_insert_item():
    # Insert mock item
    item = Item(item_number="TEST123", height=1.0, width=2.0, length=3.0).save()

    # Check it exists
    assert Item.objects(item_number="TEST123").count() == 1

    # Check attributes
    fetched = Item.objects.get(item_number="TEST123")
    assert fetched.height == item.height
    assert fetched.width == item.width
    assert fetched.length == item.length

def test_insert_customer():
    customer = Customer(name="ABC Corporation", email="example@gmail.com").save()

    # Check it exists
    assert Customer.objects(name="ABC Corporation").count() == 1

    # Check attributes
    fetched = Customer.objects.get(name="ABC Corporation")
    assert fetched.name == customer.name
    assert fetched.email == customer.email

def test_insert_customer_order():
    # Create and save customer
    customer = Customer(name="XYZ Industries", email="xyz@example.com").save()

    # Create and save items
    item1 = Item(item_number="ITEM001", height=2.0, width=3.0, length=4.0).save()
    item2 = Item(item_number="ITEM002", height=1.5, width=2.5, length=3.5).save()

    # Explicitly set order date
    date = datetime(2024, 1, 1, 10, 30)

    # Create and save order
    order = CustomerOrder(customer=customer, item=[item1, item2], order_date=date).save()

    # Assertions
    assert CustomerOrder.objects(customer=customer).count() == 1

    fetched_order = CustomerOrder.objects.get(customer=customer)
    assert fetched_order.order_date == date

