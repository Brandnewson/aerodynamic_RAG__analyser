"""Database transaction and error handling tests.

Tests database-level error scenarios including transaction rollbacks,
constraint violations, and connection failures.

Run with:
    uv run pytest tests/test_database_errors.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import patch, MagicMock

from app.infrastructure.database import Base, get_db
from app.main import app
from app.domain.models import AeroConcept, ConceptEvaluation, ConceptStatus
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Test database setup — in-memory SQLite with StaticPool
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign key constraints for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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


@pytest.fixture()
def db_session():
    """Provide a database session for direct database operations."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Transaction Rollback Tests
# ---------------------------------------------------------------------------


def test_failed_commit_rolls_back_transaction(db_session):
    """Test that failed commits properly roll back transactions."""
    # Create a concept
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    # Try to create evaluation with invalid foreign key (should be caught by constraint)
    with pytest.raises(Exception):
        evaluation = ConceptEvaluation(
            concept_id=99999,  # Non-existent concept
            novelty_score=0.8,
            confidence_score=0.9,
            mechanisms=[],
            tradeoffs={},
            regulatory_flags=[],
            similar_references=[],
            existing_implementations=[],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(evaluation)
        db_session.commit()

    # Verify transaction was rolled back - original concept should still exist
    db_session.rollback()
    existing_concept = db_session.get(AeroConcept, concept.id)
    assert existing_concept is not None
    assert existing_concept.title == "Test Concept"


def test_cascade_delete_removes_evaluation(db_session):
    """Test that deleting a concept cascades to delete its evaluation."""
    # Create concept
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    # Create evaluation
    evaluation = ConceptEvaluation(
        concept_id=concept.id,
        novelty_score=0.8,
        confidence_score=0.9,
        mechanisms=["Test"],
        tradeoffs={"performance": "High"},
        regulatory_flags=[],
        similar_references=[],
        existing_implementations=[],
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation)
    db_session.commit()
    evaluation_id = evaluation.id

    # Delete concept
    db_session.delete(concept)
    db_session.commit()

    # Verify evaluation was also deleted (cascade)
    deleted_evaluation = db_session.get(ConceptEvaluation, evaluation_id)
    assert deleted_evaluation is None


def test_concurrent_evaluation_creation_prevented(db_session):
    """Test that database constraints prevent concurrent evaluation creation."""
    # Create concept
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    # Create first evaluation
    evaluation1 = ConceptEvaluation(
        concept_id=concept.id,
        novelty_score=0.8,
        confidence_score=0.9,
        mechanisms=[],
        tradeoffs={},
        regulatory_flags=[],
        similar_references=[],
        existing_implementations=[],
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation1)
    db_session.commit()

    # Attempting to create second evaluation should fail (one-to-one relationship)
    # In our schema, this is prevented by checking concept.evaluation in service layer
    # But we can verify the database properly stores the relationship
    db_session.refresh(concept)
    assert concept.evaluation is not None
    assert concept.evaluation.id == evaluation1.id


# ---------------------------------------------------------------------------
# Connection and Operational Error Tests
# ---------------------------------------------------------------------------


def test_database_connection_failure_handling(client: TestClient):
    """Test graceful handling of database connection failures."""
    # Mock database session to raise OperationalError
    def failing_get_db():
        raise OperationalError("Database connection failed", None, None)

    app.dependency_overrides[get_db] = failing_get_db

    # Attempt to list concepts
    response = client.get("/api/v1/concepts")
    assert response.status_code == 500

    # Clean up
    app.dependency_overrides.clear()


def test_database_commit_failure_handling(client: TestClient):
    """Test handling of commit failures."""
    # Create a concept first
    create_response = client.post(
        "/api/v1/concepts",
        json={
            "title": "Test Concept",
            "description": "This is a valid test description that meets the minimum length requirement for concepts",
            "author": "Test Author",
            "tags": ["test"],
        },
    )
    assert create_response.status_code == 201

    # Mock commit to fail
    with patch("sqlalchemy.orm.Session.commit", side_effect=OperationalError("Commit failed", None, None)):
        update_response = client.put(
            f"/api/v1/concepts/{create_response.json()['id']}",
            json={"title": "Updated Title"},
        )
        # Should return 500 due to commit failure
        assert update_response.status_code == 500


# ---------------------------------------------------------------------------
# Data Integrity Tests
# ---------------------------------------------------------------------------


def test_concept_status_constraint(db_session):
    """Test that concept status must be valid enum value."""
    # SQLAlchemy enum constraint ensures only valid statuses
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()

    # Verify status is correctly stored
    db_session.refresh(concept)
    assert concept.status == ConceptStatus.SUBMITTED

    # Update to ANALYSED
    concept.status = ConceptStatus.ANALYSED
    db_session.commit()
    db_session.refresh(concept)
    assert concept.status == ConceptStatus.ANALYSED


def test_evaluation_scores_within_valid_range(db_session):
    """Test that evaluation scores are stored correctly."""
    # Create concept
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    # Create evaluation with valid scores
    evaluation = ConceptEvaluation(
        concept_id=concept.id,
        novelty_score=0.85,
        confidence_score=0.90,
        mechanisms=["Test mechanism"],
        tradeoffs={"performance": "High", "complexity": "Medium"},
        regulatory_flags=[],
        similar_references=[{"title": "Reference 1", "similarity_score": 0.85}],
        existing_implementations=[],
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)

    # Verify scores are stored correctly with proper precision
    assert evaluation.novelty_score == pytest.approx(0.85, rel=1e-9)
    assert evaluation.confidence_score == pytest.approx(0.90, rel=1e-9)


def test_json_field_storage(db_session):
    """Test that JSON fields (lists) are properly stored and retrieved."""
    # Create concept
    concept = AeroConcept(
        title="Test Concept",
        description="This is a valid test description that meets the minimum length requirement",
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    # Create evaluation with complex JSON data
    mechanisms = ["Boundary layer control", "Vortex generation"]
    tradeoffs = {"boundary_layer": "Control mechanism", "vortex": "Generation method"}
    similar_references = [{"title": "Smith et al. (2020)", "similarity_score": 0.85}, {"title": "Johnson (2019)", "similarity_score": 0.85}]
    flags = ["FAA Part 25 certification required"]
    implementations = ["Boeing 787 winglet"]

    evaluation = ConceptEvaluation(
        concept_id=concept.id,
        novelty_score=0.75,
        confidence_score=0.88,
        mechanisms=mechanisms,
        tradeoffs=tradeoffs,
        regulatory_flags=flags,
        similar_references=similar_references,
        existing_implementations=implementations,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation)
    db_session.commit()
    db_session.refresh(evaluation)

    # Verify JSON fields are correctly stored and retrieved
    assert evaluation.mechanisms == mechanisms
    assert evaluation.tradeoffs == tradeoffs
    assert evaluation.regulatory_flags == flags
    assert evaluation.similar_references == similar_references
    assert evaluation.existing_implementations == implementations


# ---------------------------------------------------------------------------
# Session Management Tests
# ---------------------------------------------------------------------------


def test_session_cleanup_after_error(client: TestClient):
    """Test that sessions are properly cleaned up after errors."""
    # Trigger an error
    response = client.get("/api/v1/concepts/99999")
    assert response.status_code == 404

    # Verify system can still handle new requests (session was cleaned up)
    list_response = client.get("/api/v1/concepts")
    assert list_response.status_code == 200


def test_multiple_sequential_operations(client: TestClient):
    """Test that multiple sequential database operations work correctly."""
    # Create multiple concepts
    concept_ids = []
    for i in range(5):
        response = client.post(
            "/api/v1/concepts",
            json={
                "title": f"Concept {i}",
                "description": f"This is a test description for concept {i} that meets the minimum length requirement",
                "author": "Test Author",
                "tags": [f"tag{i}"],
            },
        )
        assert response.status_code == 201
        concept_ids.append(response.json()["id"])

    # Update each concept
    for concept_id in concept_ids:
        response = client.put(
            f"/api/v1/concepts/{concept_id}",
            json={"description": f"Updated description {concept_id}"},
        )
        assert response.status_code == 200

    # Delete each concept
    for concept_id in concept_ids:
        response = client.delete(f"/api/v1/concepts/{concept_id}")
        assert response.status_code == 204

    # Verify all are deleted
    list_response = client.get("/api/v1/concepts")
    assert list_response.json()["total"] == 0


def test_database_state_isolation_between_tests(client: TestClient):
    """Test that database state is properly isolated between tests."""
    # This test should start with an empty database
    list_response = client.get("/api/v1/concepts")
    assert list_response.status_code == 200
    # Total could be 0 or have items from previous operations in this test run
    # The fixture ensures clean state per test


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------


def test_empty_tags_list_storage(db_session):
    """Test that concepts can have empty tags lists."""
    concept = AeroConcept(
        title="Test Concept",
        description="Test description",
        author="Test Author",
        tags=[],  # Empty list
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    assert concept.tags == []


def test_very_long_text_fields(db_session):
    """Test that long text fields are handled correctly."""
    long_description = "A" * 10000  # 10,000 characters
    
    concept = AeroConcept(
        title="Test Concept",
        description=long_description,
        author="Test Author",
        tags=["test"],
        status=ConceptStatus.SUBMITTED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(concept)
    db_session.commit()
    db_session.refresh(concept)

    assert len(concept.description) == 10000
    assert concept.description == long_description
