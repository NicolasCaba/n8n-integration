import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Users Microservice is running"}


def test_get_users_returns_list():
    response = client.get("/users")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) == 5


def test_get_users_fields():
    response = client.get("/users")
    user = response.json()[0]
    assert "id" in user
    assert "name" in user
    assert "email" in user
    assert "username" in user


def test_get_user_by_id():
    response = client.get("/users/1")
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert user["name"] == "Alice Johnson"
    assert user["email"] == "alice@example.com"


def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
