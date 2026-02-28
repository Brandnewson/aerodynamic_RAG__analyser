"""RAGService — orchestrates retrieval and LLM evaluation.

This module is a *stub* at the scaffolding stage.
The full implementation will be wired during Phase 3 (ChromaDB retrieval)
and Phase 4 (OpenAI structured output).

The interface is defined here so the evaluation router can already import
and call ``evaluate_concept`` without breaking — it will return a
placeholder response until the implementation is filled in.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import AeroConcept, ConceptEvaluation, ConceptStatus
from app.domain.schemas import EvaluationResponse


class RAGService:
    """Coordinates embedding, retrieval, prompting, and result persistence."""

    def evaluate_concept(
        self, db: Session, concept: AeroConcept
    ) -> ConceptEvaluation:
        """Generate a structured evaluation for the given concept.

        Workflow (to be implemented):
          1. Embed ``concept.description`` via SentenceTransformers.
          2. Query ChromaDB for top-k similar literature chunks.
          3. Build a structured prompt from the chunks.
          4. Call OpenAI API and parse the JSON response.
          5. Persist the evaluation and update concept status.

        Currently returns a placeholder evaluation so the endpoint is
        exercisable end-to-end before the RAG pipeline is wired.
        """
        # --- STUB: replace with real implementation in Phase 3 / 4 ---
        placeholder_eval = ConceptEvaluation(
            concept_id=concept.id,
            novelty_score=0.0,
            confidence_score=0.0,
            mechanisms=["[RAG pipeline not yet wired]"],
            tradeoffs={"note": "Stub response — implementation pending"},
            regulatory_flags=[],
            similar_references=[],
            llm_raw_response="STUB",
        )
        db.add(placeholder_eval)
        concept.status = ConceptStatus.ANALYSED
        db.commit()
        db.refresh(placeholder_eval)
        return placeholder_eval


# Module-level singleton
rag_service = RAGService()
