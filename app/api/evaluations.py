"""Evaluations router — trigger and retrieve AI evaluations.

Route layout:
  POST  /concepts/{id}/evaluate    202  Trigger evaluation (async-style)
  GET   /concepts/{id}/evaluation  200  Retrieve evaluation result
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id={concept_id} was not found.",
        )

    if concept.evaluation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Concept id={concept_id} already has an evaluation. "
                "Delete the concept and resubmit to re-evaluate."
            ),
        )

    evaluation = rag_service.evaluate_concept(db, concept)
    return evaluation  # type: ignore[return-value]


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
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id={concept_id} was not found.",
        )

    if concept.evaluation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Concept id={concept_id} has not been evaluated yet. "
                "POST /concepts/{id}/evaluate to trigger evaluation."
            ),
        )

    return concept.evaluation  # type: ignore[return-value]
