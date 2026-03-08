"""Evaluations router — trigger and retrieve AI evaluations.

Route layout:
  POST  /concepts/{id}/evaluate    202  Trigger evaluation (async-style)
  GET   /concepts/{id}/evaluation  200  Retrieve evaluation result
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConceptNotFoundError,
    EvaluationExistsError,
    EvaluationNotFoundError,
)
from app.domain.schemas import ErrorResponse, EvaluationResponse
from app.infrastructure.database import get_db
from app.services import concept_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/concepts", tags=["evaluations"])


# ---------------------------------------------------------------------------
# POST /concepts/{id}/evaluate
# ---------------------------------------------------------------------------


@router.post(
    "/{concept_id}/evaluate",
    response_model=EvaluationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger RAG evaluation for a concept",
    responses={
        404: {"model": ErrorResponse, "description": "Concept not found"},
        409: {
            "model": ErrorResponse,
            "description": "Concept already has an evaluation",
        },
    },
)
def evaluate_concept(
    concept_id: int,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    """Run the RAG pipeline and store a structured evaluation.

    Returns ``202 Accepted`` because evaluation may take several seconds
    (embedding + LLM call).  The response body contains the completed
    evaluation once the synchronous pipeline finishes.
    """
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise ConceptNotFoundError(concept_id)

    if concept.evaluation is not None:
        raise EvaluationExistsError(concept_id)

    evaluation = rag_service.evaluate_concept(db, concept)
    
    # rag_service returns (evaluation, retrieved_chunks)
    evaluation_model, retrieved_chunks = evaluation
    
    # Build response with retrieved context
    return EvaluationResponse(
        id=evaluation_model.id,
        concept_id=evaluation_model.concept_id,
        novelty_score=evaluation_model.novelty_score,
        confidence_score=evaluation_model.confidence_score,
        mechanisms=evaluation_model.mechanisms,
        tradeoffs=evaluation_model.tradeoffs,
        regulatory_flags=evaluation_model.regulatory_flags,
        similar_references=evaluation_model.similar_references,
        existing_implementations=evaluation_model.existing_implementations,
        retrieved_context=retrieved_chunks,
        created_at=evaluation_model.created_at,
    )


# ---------------------------------------------------------------------------
# GET /concepts/{id}/evaluation
# ---------------------------------------------------------------------------


@router.get(
    "/{concept_id}/evaluation",
    response_model=EvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve the evaluation for a concept",
    responses={
        404: {"model": ErrorResponse, "description": "Concept or evaluation not found"},
    },
)
def get_evaluation(
    concept_id: int,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    """Retrieve stored evaluation and re-fetch retrieved context from ChromaDB."""
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise ConceptNotFoundError(concept_id)

    if concept.evaluation is None:
        raise EvaluationNotFoundError(concept_id)

    eval_model = concept.evaluation
    
    # Re-run vector search to get retrieved context
    # (Context is not persisted, but ChromaDB still has the same chunks)
    retrieved_chunks = rag_service.get_retrieved_context_for_concept(concept)
    
    return EvaluationResponse(
        id=eval_model.id,
        concept_id=eval_model.concept_id,
        novelty_score=eval_model.novelty_score,
        confidence_score=eval_model.confidence_score,
        mechanisms=eval_model.mechanisms,
        tradeoffs=eval_model.tradeoffs,
        regulatory_flags=eval_model.regulatory_flags,
        similar_references=eval_model.similar_references,
        existing_implementations=eval_model.existing_implementations,
        retrieved_context=retrieved_chunks,
        created_at=eval_model.created_at,
    )
