"""End-to-end integration tests.

Tests complete user workflows from concept creation to evaluation retrieval,
ensuring all components work together correctly.

Run with:
    uv run pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from app.infrastructure.database import Base, get_db
from app.main import app

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
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Complete User Workflow Tests
# ---------------------------------------------------------------------------


def test_complete_concept_lifecycle(client: TestClient):
    """Test complete workflow: create → list → get → update → evaluate → get evaluation → delete."""
    
    # Step 1: Create a concept
    create_payload = {
        "title": "Morphing Wing with Adaptive Camber",
        "description": "A wing design that changes camber in flight to optimize for different phases",
        "author": "Test Engineer",
        "tags": ["morphing", "adaptive", "wing"],
    }
    create_response = client.post("/api/v1/concepts", json=create_payload)
    assert create_response.status_code == 201
    concept_data = create_response.json()
    concept_id = concept_data["id"]
    assert concept_data["title"] == create_payload["title"]
    assert concept_data["status"] == "SUBMITTED"

    # Step 2: List concepts (should include our new concept)
    list_response = client.get("/api/v1/concepts")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 1
    assert any(c["id"] == concept_id for c in list_data["items"])

    # Step 3: Get specific concept
    get_response = client.get(f"/api/v1/concepts/{concept_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["id"] == concept_id
    assert get_data["title"] == create_payload["title"]

    # Step 4: Update concept
    update_payload = {
        "description": "Updated: A wing design with variable geometry control surfaces"
    }
    update_response = client.put(f"/api/v1/concepts/{concept_id}", json=update_payload)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["description"] == update_payload["description"]
    assert updated_data["title"] == create_payload["title"]  # Unchanged

    # Step 5: Evaluate concept (mock vector store and LLM)
    with patch("app.services.rag_service.vector_store.query") as mock_vector:
        with patch("app.services.rag_service.get_llm_client") as mock_llm_client:
            # Mock vector store to return empty chunks
            mock_vector.return_value = []
            
            # Mock LLM to return valid JSON response
            mock_llm = MagicMock()
            mock_llm.chat.return_value = '''{
                "novelty_score": 0.75,
                "confidence_score": 0.85,
                "mechanisms": ["Variable geometry control surfaces", "Adaptive trailing edge"],
                "tradeoffs": {
                    "mechanical_complexity": "Increased actuator count",
                    "weight_penalty": "5-10% mass addition from mechanisms"
                },
                "regulatory_flags": ["Requires structural certification"],
                "similar_references": [
                    {"title": "NASA Mission Adaptive Wing (1985)", "similarity_score": 0.85},
                    {"title": "AFTI/F-111 research program", "similarity_score": 0.80}
                ],
                "existing_implementations": []
            }'''
            mock_llm_client.return_value = mock_llm

            eval_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
            assert eval_response.status_code == 202
            eval_data = eval_response.json()
            assert eval_data["concept_id"] == concept_id
            assert eval_data["novelty_score"] == 0.75
            assert eval_data["confidence_score"] == 0.85
            assert len(eval_data["mechanisms"]) == 2

    # Step 6: Get evaluation
    with patch(
        "app.services.rag_service.rag_service.get_retrieved_context_for_concept"
    ) as mock_context:
        mock_context.return_value = []
        
        get_eval_response = client.get(f"/api/v1/concepts/{concept_id}/evaluation")
        assert get_eval_response.status_code == 200
        get_eval_data = get_eval_response.json()
        assert get_eval_data["novelty_score"] == 0.75
        assert len(get_eval_data["mechanisms"]) == 2

    # Step 7: Verify concept status changed to ANALYSED
    final_get_response = client.get(f"/api/v1/concepts/{concept_id}")
    final_data = final_get_response.json()
    assert final_data["status"] == "ANALYSED"

    # Step 8: Delete concept
    delete_response = client.delete(f"/api/v1/concepts/{concept_id}")
    assert delete_response.status_code == 204

    # Step 9: Verify deletion
    get_deleted_response = client.get(f"/api/v1/concepts/{concept_id}")
    assert get_deleted_response.status_code == 404


def test_multiple_concepts_workflow(client: TestClient):
    """Test managing multiple concepts simultaneously."""
    
    # Create multiple concepts
    concepts = []
    for i in range(3):
        payload = {
            "title": f"Concept {i+1}",
            "description": f"Test concept number {i+1}",
            "author": "Test Engineer",
            "tags": [f"test{i+1}"],
        }
        response = client.post("/api/v1/concepts", json=payload)
        assert response.status_code == 201
        concepts.append(response.json())

    # List all concepts
    list_response = client.get("/api/v1/concepts")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 3

    # Filter by status
    filter_response = client.get("/api/v1/concepts?status=SUBMITTED")
    assert filter_response.status_code == 200
    assert filter_response.json()["total"] == 3

    # Test pagination
    page1_response = client.get("/api/v1/concepts?page=1&page_size=2")
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    assert len(page1_data["items"]) == 2
    assert page1_data["total"] == 3

    page2_response = client.get("/api/v1/concepts?page=2&page_size=2")
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    assert len(page2_data["items"]) == 1


def test_evaluation_caching_behavior(client: TestClient):
    """Test that evaluations are cached and not re-run."""
    
    # Create concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Caching",
            "description": "This is a test description for evaluation caching that meets minimum length",
            "author": "Test",
            "tags": ["cache"],
        },
    )
    concept_id = create_response.json()["id"]

    # First evaluation - mock vector store and LLM but let evaluation save to DB
    with patch("app.services.rag_service.vector_store.query") as mock_vector:
        with patch("app.services.rag_service.get_llm_client") as mock_llm_client:
            # Mock vector store to return empty chunks
            mock_vector.return_value = []
            
            # Mock LLM to return valid JSON response
            mock_llm = MagicMock()
            mock_llm.chat.return_value = '''{
                "novelty_score": 0.8,
                "confidence_score": 0.9,
                "mechanisms": ["Test mechanism"],
                "tradeoffs": {"performance": "High"},
                "regulatory_flags": [],
                "similar_references": [],
                "existing_implementations": []
            }'''
            mock_llm_client.return_value = mock_llm
            
            eval_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
            assert eval_response.status_code == 202

    # Second evaluation attempt should fail (409 Conflict)
    second_eval_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
    assert second_eval_response.status_code == 409
    assert "already has an evaluation" in second_eval_response.json()["detail"]


def test_health_check_endpoint(client: TestClient):
    """Test system health check returns component status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "vector_store" in data["components"]
    assert "llm" in data["components"]


def test_mcp_discovery_endpoint(client: TestClient):
    """Test MCP integration discovery endpoint."""
    response = client.get("/api/v1/mcp")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "available"
    assert "tools" in data
    assert len(data["tools"]) == 4
    assert "list_concepts" in data["tools"]
    assert "create_concept" in data["tools"]
    assert "evaluate_concept" in data["tools"]
    assert "get_evaluation" in data["tools"]


def test_error_recovery_workflow(client: TestClient):
    """Test that the system recovers gracefully from errors."""
    
    # Attempt to evaluate non-existent concept
    eval_response = client.post("/api/v1/concepts/99999/evaluate")
    assert eval_response.status_code == 404

    # Create a valid concept after error
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Recovery Test",
            "description": "Test recovery after error",
            "author": "Test",
            "tags": ["recovery"],
        },
    )
    assert create_response.status_code == 201  # System recovered

    # Attempt to get evaluation before evaluating
    concept_id = create_response.json()["id"]
    get_eval_response = client.get(f"/api/v1/concepts/{concept_id}/evaluation")
    assert get_eval_response.status_code == 404

    # Successfully evaluate after previous error
    with patch("app.services.rag_service.rag_service.evaluate_concept") as mock:
        from app.domain.models import ConceptEvaluation
        from datetime import datetime, timezone

        mock_evaluation = MagicMock(spec=ConceptEvaluation)
        mock_evaluation.id = 1
        mock_evaluation.concept_id = concept_id
        mock_evaluation.novelty_score = 0.7
        mock_evaluation.confidence_score = 0.8
        mock_evaluation.mechanisms = []
        mock_evaluation.tradeoffs = {}
        mock_evaluation.regulatory_flags = []
        mock_evaluation.similar_references = []
        mock_evaluation.existing_implementations = []
        mock_evaluation.created_at = datetime.now(timezone.utc)

        mock.return_value = (mock_evaluation, [])
        
        eval_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
        assert eval_response.status_code == 202


def test_update_preservation_of_evaluation(client: TestClient):
    """Test that updating a concept preserves its evaluation."""
    
    # Create and evaluate concept
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Preservation",
            "description": "This is an original description that meets the minimum length requirement",
            "author": "Test",
            "tags": ["test"],
        },
    )
    concept_id = create_response.json()["id"]

    # Evaluate concept - mock vector store and LLM but let evaluation save to DB
    with patch("app.services.rag_service.vector_store.query") as mock_vector:
        with patch("app.services.rag_service.get_llm_client") as mock_llm_client:
            mock_vector.return_value = []
            mock_llm = MagicMock()
            mock_llm.chat.return_value = '''{
                "novelty_score": 0.9,
                "confidence_score": 0.95,
                "mechanisms": ["Mechanism 1"],
                "tradeoffs": {"performance": "High"},
                "regulatory_flags": [],
                "similar_references": [],
                "existing_implementations": []
            }'''
            mock_llm_client.return_value = mock_llm
            
            client.post(f"/api/v1/concepts/{concept_id}/evaluate")

    # Update concept
    update_response = client.put(
        f"/api/v1/concepts/{concept_id}",
        json={"description": "This is an updated description that also meets the minimum length requirement"},
    )
    assert update_response.status_code == 200

    # Verify evaluation still exists
    with patch(
        "app.services.rag_service.rag_service.get_retrieved_context_for_concept"
    ) as mock_context:
        mock_context.return_value = []
        
        get_eval_response = client.get(f"/api/v1/concepts/{concept_id}/evaluation")
        assert get_eval_response.status_code == 200
        eval_data = get_eval_response.json()
        assert eval_data["novelty_score"] == 0.9  # Preserved


def test_report_lifecycle_workflow(client: TestClient):
    """Test complete report workflow: upload -> list -> get -> update -> delete."""

    with patch("app.services.report_service.extract_pdf_text", return_value="D" * 260):
        with patch("app.services.report_service._embed_chunks", return_value=[[0.1, 0.2, 0.3]]):
            with patch("app.services.report_service.vector_store.add_documents"):
                create_response = client.post(
                    "/api/v1/reports",
                    files={"file": ("workflow.pdf", b"%PDF-1.4 fake", "application/pdf")},
                    data={"title": "Workflow Report", "tags": "alpha,beta"},
                )

    assert create_response.status_code == 201
    report_id = create_response.json()["id"]
    assert create_response.json()["chunk_count"] == 1

    list_response = client.get("/api/v1/reports")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(f"/api/v1/reports/{report_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Workflow Report"

    with patch("app.services.report_service._embed_chunks", return_value=[[0.5, 0.6, 0.7]]):
        with patch("app.services.report_service.vector_store.delete_where"):
            with patch("app.services.report_service.vector_store.add_documents"):
                update_response = client.put(
                    f"/api/v1/reports/{report_id}",
                    json={
                        "content": "Updated workflow report content that is long enough for validation.",
                        "title": "Workflow Report v2",
                    },
                )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Workflow Report v2"

    with patch("app.services.report_service.vector_store.delete_where"):
        delete_response = client.delete(f"/api/v1/reports/{report_id}")
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/api/v1/reports/{report_id}")
    assert get_deleted.status_code == 404
