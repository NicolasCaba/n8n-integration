import pytest
from fastapi.testclient import TestClient
from main import app, MOCK_USERS

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_token(username: str = "admin", password: str = "admin123") -> str:
    response = client.post("/auth/login", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Users Microservice is running"}


# ---------------------------------------------------------------------------
# Auth – login
# ---------------------------------------------------------------------------

def test_login_success():
    response = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password():
    response = client.post("/auth/login", data={"username": "admin", "password": "wrongpass"})
    assert response.status_code == 401


def test_login_unknown_user():
    response = client.post("/auth/login", data={"username": "nobody", "password": "x"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Auth – /auth/me
# ---------------------------------------------------------------------------

def test_me_authenticated():
    token = get_token()
    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_me_unauthenticated():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_invalid_token():
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# /users – requires authentication
# ---------------------------------------------------------------------------

def test_get_users_unauthenticated():
    response = client.get("/users")
    assert response.status_code == 401


def test_get_users_returns_list():
    token = get_token()
    response = client.get("/users", headers=auth_headers(token))
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 5


def test_get_users_fields():
    token = get_token()
    response = client.get("/users", headers=auth_headers(token))
    user = response.json()[0]
    assert "id" in user
    assert "name" in user
    assert "email" in user
    assert "username" in user


def test_get_user_by_id():
    token = get_token()
    response = client.get("/users/1", headers=auth_headers(token))
    assert response.status_code == 200
    user = response.json()
    assert user["id"] == 1
    assert user["name"] == "Alice Johnson"
    assert user["email"] == "alice@example.com"


def test_get_user_by_id_unauthenticated():
    response = client.get("/users/1")
    assert response.status_code == 401


def test_get_user_not_found():
    token = get_token()
    response = client.get("/users/999", headers=auth_headers(token))
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_create_user():
    token = get_token()
    payload = {
        "name": "Frank Castle",
        "email": "frank@example.com",
        "username": "frankc",
        "phone": "555-0000",
        "website": "frank.io",
    }
    response = client.post("/users", json=payload, headers=auth_headers(token))
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == payload["name"]
    assert created["email"] == payload["email"]
    assert created["username"] == payload["username"]
    assert "id" in created


def test_create_user_unauthenticated():
    payload = {
        "name": "Frank Castle",
        "email": "frank@example.com",
        "username": "frankc",
    }
    response = client.post("/users", json=payload)
    assert response.status_code == 401


def test_create_user_appears_in_list():
    token = get_token()
    payload = {
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "username": "graceh",
    }
    post_response = client.post("/users", json=payload, headers=auth_headers(token))
    assert post_response.status_code == 201
    response = client.get("/users", headers=auth_headers(token))
    names = [u["name"] for u in response.json()]
    assert "Grace Hopper" in names


def test_create_user_missing_required_fields():
    token = get_token()
    response = client.post("/users", json={"phone": "555-9999"}, headers=auth_headers(token))
    assert response.status_code == 422
