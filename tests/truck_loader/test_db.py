import os
import sys
import pytest
from datetime import datetime
from mongoengine import connect, disconnect
from bson import ObjectId

# Ensure models can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.item import Item
from models.customer import Customer
from models.account import Account
from models.order import Order, OrderItem

TEST_DB = "test_customer_orders"

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", uuidRepresentation="standard")
    yield
    Item.drop_collection()
    Customer.drop_collection()
    Account.drop_collection()
    Order.drop_collection()
    disconnect()


def test_create_item_model():
    item = Item(item_number="ABC12345", height=10.0, width=5.5, length=3.3, special_instructions="Keep upright")
    item.save()

    fetched = Item.objects.get(item_number="ABC12345")
    assert fetched.height == 10.0
    assert fetched.special_instructions == "Keep upright"


def test_create_customer_model():
    customer = Customer(name="Customer Inc", email_domain="example.com")
    customer.save()

    fetched = Customer.objects.get(email_domain="example.com")
    assert fetched.name == "Customer Inc"
    assert fetched.email_domain == "example.com"


def test_create_account_and_link_customers():
    account = Account(name="Corp Account", email="corp@account.com", hashed_password="abc123").save()

    cust1 = Customer(name="Customer1", email_domain="cust1.com", account=account).save()
    cust2 = Customer(name="Customer2", email_domain="cust2.com", account=account).save()

    # Fetch customers linked to the account
    linked_customers = Customer.objects(account=account)

    assert Account.objects(email="corp@account.com").count() == 1
    assert linked_customers.count() == 2
    assert linked_customers[0].account.id == account.id
    assert set(c.name for c in linked_customers) == {"Customer1", "Customer2"}


def test_create_order_with_embedded_items():
    item1 = Item(item_number="ORDITEM1", height=1.0, width=1.0, length=1.0).save()
    item2 = Item(item_number="ORDITEM2", height=2.0, width=2.0, length=2.0).save()
    customer = Customer(name="Order Buyer", email_domain="buyer.com").save()

    oi1 = OrderItem(item=item1, number_pallets=2)
    oi2 = OrderItem(item=item2, number_pallets=4)

    order = Order(
        customer=customer,
        items=[oi1, oi2],
        order_date=datetime(2025, 5, 5, 15, 30),
        upcoming_shipment_times=["7am, 9am"]
    )
    order.save()

    fetched_order = Order.objects.get(id=order.id) # type: ignore
    assert fetched_order.customer.name == "Order Buyer"
    assert len(fetched_order.items) == 2
    assert fetched_order.items[0].number_pallets == 2
    assert fetched_order.upcoming_shipment_times == ["7am, 9am"]


def test_orderitem_pallet_calculation():
    order_item = OrderItem(item=Item(item_number="PALLETTEST").save(), number_pallets=0)
    order_item.set_pallets(order_quantity=120, units_per_pallet=50)
    assert order_item.number_pallets == 3

    with pytest.raises(ValueError):
        order_item.set_pallets(order_quantity=10, units_per_pallet=0)
