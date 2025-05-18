import sys
import os
import tempfile
from bson import ObjectId
import pandas as pd
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from models.types import Customer, Order, Item, Account, OrderBatch
from scripts.truck_loader.ingestion import create_customer_receipt, parse_csv, parse_pdf
from mongoengine import connect, disconnect

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
    Item.drop_collection()
    Customer.drop_collection()
    Order.drop_collection()
    OrderBatch.drop_collection()
    disconnect()

def test_parse_csv_valid():
    csv_content = b"Item,Quantity\n123,5\n456,10\n"
    df = parse_csv(csv_content)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Item", "Quantity"]
    assert df['Item'].dtype == object
    assert df.iloc[0]['Item'] == '123'
    assert df.iloc[1]['Quantity'] == 10

def test_parse_csv_empty_file():
    with pytest.raises(ValueError, match="Empty CSV content provided"):
        parse_csv(b"")

def test_parse_csv_invalid_input_type():
    csv_content = "Item,Quantity\n123,5\n456,10\n"  # intentionally wrong (str, not bytes)

    with pytest.raises(TypeError, match="Expected CSV data as bytes"):
        parse_csv(csv_content)

def test_parse_pdf():    
    # Load PDF as raw bytes
    with open("data/example_order.pdf", "rb") as f:
        pdf_bytes = f.read()

    # Pass bytes directly to parse_pdf (it internally uses BytesIO correctly)
    domain, date_ordered, units_per_pallet, special_instructions = parse_pdf(pdf_bytes)

    assert domain == "shorr.com"
    assert len(special_instructions) == 6
    assert date_ordered == "11/18/24"
    assert special_instructions[0]["item_id"] == "10126054"
    assert "Gaylords" in special_instructions[0]["instruction"]
    assert units_per_pallet[0]["item_id"] == "10202638"
    assert units_per_pallet[0]["units_per_pallet"] == 2400

def test_create_order_reciept():
    # Load PDF as raw bytes
    with open("data/example_order.pdf", "rb") as f:
        pdf_bytes = f.read()
    # Load CSV as raw bytes
    with open("data/example_order.csv", "rb") as f:
        csv_bytes = f.read()

    account = Account(email="test@gmail.com", name="account", company_code="ABCG").save()

    email_data = {
        "csv_file": csv_bytes,
        "pdf_file": pdf_bytes, 
        "subject": account.company_code, 
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
    # Run the function under test
    order_data = create_customer_receipt(email_data)

    # Validate returned order data
    assert order_data["customer_email_domain"] == "shorr.com"
    assert ObjectId.is_valid(order_data["order_id"]), "Invalid order_id"

    # Fetch order from DB
    order = Order.objects(id=ObjectId(order_data["order_id"])).first()
    assert order is not None, "Order was not found in the database"

    # Validate basic order fields
    assert len(order.order_item_ids) > 0, "No order items found"
    assert order.shipment_times == ["7am", "9am", "11am", "11am", "1pm"]

    # Validate item-level data (check first OrderBatch and its Item)
    order_batch = order.order_item_ids[0]
    item = order_batch.item_id

    assert item.item_number == "10202638"
    assert len(item.special_instructions) == 0
    assert order_batch.number_pallets > 0
