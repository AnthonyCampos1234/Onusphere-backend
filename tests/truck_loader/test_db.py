import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from datetime import datetime
from mongoengine import connect, disconnect
from models.item import Item
from models.account import Account
from models.order import Order, OrderItem
from models.customer import Customer

TEST_DB = "customer_orders_test_db"

@pytest.fixture(scope="module", autouse=True)
def db():
    connect(
        TEST_DB,
        host="mongodb://localhost:27017/" + TEST_DB,
        uuidRepresentation='standard'
    )
    yield
    Item.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    Account.drop_collection()
    disconnect()

def test_create_item():
    Item(item_number="ITEM-TEST-001", height=10.0, width=5.0, length=3.0).save()
    assert Item.objects(item_number="ITEM-TEST-001").count() == 1
    fetched = Item.objects.get(item_number="ITEM-TEST-001")
    assert fetched.height == 10.0
    assert fetched.width == 5.0
    assert fetched.length == 3.0

def test_create_customer():
    Customer(name="Customer A").save()
    assert Customer.objects(name="Customer A").count() == 1
    fetched = Customer.objects.get(name="Customer A")
    assert fetched.name == "Customer A"

def test_create_account_with_customers():
    cust1 = Customer(name="Cust1").save()
    cust2 = Customer(name="Cust2").save()
    Account(name="Account1", customers=[cust1, cust2]).save()
    assert Account.objects(name="Account1").count() == 1
    fetched = Account.objects.get(name="Account1")
    assert len(fetched.customers) == 2
    assert fetched.customers[0].name == "Cust1"

def test_create_account_no_customer():
    Account(name="Account").save()
    assert Account.objects(name="Account").count() == 1
    fetched = Account.objects.get(name="Account")
    assert len(fetched.customers) == 0

def test_create_order_and_link_to_customer():
    customer = Customer(name="OrderCustomer").save()
    item1 = Item(item_number="ORD-ITEM-1", height=2.0, width=3.0, length=4.0).save()
    item2 = Item(item_number="ORD-ITEM-2", height=1.5, width=2.5, length=3.5).save()

    oi1 = OrderItem(item=item1, number_pallets=2)
    oi2 = OrderItem(item=item2, number_pallets=4)

    order_date = datetime(2024, 5, 1, 12, 0)
    order = Order(items=[oi1, oi2], order_date=order_date).save()

    # Link order to customer
    customer.orders.append(order)
    customer.save()

    assert Order.objects().count() == 1
    assert Customer.objects.get(id=customer.id).orders[0] == order
    fetched_order = Order.objects.first()
    assert len(fetched_order.items) == 2
    assert fetched_order.items[0].item.item_number == "ORD-ITEM-1"
    assert fetched_order.items[1].number_pallets == 4

