import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from models.account import Account
from pipeline.app import app

TEST_DB = "test_auth_db"

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def db():
    connect(TEST_DB, host=f"mongodb://localhost:27017/{TEST_DB}")
    yield
    Account.drop_collection()
    disconnect()

def test_successful_signup():
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    response = client.post("/signup", json=payload)
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
    response = client.post("/signup", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"

def test_successful_login():
    payload = {
        "email": "testuser@example.com",
        "password": "securepassword123"
    }
    response = client.post("/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password():
    payload = {
        "email": "testuser@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_nonexistent_user():
    payload = {
        "email": "ghost@example.com",
        "password": "doesntmatter"
    }
    response = client.post("/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
