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


def test_create_user():
    payload = {
        "name": "Frank Castle",
        "email": "frank@example.com",
        "username": "frankc",
        "phone": "555-0000",
        "website": "frank.io",
    }
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == payload["name"]
    assert created["email"] == payload["email"]
    assert created["username"] == payload["username"]
    assert "id" in created


def test_create_user_appears_in_list():
    payload = {
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "username": "graceh",
    }
    post_response = client.post("/users", json=payload)
    assert post_response.status_code == 201
    response = client.get("/users")
    names = [u["name"] for u in response.json()]
    assert "Grace Hopper" in names


def test_create_user_missing_required_fields():
    response = client.post("/users", json={"phone": "555-9999"})
    assert response.status_code == 422
