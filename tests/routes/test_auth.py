import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from models.types import Account, Member
from main import app

TEST_DB = "test_auth_db"

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db():
    disconnect()
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}")
    yield
    Account.drop_collection()
    Member.drop_collection()
    disconnect()

def test_create_business_account_success():
    payload = {
        "business_name": "Onusphere Inc",
        "business_email": "contact@onusphere.com",
        "full_name": "Will Anderson",
        "email": "will@onusphere.com",
        "password": "StrongPassword123!",
        "phone": "123-456-7890",
    }

    response = client.post("/auth/create-business-account", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify Account was created
    account = Account.objects(email="contact@onusphere.com").first() # type: ignore
    assert account is not None
    assert account.name == "Onusphere Inc"
    assert isinstance(account.company_code, str)
    assert len(account.company_code) == 6

    # Verify Member was created and linked
    member = Member.objects(email="will@onusphere.com").first() # type: ignore
    assert member is not None
    assert member.account.id == account.pk
    assert member.role == "admin"

def test_create_business_account_duplicate():
    payload = {
        "business_name": "Onusphere Inc",
        "business_email": "contact@onusphere.com",  # duplicate email
        "full_name": "Duplicate User",
        "email": "dup@onusphere.com",
        "password": "AnotherPassword123!",
        "phone": "999-999-9999",
    }

    response = client.post("/auth/create-business-account", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Account already exists"


def test_add_new_member_success():
    # First create an account to associate with the member
    account = Account(
        name="Test Business",
        email="testbusiness@example.com",
        company_code="ABC123"
    ).save()

    payload = {
        "company_code": "ABC123",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "TestPass123!",
        "phone": "555-555-5555"
    }

    response = client.post("/auth/add-new-member", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify Member was created and linked correctly
    member = Member.objects(email="johndoe@example.com").first() # type: ignore
    assert member is not None
    assert member.account.id == account.pk
    assert member.name == "John Doe"
    assert member.phone == "555-555-5555"
    assert member.role == "member"

def test_add_new_member_invalid_company_code():
    payload = {
        "company_code": "INVALID",
        "full_name": "Jane Doe",
        "email": "janedoe@example.com",
        "password": "TestPass123!",
        "phone": "555-555-1234"
    }

    response = client.post("/auth/add-new-member", json=payload)
    assert response.status_code == 404  # Assuming you handle it this way
    assert response.json()["detail"] == "Account not found"

def test_add_new_member_duplicate_email():
    # Setup account and initial member
    account = Account(
        name="Another Business",
        email="anotherbusiness@example.com",
        company_code="DEF456"
    ).save()

    Member(
        account=account.pk,
        name="Existing User",
        email="existing@example.com",
        phone="123-123-1234",
        hashed_password="hashedpass",
        role="admin"
    ).save()

    payload = {
        "company_code": "DEF456",
        "full_name": "Duplicate User",
        "email": "existing@example.com",
        "password": "TestPass123!",
        "phone": "555-555-9876"
    }

    response = client.post("/auth/add-new-member", json=payload)
    assert response.status_code == 400  # Assuming you check for duplicates
    assert response.json()["detail"] == "Member already exists"



"""
def test_successful_signup():
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_signup_duplicate_email():
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "anotherpass"
    }
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"

def test_successful_login():
    payload = {
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    payload = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_nonexistent_user():
    payload = {
        "email": "ghost@example.com",
        "password": "doesntmatter"
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

    """
