"""Shared helpers for authenticated API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def authenticate_client(
    client: TestClient,
    *,
    username: str = "testuser",
    password: str = "Supersecret1!",
) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return token
