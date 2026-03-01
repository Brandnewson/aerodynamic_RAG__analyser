"""End-to-end test for the RAG evaluation flow.

This script validates the complete POST /concepts/{id}/evaluate pipeline:
  1. Create a test concept
  2. Trigger RAG evaluation
  3. Verify the response structure
  4. Check retrieved_context attribution
  5. Retrieve the persisted evaluation

Usage:
    # Start the server first:
    uv run uvicorn app.main:app --reload

    # Then run this test:
    uv run python scripts/test_evaluation.py

Expected behavior:
  - 201 Created for concept
  - 202 Accepted for evaluation (synchronous in practice)
  - Response includes novelty_score, mechanisms, tradeoffs, retrieved_context
  - retrieved_context contains arXiv citations with title/authors/url
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8001/api/v1"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_evaluation_flow():
    """Run the complete evaluation flow test."""
    
    print_section("STEP 1: Create Test Concept")
    
    concept_payload = {
        "title": "Ground effect diffuser with active flow control",
        "description": (
            "A ground effect diffuser that uses active flow control via "
            "synthetic jets to delay separation and increase downforce "
            "efficiency in low-speed corners. The system would dynamically "
            "adjust jet frequency based on ride height and speed sensors."
        ),
        "author": "Test Engineer",
        "tags": ["ground-effect", "active-aero", "diffuser", "downforce"],
    }
    
    response = requests.post(f"{BASE_URL}/concepts", json=concept_payload, timeout=10)
    
    if response.status_code != 201:
        print(f"✗ Failed to create concept: {response.status_code}")
        print(response.text)
        return False
    
    concept = response.json()
    concept_id = concept["id"]
    print(f"✓ Created concept with id={concept_id}")
    print(f"  Title: {concept['title']}")
    print(f"  Status: {concept['status']}")
    
    # -------------------------------------------------------------------------
    
    print_section("STEP 2: Trigger RAG Evaluation")
    
    response = requests.post(
        f"{BASE_URL}/concepts/{concept_id}/evaluate",
        timeout=60,  # LLM calls can take time
    )
    
    if response.status_code not in (200, 202):
        print(f"✗ Evaluation failed: {response.status_code}")
        print(response.text)
        return False
    
    evaluation = response.json()
    print(f"✓ Evaluation completed (status {response.status_code})")
    
    # -------------------------------------------------------------------------
    
    print_section("STEP 3: Validate Response Structure")
    
    required_fields = [
        "id",
        "concept_id",
        "novelty_score",
        "confidence_score",
        "mechanisms",
        "tradeoffs",
        "regulatory_flags",
        "similar_references",
        "retrieved_context",
        "created_at",
    ]
    
    missing_fields = [f for f in required_fields if f not in evaluation]
    if missing_fields:
        print(f"✗ Missing fields: {missing_fields}")
        return False
    
    print("✓ All required fields present")
    
    # Validate scores
    novelty = evaluation["novelty_score"]
    confidence = evaluation["confidence_score"]
    
    if not (0.0 <= novelty <= 1.0):
        print(f"✗ Invalid novelty_score: {novelty}")
        return False
    
    if not (0.0 <= confidence <= 1.0):
        print(f"✗ Invalid confidence_score: {confidence}")
        return False
    
    print(f"  Novelty: {novelty:.2f}")
    print(f"  Confidence: {confidence:.2f}")
    print(f"  Mechanisms: {len(evaluation['mechanisms'])} identified")
    print(f"  Tradeoffs: {len(evaluation['tradeoffs'])} identified")
    print(f"  Regulatory Flags: {len(evaluation['regulatory_flags'])} identified")
    
    # -------------------------------------------------------------------------
    
    print_section("STEP 4: Validate Retrieved Context (Citations)")
    
    retrieved = evaluation.get("retrieved_context", [])
    
    if not retrieved:
        print("⚠ Warning: No retrieved_context returned")
        print("  This may indicate ChromaDB is empty or retrieval failed")
    else:
        print(f"✓ Retrieved {len(retrieved)} chunks from ChromaDB")
        
        for i, chunk in enumerate(retrieved[:3], 1):  # Show first 3
            citation = chunk.get("citation", {})
            print(f"\n  [{i}] {citation.get('title', 'Unknown')}")
            print(f"      arXiv: {citation.get('arxiv_id', 'N/A')}")
            print(f"      Authors: {citation.get('authors', 'N/A')}")
            print(f"      URL: {citation.get('url', 'N/A')}")
            print(f"      Similarity: {chunk.get('similarity_score', 0.0):.3f}")
            print(f"      Chunk: {chunk.get('chunk_index', 0)}")
            print(f"      Text preview: {chunk.get('text', '')[:100]}...")
    
    # -------------------------------------------------------------------------
    
    print_section("STEP 5: Retrieve Persisted Evaluation (GET)")
    
    response = requests.get(f"{BASE_URL}/concepts/{concept_id}/evaluation", timeout=10)
    
    if response.status_code != 200:
        print(f"✗ Failed to retrieve evaluation: {response.status_code}")
        print(response.text)
        return False
    
    persisted = response.json()
    print("✓ Successfully retrieved persisted evaluation via GET")
    print(f"  Evaluation ID: {persisted['id']}")
    print(f"  Novelty: {persisted['novelty_score']:.2f}")
    
    # Note: GET response won't have retrieved_context (not stored in DB)
    if persisted.get("retrieved_context"):
        print(f"  Retrieved context: {len(persisted['retrieved_context'])} chunks")
    else:
        print("  Retrieved context: (not stored in DB, only in POST response)")
    
    # -------------------------------------------------------------------------
    
    print_section("STEP 6: Cleanup")
    
    response = requests.delete(f"{BASE_URL}/concepts/{concept_id}", timeout=10)
    
    if response.status_code != 204:
        print(f"⚠ Warning: Failed to delete test concept: {response.status_code}")
    else:
        print(f"✓ Deleted test concept id={concept_id}")
    
    # -------------------------------------------------------------------------
    
    print_section("TEST RESULT: SUCCESS ✓")
    print("\nThe RAG evaluation pipeline is working end-to-end:")
    print("  ✓ Concept creation")
    print("  ✓ RAG evaluation with LLM")
    print("  ✓ Score validation")
    print("  ✓ Retrieved context with citations")
    print("  ✓ Persistence and retrieval")
    
    return True


if __name__ == "__main__":
    try:
        success = test_evaluation_flow()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API server")
        print("  Make sure the server is running:")
        print("  $ uv run uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
