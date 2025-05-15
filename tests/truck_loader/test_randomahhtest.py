import os
import sys
from fastapi.testclient import TestClient
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from pipeline.truck_loader.pipeline import start_truck_loader_thread
from models.order import Order
from models.account import Account
from models.customer import Customer
from mongoengine import connect, disconnect
from main import app

# Load environment variables from .env
load_dotenv()

client = TestClient(app)

# Connect to the normal DB (not test DB)
connect(    
    db=os.getenv("MONGO_DB_NAME"),
    host=os.getenv("MONGO_URI"),
    uuidRepresentation='standard'
)

def test_pipeline_email_initiation_on_real_db():
    start_truck_loader_thread()

    signup_payload = {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    signup_res = client.post("/auth/signup", json=signup_payload)
    print("Signup response:", signup_res.json())
    assert signup_res.status_code == 200

    email_data = {
        "csv_file_path": "data/example_order.csv",
        "pdf_file_path": "data/example_order.pdf",
        "email_body": "Warehouse team- please have loaded for below times\n7am\n9am\n11am"
    }

    headers = {
        "email": "testuser@example.com"
    }

    email_res = client.post("/testing/email-trigger", json=email_data, headers=headers)
    print("Email trigger response:", email_res.json())
    assert email_res.status_code == 200