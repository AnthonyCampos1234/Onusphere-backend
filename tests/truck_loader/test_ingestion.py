from datetime import datetime
import sys
import os
import tempfile
import uuid
import pandas as pd
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.truck_loader.ingestion import create_customer_receipt, parse_csv, parse_pdf

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

def test_extract_special_instructions():    
    instructions, date_ordered, customer_id = parse_pdf("data/example_order.pdf")

    assert len(instructions) == 6
    assert date_ordered == "11/18/24"
    assert customer_id == "Target.York PA 9475"
    assert instructions[0]["item_id"] == "10126054"
    assert "Gaylords" in instructions[0]["instruction"]


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

    result = create_customer_receipt(email_data)

    # Validate order_id exists and is a UUID
    assert "order_id" in result
    uuid_obj = result["order_id"]
    assert isinstance(uuid_obj, uuid.UUID)

    # Validate date_ordered is a date-like object or string
    assert "date_ordered" in result
    try:
        parsed_date = datetime.strptime(result["date_ordered"], "%m/%d/%y")
    except ValueError:
        pytest.fail("date_ordered is not in MM/DD/YY format")

    # Validate upcoming_shipment_times is a list of strings
    assert isinstance(result["upcoming_shipment_times"], list)
    assert all(isinstance(t, str) for t in result["upcoming_shipment_times"])
    assert "7am" in result["upcoming_shipment_times"]

    # Validate order_details is a DataFrame and contains the expected column
    assert isinstance(result["order_details"], pd.DataFrame)
    assert "Special_Instructions" in result["order_details"].columns