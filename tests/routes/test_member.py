import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mongoengine import connect, disconnect
from models.types import Account, Member
from main import app
from utils.dependencies import get_current_user

TEST_DB = "test_member_routes_db"
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}", alias="default")
    yield
    Member.drop_collection()
    Account.drop_collection()
    disconnect()


@pytest.fixture
def test_member():
    unique_code = f"CODE_{uuid.uuid4().hex[:6]}"
    unique_email = f"account_{uuid.uuid4().hex}@test.com"

    account = Account(
        name="Test Account",
        email=unique_email,
        company_code=unique_code
    ).save()

    member = Member(
        account=account,
        name="Test Member",
        email=f"member_{uuid.uuid4().hex}@test.com",
        phone="123-456-7890",
        hashed_password="hashed",
        role="admin"
    ).save()

    return member

def test_get_current_member_info(test_member):
    app.dependency_overrides[get_current_user] = lambda: test_member

    response = client.get("/member/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_member.pk)
    assert data["name"] == test_member.name
    assert data["email"] == test_member.email
    assert data["phone"] == test_member.phone
    assert data["role"] == test_member.role
    assert data["account_id"] == str(test_member.account.id)

    app.dependency_overrides = {}

def test_update_current_member_info(test_member):
    app.dependency_overrides[get_current_user] = lambda: test_member

    new_data = {
        "name": "Updated Member",
        "phone": "999-999-9999"
    }

    response = client.put("/member/me/update", json=new_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    test_member.reload()
    assert test_member.name == "Updated Member"
    assert test_member.phone == "999-999-9999"

    app.dependency_overrides = {}
