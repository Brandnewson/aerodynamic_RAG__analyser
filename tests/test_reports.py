"""Tests for /api/v1/reports CRUD endpoints."""

from __future__ import annotations

from unittest.mock import patch

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


def _pdf_upload_payload(filename: str = "report.pdf"):
    return {
        "file": (filename, b"%PDF-1.4 fake", "application/pdf"),
    }


def test_create_report_returns_201(client: TestClient):
    with patch("app.services.report_service.extract_pdf_text", return_value="A" * 240):
        with patch("app.services.report_service._embed_chunks", return_value=[[0.1, 0.2, 0.3]]):
            with patch("app.services.report_service.vector_store.add_documents"):
                response = client.post(
                    "/api/v1/reports",
                    files=_pdf_upload_payload(),
                    data={"title": "Wind Tunnel Run", "author": "QA", "tags": "lift,drag"},
                )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Wind Tunnel Run"
    assert data["source_filename"] == "report.pdf"
    assert data["chunk_count"] == 1
    assert data["tags"] == ["lift", "drag"]


def test_create_report_rejects_non_pdf(client: TestClient):
    response = client.post(
        "/api/v1/reports",
        files={"file": ("report.txt", b"hello", "text/plain")},
        data={"title": "Bad Upload"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_report_vector_store_failure_returns_503(client: TestClient):
    with patch("app.services.report_service.extract_pdf_text", return_value="B" * 240):
        with patch("app.services.report_service._embed_chunks", return_value=[[0.1, 0.2, 0.3]]):
            with patch(
                "app.services.report_service.vector_store.add_documents",
                side_effect=RuntimeError("boom"),
            ):
                response = client.post(
                    "/api/v1/reports",
                    files=_pdf_upload_payload(),
                    data={"title": "Will Fail"},
                )

    assert response.status_code == 503
    assert response.json()["code"] == "VECTOR_STORE_ERROR"

    list_response = client.get("/api/v1/reports")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0


def test_report_crud_flow(client: TestClient):
    with patch("app.services.report_service.extract_pdf_text", return_value="C" * 240):
        with patch("app.services.report_service._embed_chunks", return_value=[[0.1, 0.2, 0.3]]):
            with patch("app.services.report_service.vector_store.add_documents"):
                create_response = client.post(
                    "/api/v1/reports",
                    files=_pdf_upload_payload(),
                    data={"title": "Baseline Report", "author": "Author One", "tags": "baseline"},
                )

    assert create_response.status_code == 201
    report_id = create_response.json()["id"]

    list_response = client.get("/api/v1/reports")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(f"/api/v1/reports/{report_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Baseline Report"

    with patch("app.services.report_service._embed_chunks", return_value=[[0.4, 0.5, 0.6]]):
        with patch("app.services.report_service.vector_store.delete_where") as mock_delete:
            with patch("app.services.report_service.vector_store.add_documents") as mock_add:
                update_response = client.put(
                    f"/api/v1/reports/{report_id}",
                    json={
                        "title": "Updated Report",
                        "content": "Updated content with enough detail to pass validation for reindexing.",
                        "tags": ["updated"],
                    },
                )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Report"
    assert update_response.json()["tags"] == ["updated"]
    assert mock_delete.called
    assert mock_add.called

    with patch("app.services.report_service.vector_store.delete_where") as mock_delete:
        delete_response = client.delete(f"/api/v1/reports/{report_id}")
    assert delete_response.status_code == 204
    assert mock_delete.called

    missing_response = client.get(f"/api/v1/reports/{report_id}")
    assert missing_response.status_code == 404
    assert missing_response.json()["code"] == "REPORT_NOT_FOUND"


def test_list_indexed_reports_returns_grouped_results(client: TestClient):
    with patch("app.services.report_service.extract_pdf_text", return_value="E" * 260):
        with patch("app.services.report_service._embed_chunks", return_value=[[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]]):
            with patch("app.services.report_service.vector_store.add_documents"):
                create_response = client.post(
                    "/api/v1/reports",
                    files=_pdf_upload_payload(),
                    data={"title": "Indexable Report", "author": "Ops", "tags": "alpha,beta"},
                )

    assert create_response.status_code == 201

    with patch(
        "app.services.report_service.vector_store.list_chunks",
        return_value=[
            {
                "id": "report_1::chunk::0",
                "document": "Baseline wind tunnel result with alpha sweep.",
                "metadata": {
                    "report_id": 1,
                    "title": "Indexable Report",
                    "source_filename": "report.pdf",
                    "author": "Ops",
                    "tags": "alpha,beta",
                    "source_type": "report",
                },
            },
            {
                "id": "report_1::chunk::1",
                "document": "Secondary chunk discussing drag minimization.",
                "metadata": {
                    "report_id": 1,
                    "title": "Indexable Report",
                    "source_filename": "report.pdf",
                    "author": "Ops",
                    "tags": "alpha,beta",
                    "source_type": "report",
                },
            },
        ],
    ):
        response = client.get("/api/v1/reports/index")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["report_id"] == 1
    assert payload["items"][0]["indexed_chunk_count"] == 2
    assert payload["items"][0]["matched_chunk_count"] == 2

    with patch(
        "app.services.report_service.vector_store.list_chunks",
        return_value=[
            {
                "id": "report_1::chunk::0",
                "document": "Baseline wind tunnel result with alpha sweep.",
                "metadata": {
                    "report_id": 1,
                    "title": "Indexable Report",
                    "source_filename": "report.pdf",
                    "author": "Ops",
                    "tags": "alpha,beta",
                    "source_type": "report",
                },
            }
        ],
    ):
        filtered = client.get("/api/v1/reports/index?query=alpha")

    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


def test_list_indexed_reports_vector_store_failure_returns_503(client: TestClient):
    with patch(
        "app.services.report_service.vector_store.list_chunks",
        side_effect=RuntimeError("vector down"),
    ):
        response = client.get("/api/v1/reports/index")

    assert response.status_code == 503
    assert response.json()["code"] == "VECTOR_STORE_ERROR"


def test_update_and_delete_report_not_found(client: TestClient):
    update_response = client.put("/api/v1/reports/999", json={"title": "x" * 5})
    assert update_response.status_code == 404

    delete_response = client.delete("/api/v1/reports/999")
    assert delete_response.status_code == 404
