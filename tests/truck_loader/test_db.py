import sys
import os
import pytest
from datetime import datetime, date
from mongoengine import connect, disconnect
from bson import ObjectId

# Ensure models can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from models.types import Account, Member, Customer, Item, OrderBatch, Order

TEST_DB = "test_customer_orders"

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", uuidRepresentation="standard")
    yield
    Item.drop_collection()
    Customer.drop_collection()
    Account.drop_collection()
    OrderBatch.drop_collection()
    Order.drop_collection()
    Member.drop_collection()
    disconnect()

def test_create_item_model():
    item = Item(
        item_number="ABC12345",
        height=10.0,
        width=5.5,
        length=3.3,
        special_instructions="Keep upright",
        description="Sample item",
        units_per_pallet=50
    ).save()

    fetched = Item.objects.get(item_number="ABC12345")
    assert fetched.height == 10.0
    assert fetched.special_instructions == "Keep upright"

def test_create_account_and_member_and_customer():
    account = Account(
        email="corp@account.com",
        name="Corp Account",
        company_code="ABCDEF"
    ).save()

    member = Member(
        account=account,
        name="John Doe",
        email="johndoe@corp.com",
        phone="1234567890",
        hashed_password="hashed_pw",
        role="admin"
    ).save()

    customer = Customer(
        account=account,
        name="Customer Inc",
        email_domain="example.com"
    ).save()

    assert Account.objects(email="corp@account.com").count() == 1
    assert Member.objects(email="johndoe@corp.com").count() == 1
    assert Customer.objects(email_domain="example.com").count() == 1

def test_create_orderbatch_with_pallet_calc():
    item = Item(
        item_number="ITEMBATCH",
        height=2.0,
        width=2.0,
        length=2.0,
        special_instructions="Handle with care",
        description="Batch item",
        units_per_pallet=40
    ).save()

    batch = OrderBatch(
        item_id=item,
        number_pallets=0
    )
    batch.set_pallets(order_quantity=120, units_per_pallet=40)
    batch.save()

    fetched_batch = OrderBatch.objects.get(id=batch.id)
    assert fetched_batch.number_pallets == 3

def test_create_order_linked_all():
    # Prepare linked entities
    account = Account.objects.get(company_code="ABCDEF")
    customer = Customer.objects.get(account=account)
    item1 = Item.objects.get(item_number="ABC12345")
    item2 = Item.objects.get(item_number="ITEMBATCH")

    # Create batches
    batch1 = OrderBatch(
        item_id=item1,
        number_pallets=2
    ).save()

    batch2 = OrderBatch(
        item_id=item2,
        number_pallets=4
    ).save()

    order = Order(
        customer=customer,
        order_item_ids=[batch1, batch2],
        order_date=date(2025, 5, 6),
        shipment_times=["8am", "10am"],
        status="processing",
        loading_instructions=["Use dock 3", "Stack double pallets"]
    ).save()

    fetched_order = Order.objects.get(id=order.id)
    assert fetched_order.customer.name == "Customer Inc"
    assert len(fetched_order.order_item_ids) == 2
    assert fetched_order.status == "processing"
    assert fetched_order.loading_instructions == ["Use dock 3", "Stack double pallets"]
