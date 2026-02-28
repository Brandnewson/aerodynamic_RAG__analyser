"""Tests for the /api/v1/concepts CRUD endpoints.

Run with:
    uv run pytest tests/ -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test database — in-memory SQLite with StaticPool.
#
# StaticPool forces *all* connections to reuse the same underlying DBAPI
# connection, which is required for in-memory SQLite: without it, each
# new connection starts a fresh (empty) database, so tables created during
# setup are invisible to the session used inside route handlers.
# ---------------------------------------------------------------------------

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
    """Provide a TestClient backed by an isolated in-memory SQLite database.

    Table creation happens here (not in a separate autouse fixture) so the
    ordering is guaranteed: tables exist before the TestClient starts.
    """
    from app.domain import models  # noqa: F401 — register ORM models with Base

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PAYLOAD = {
    "title": "Double-element beam wing",
    "description": (
        "Introduce a double-element beam wing to improve rear load "
        "consistency in medium-speed corners by energising the rear wake."
    ),
    "author": "Test Engineer",
    "tags": ["downforce", "beam-wing"],
}


# ---------------------------------------------------------------------------
# POST /concepts
# ---------------------------------------------------------------------------


def test_create_concept_returns_201(client):
    response = client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == VALID_PAYLOAD["title"]
    assert data["status"] == "SUBMITTED"
    assert data["tags"] == ["downforce", "beam-wing"]


def test_create_concept_missing_required_fields_returns_422(client):
    response = client.post("/api/v1/concepts", json={"title": "Only title"})
    assert response.status_code == 422


def test_create_concept_description_too_short_returns_422(client):
    payload = {**VALID_PAYLOAD, "description": "Too short"}
    response = client.post("/api/v1/concepts", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /concepts
# ---------------------------------------------------------------------------


def test_list_concepts_empty(client):
    response = client.get("/api/v1/concepts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_list_concepts_returns_created_concept(client):
    client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    response = client.get("/api/v1/concepts")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_concepts_filter_by_status(client):
    client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    response = client.get("/api/v1/concepts?status=SUBMITTED")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/concepts?status=ANALYSED")
    assert response.json()["total"] == 0


# ---------------------------------------------------------------------------
# GET /concepts/{id}
# ---------------------------------------------------------------------------


def test_get_concept_returns_200(client):
    client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    response = client.get("/api/v1/concepts/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_concept_not_found_returns_404(client):
    response = client.get("/api/v1/concepts/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /concepts/{id}
# ---------------------------------------------------------------------------


def test_update_concept_title(client):
    client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    response = client.put("/api/v1/concepts/1", json={"title": "Updated title"})
    assert response.status_code == 200
    assert response.json()["title"] == "Updated title"
    # Unchanged fields must be preserved
    assert response.json()["description"] == VALID_PAYLOAD["description"]


def test_update_concept_not_found_returns_404(client):
    response = client.put("/api/v1/concepts/999", json={"title": "x" * 10})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /concepts/{id}
# ---------------------------------------------------------------------------


def test_delete_concept_returns_204(client):
    client.post("/api/v1/concepts", json=VALID_PAYLOAD)
    response = client.delete("/api/v1/concepts/1")
    assert response.status_code == 204

    # Verify it's gone
    assert client.get("/api/v1/concepts/1").status_code == 404


def test_delete_concept_not_found_returns_404(client):
    response = client.delete("/api/v1/concepts/999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
