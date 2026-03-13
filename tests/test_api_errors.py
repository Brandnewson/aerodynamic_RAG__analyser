"""API error handling tests.

Tests all error scenarios including 404, 409, 422, 500, and 503 responses
to ensure proper error handling throughout the application.

Run with:
    uv run pytest tests/test_api_errors.py -v
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from tests.auth_helpers import authenticate_client
from app.infrastructure.database import Base, get_db
from app.main import app
from app.core.exceptions import VectorStoreError, LLMServiceError, DatabaseError
from app.domain.models import AeroConcept, ConceptEvaluation

# ---------------------------------------------------------------------------
# Test database setup — in-memory SQLite with StaticPool
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
    """Provide a TestClient backed by an isolated in-memory SQLite database."""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        authenticate_client(c)
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# 404 Not Found Tests
# ---------------------------------------------------------------------------


def test_get_nonexistent_concept_returns_404(client: TestClient):
    """GET /concepts/{id} for nonexistent concept returns 404."""
    response = client.get("/api/v1/concepts/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CONCEPT_NOT_FOUND"
    assert data["concept_id"] == 99999
    assert "not found" in data["detail"].lower()


def test_update_nonexistent_concept_returns_404(client: TestClient):
    """PUT /concepts/{id} for nonexistent concept returns 404."""
    response = client.put(
        "/api/v1/concepts/99999",
        json={"title": "Updated Title"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CONCEPT_NOT_FOUND"


def test_delete_nonexistent_concept_returns_404(client: TestClient):
    """DELETE /concepts/{id} for nonexistent concept returns 404."""
    response = client.delete("/api/v1/concepts/99999")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CONCEPT_NOT_FOUND"


def test_evaluate_nonexistent_concept_returns_404(client: TestClient):
    """POST /concepts/{id}/evaluate for nonexistent concept returns 404."""
    response = client.post("/api/v1/concepts/99999/evaluate")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CONCEPT_NOT_FOUND"


def test_get_evaluation_for_nonexistent_concept_returns_404(client: TestClient):
    """GET /concepts/{id}/evaluation for nonexistent concept returns 404."""
    response = client.get("/api/v1/concepts/99999/evaluation")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CONCEPT_NOT_FOUND"


def test_get_evaluation_for_unevaluated_concept_returns_404(client: TestClient):
    """GET /concepts/{id}/evaluation for concept without evaluation returns 404."""
    # Create a concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "This is a longer test description that meets the minimum length requirement",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    assert create_response.status_code == 201
    concept_id = create_response.json()["id"]

    # Try to get evaluation before evaluating
    response = client.get(f"/api/v1/concepts/{concept_id}/evaluation")
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "EVALUATION_NOT_FOUND"
    assert data["concept_id"] == concept_id


# ---------------------------------------------------------------------------
# 409 Conflict Tests
# ---------------------------------------------------------------------------


def test_duplicate_evaluation_returns_409(client: TestClient):
    """POST /concepts/{id}/evaluate twice returns 409 on second attempt."""
    # Create a concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "Test description for duplicate evaluation testing functionality",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    assert create_response.status_code == 201
    concept_id = create_response.json()["id"]

    # Create evaluation directly in database (bypass RAG service)
    db = TestingSessionLocal()
    try:
        evaluation = ConceptEvaluation(
            concept_id=concept_id,
            novelty_score=0.8,
            confidence_score=0.9,
            mechanisms=["Test mechanism"],
            tradeoffs={"performance": "High", "complexity": "Medium"},
            regulatory_flags=[],
            similar_references=[],
            existing_implementations=[],
            created_at=datetime.now(timezone.utc),
        )
        db.add(evaluation)
        
        # Update concept status
        concept = db.get(AeroConcept, concept_id)
        concept.status = "ANALYSED"
        db.commit()
    finally:
        db.close()

    # Second evaluation should fail with 409
    second_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
    assert second_response.status_code == 409
    data = second_response.json()
    assert data["code"] == "EVALUATION_EXISTS"
    assert data["concept_id"] == concept_id
    assert "already has an evaluation" in data["detail"]


# ---------------------------------------------------------------------------
# 422 Validation Error Tests
# ---------------------------------------------------------------------------


def test_create_concept_with_missing_fields_returns_422(client: TestClient):
    """POST /concepts with missing required fields returns 422."""
    response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            # Missing description, author, tags
        },
    )
    assert response.status_code == 422


def test_create_concept_with_invalid_data_types_returns_422(client: TestClient):
    """POST /concepts with invalid data types returns 422."""
    response = client.post(
        "/api/v1/concepts",
        json={
            "title": 123,  # Should be string
            "description": "Test",
            "author": "Test",
            "tags": "not-a-list",  # Should be array
        },
    )
    assert response.status_code == 422


def test_list_concepts_with_invalid_page_returns_422(client: TestClient):
    """GET /concepts with page < 1 returns 422."""
    response = client.get("/api/v1/concepts?page=0")
    assert response.status_code == 422


def test_list_concepts_with_invalid_page_size_returns_422(client: TestClient):
    """GET /concepts with page_size > 100 returns 422."""
    response = client.get("/api/v1/concepts?page_size=101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 503 Service Unavailable Tests (Infrastructure Failures)
# ---------------------------------------------------------------------------


def test_vector_store_failure_returns_503(client: TestClient):
    """Evaluation with vector store failure returns 503."""
    # Create a concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "Test for vector store failure",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    assert create_response.status_code == 201
    concept_id = create_response.json()["id"]

    # Mock vector store to raise error
    with patch(
        "app.services.rag_service.rag_service.evaluate_concept",
        side_effect=VectorStoreError("ChromaDB connection failed", operation="query"),
    ):
        response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == "VECTOR_STORE_ERROR"
        assert "ChromaDB" in data["detail"]


def test_llm_service_failure_returns_503(client: TestClient):
    """Evaluation with LLM failure returns 503."""
    # Create a concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "Test for LLM failure",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    assert create_response.status_code == 201
    concept_id = create_response.json()["id"]

    # Mock LLM service to raise error
    with patch(
        "app.services.rag_service.rag_service.evaluate_concept",
        side_effect=LLMServiceError(
            "OpenAI API rate limit exceeded", model="gpt-4o", error_type="rate_limit"
        ),
    ):
        response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == "LLM_SERVICE_ERROR"
        assert "rate limit" in data["detail"].lower()


# ---------------------------------------------------------------------------
# 500 Internal Server Error Tests
# ---------------------------------------------------------------------------


def test_database_error_returns_500(client: TestClient):
    """Database errors are handled with 500 status."""
    # Mock database operation to raise error
    with patch(
        "app.services.concept_service.create_concept",
        side_effect=DatabaseError("Database write failed", operation="insert"),
    ):
        response = client.post(
            "/api/v1/concepts",
            json={
                "title": "Test Concept",
                "description": "This is a test description for database failure simulation case",
                "author": "Test Author",
                "tags": ["test"],
            },
        )
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "DATABASE_ERROR"


def test_unexpected_error_returns_500(client: TestClient):
    """Unexpected exceptions return 500 with error details."""
    # Create a new TestClient that doesn't raise server exceptions
    # so we can test the error response
    test_client = TestClient(app, raise_server_exceptions=False)
    authenticate_client(test_client, username="runtime_error_user")
    
    # Mock service to raise unexpected exception
    with patch(
        "app.services.concept_service.list_concepts",
        side_effect=RuntimeError("Unexpected error"),
    ):
        response = test_client.get("/api/v1/concepts")
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == "INTERNAL_ERROR"
        assert "unexpected" in data["detail"].lower() or "error" in data["detail"].lower()


# ---------------------------------------------------------------------------
# Error Response Structure Tests
# ---------------------------------------------------------------------------


def test_error_responses_have_consistent_structure(client: TestClient):
    """All error responses follow consistent structure with detail and code."""
    # Test 404
    response_404 = client.get("/api/v1/concepts/99999")
    assert "detail" in response_404.json()
    assert "code" in response_404.json()

    # Test 422
    response_422 = client.post("/api/v1/concepts", json={"title": "Incomplete"})
    assert "detail" in response_422.json()

    # Create and evaluate a concept for 409 test
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "This is a valid test description for error response structure testing",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    concept_id = create_response.json()["id"]

    # Create evaluation directly in database
    db = TestingSessionLocal()
    try:
        evaluation = ConceptEvaluation(
            concept_id=concept_id,
            novelty_score=0.8,
            confidence_score=0.9,
            mechanisms=[],
            tradeoffs={},
            regulatory_flags=[],
            similar_references=[],
            existing_implementations=[],
            created_at=datetime.now(timezone.utc),
        )
        db.add(evaluation)
        concept = db.get(AeroConcept, concept_id)
        concept.status = "ANALYSED"
        db.commit()
    finally:
        db.close()

    # Test 409
    response_409 = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
    assert "detail" in response_409.json()
    assert "code" in response_409.json()
