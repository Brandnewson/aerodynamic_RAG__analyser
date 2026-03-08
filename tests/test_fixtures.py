"""Test fixtures and utilities for creating mock evaluation data.

Provides helper functions to create properly structured mock evaluations
that match the schema requirements.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

def create_mock_evaluation(
    concept_id: int,
    novelty_score: float = 0.8,
    confidence_score: float = 0.9,
    mechanisms: list[str] | None = None,
    tradeoffs: dict[str, str] | None = None,
):
    """Create a mock evaluation with proper structure."""
    from app.domain.models import ConceptEvaluation
    
    mock_eval = MagicMock(spec=ConceptEvaluation)
    mock_eval.id = 1
    mock_eval.concept_id = concept_id
    mock_eval.novelty_score = novelty_score
    mock_eval.confidence_score = confidence_score
    mock_eval.mechanisms = mechanisms or ["Test mechanism"]
    mock_eval.tradeoffs = tradeoffs or {"performance": "High", "complexity": "Medium"}
    mock_eval.regulatory_flags = []
    mock_eval.similar_references = []
    mock_eval.existing_implementations = []
    mock_eval.created_at = datetime.now(timezone.utc)
    
    return mock_eval


def create_mock_retrieved_chunks(count: int = 2):
    """Create mock retrieved context chunks."""
    return [
        {
            "text": f"Test context chunk {i+1}",
            "chunk_index": i,
            "similarity_score": 0.85 - (i * 0.1),
            "citation": {
                "arxiv_id": f"2301.{12345+i}",
                "title": f"Test Paper {i+1}",
                "authors": "Test Author",
                "published": "2024-01-01",
                "url": f"https://arxiv.org/abs/2301.{12345+i}",
            },
        }
        for i in range(count)
    ]
