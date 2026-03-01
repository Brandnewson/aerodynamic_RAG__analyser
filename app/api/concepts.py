"""Concepts router — CRUD endpoints for AeroConcept resources.

Route layout:
  POST   /concepts                 201  Create a new concept
  GET    /concepts                 200  List concepts (paginated, filterable)
  GET    /concepts/{id}            200  Retrieve a single concept
  PUT    /concepts/{id}            200  Update a concept
  DELETE /concepts/{id}            204  Delete a concept
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.domain.schemas import (
    ConceptCreate,
    ConceptListResponse,
    ConceptResponse,
    ConceptStatus,
    ConceptUpdate,
    ErrorResponse,
)
from app.infrastructure.database import get_db
from app.services import concept_service

router = APIRouter(prefix="/concepts", tags=["concepts"])


# ---------------------------------------------------------------------------
# POST /concepts
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new aerodynamic concept",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def create_concept(
    payload: ConceptCreate,
    db: Session = Depends(get_db),
) -> ConceptResponse:
    """Create a new AeroConcept record with status ``SUBMITTED``."""
    concept = concept_service.create_concept(db, payload)
    return concept  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# GET /concepts
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ConceptListResponse,
    status_code=status.HTTP_200_OK,
    summary="List aerodynamic concepts",
)
def list_concepts(
    status: ConceptStatus | None = Query(
        None,
        description="Filter by lifecycle status (SUBMITTED | ANALYSED).",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Records per page."),
    db: Session = Depends(get_db),
) -> ConceptListResponse:
    """Return a paginated, optionally filtered list of concepts."""
    items, total = concept_service.list_concepts(
        db, status=status, page=page, page_size=page_size
    )
    return ConceptListResponse(
        items=items,  # type: ignore[arg-type]
        total=total,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# GET /concepts/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{concept_id}",
    response_model=ConceptResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single concept",
    responses={
        404: {"model": ErrorResponse, "description": "Concept not found"},
    },
)
def get_concept(
    concept_id: int,
    db: Session = Depends(get_db),
) -> ConceptResponse:
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id={concept_id} was not found.",
        )
    return concept  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# PUT /concepts/{id}
# ---------------------------------------------------------------------------


@router.put(
    "/{concept_id}",
    response_model=ConceptResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a concept",
    responses={
        404: {"model": ErrorResponse, "description": "Concept not found"},
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def update_concept(
    concept_id: int,
    payload: ConceptUpdate,
    db: Session = Depends(get_db),
) -> ConceptResponse:
    """Partially update a concept.  Only provided fields are written."""
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id={concept_id} was not found.",
        )
    updated = concept_service.update_concept(db, concept, payload)
    return updated  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# DELETE /concepts/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{concept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a concept",
    responses={
        404: {"model": ErrorResponse, "description": "Concept not found"},
    },
)
def delete_concept(
    concept_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Permanently delete a concept and its evaluation (if any)."""
    concept = concept_service.get_concept_by_id(db, concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept with id={concept_id} was not found.",
        )
    concept_service.delete_concept(db, concept)
