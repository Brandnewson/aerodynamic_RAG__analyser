"""Authentication endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    from app.domain import models  # noqa: F401

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def test_register_login_and_get_me(client: TestClient):
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "Supersecret1!"},
    )
    assert register.status_code == 201
    assert register.json()["username"] == "testuser"

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "Supersecret1!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "testuser"


def test_register_duplicate_username_returns_409(client: TestClient):
    payload = {"username": "duplicate", "password": "Supersecret1!"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409
    assert second.json()["code"] == "USER_ALREADY_EXISTS"


def test_register_rejects_password_without_number_or_special_character(client: TestClient):
    no_number = client.post(
        "/api/v1/auth/register",
        json={"username": "nonumber", "password": "password!"},
    )
    assert no_number.status_code == 422

    no_special = client.post(
        "/api/v1/auth/register",
        json={"username": "nospecial", "password": "password1"},
    )
    assert no_special.status_code == 422


def test_login_invalid_credentials_returns_401(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"username": "tester", "password": "Supersecret1!"},
    )

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "tester", "password": "wrong-password"},
    )
    assert login.status_code == 401
    assert login.json()["code"] == "INVALID_CREDENTIALS"


def test_me_requires_bearer_token(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_ERROR"


def test_protected_business_route_requires_bearer_token(client: TestClient):
    response = client.get("/api/v1/concepts")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_ERROR"
