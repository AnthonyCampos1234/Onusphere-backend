import sys
import os
import tempfile
from bson import ObjectId
import pandas as pd
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from models.customer import Customer
from models.item import Item
from models.order import Order
from scripts.truck_loader.ingestion import create_customer_receipt, parse_csv, parse_pdf
from mongoengine import connect, disconnect

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
    disconnect()

def test_parse_csv_valid():
    # Create temporary CSV with valid data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp.write("Item,Quantity\n")
        tmp.write("123,5\n")
        tmp.write("456,10\n")
        tmp_path = tmp.name

    try:
        df = parse_csv(tmp_path)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["Item", "Quantity"]
        assert df['Item'].dtype == object
        assert df.iloc[0]['Item'] == '123'
        assert df.iloc[1]['Quantity'] == 10
    finally:
        os.remove(tmp_path)

def test_parse_csv_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
        tmp_path = tmp.name

    try:
        with pytest.raises(pd.errors.EmptyDataError):
            parse_csv(tmp_path)
    finally:
        os.remove(tmp_path)

def test_parse_csv_invalid_path():
    with pytest.raises(FileNotFoundError):
        parse_csv("/path/does/not/exist.csv")

def test_parse_pdf():    
    domain, date_ordered, units_per_pallet, special_instructions = parse_pdf("data/example_order.pdf")

    assert len(special_instructions) == 6
    assert date_ordered == "11/18/24"
    assert domain == "shorr.com"
    assert special_instructions[0]["item_id"] == "10126054"
    assert "Gaylords" in special_instructions[0]["instruction"]
    assert units_per_pallet[0]["item_id"] == "10202638"
    assert units_per_pallet[0]["units_per_pallet"] == 2400

def test_create_order_reciept():
    email_data = {
        "csv_file_path": "data/example_order.csv",
        "pdf_file_path": "data/example_order.pdf",
        "email_body": """Warehouse team- please have loaded for below times

                        7am
                        9am
                        11am
                        11am
                        1pm


                        Shaina Reed - Fleet Operations Manager
                        825 Locust Point Road | York, PA 17406
                        P: 717-790-6260  | C: 717-462-8550""",
    }

    order_data = create_customer_receipt(email_data)

    assert order_data["customer_email_domain"] == "shorr.com"
    assert ObjectId.is_valid(order_data["order_id"]) # make sure order exists in DB

    order = Order.objects(id=ObjectId(order_data["order_id"])).first()
    assert order is not None, "Order was not found in the database"

    # Validate basic order fields
    assert len(order.items) > 0, "No order items found"
    assert order.upcoming_shipment_times == "7am, 9am, 11am, 11am, 1pm"

    # Validate item-level data (example for the first item)
    item = order.items[0]
    assert item.item.item_number == "10202638"
    assert len(item.item.special_instructions) == 0
    assert item.number_pallets > 0
