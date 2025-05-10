import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.account import Account
from main import app
from utils.dependencies import get_current_user

TEST_DB = "test_account_routes_db"
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", alias="default")
    yield
    Account.drop_collection()
    disconnect()

@pytest.fixture
def test_account():
    unique_email = f"test_{uuid.uuid4().hex}@example.com"
    account = Account(
        name="Test User",
        email=unique_email,
        hashed_password="test",
        company_name="TestCo",
        phone="123-456-7890",
        job_title="Engineer",
        timezone="UTC"
    ).save()
    return account

def test_get_current_user_info(test_account):
    app.dependency_overrides[get_current_user] = lambda: test_account
    response = client.get("/account/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_account.email
    assert data["name"] == test_account.name
    assert data["company_name"] == test_account.company_name
    assert data["timezone"] == test_account.timezone

def test_update_current_user(test_account):
    app.dependency_overrides[get_current_user] = lambda: test_account
    new_data = {
        "name": "Updated Name",
        "phone": "999-999-9999",
        "timezone": "America/New_York"
    }
    response = client.put("/account/me/update", json=new_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    test_account.reload()
    assert test_account.name == "Updated Name"
    assert test_account.phone == "999-999-9999"
    assert test_account.timezone == "America/New_York"
