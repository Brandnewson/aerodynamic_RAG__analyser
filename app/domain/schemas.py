"""Pydantic schemas — request bodies, response models, and error shapes.

Schemas are *separate* from ORM models by design:
  - ORM models: persistence (what the DB stores)
  - Schemas: API contract (what clients send and receive)

This boundary makes it possible to change either layer independently.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enumerations (mirrored from domain.models to keep schemas independent)
# ---------------------------------------------------------------------------


class ConceptStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ANALYSED = "ANALYSED"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# AeroConcept — request schemas
# ---------------------------------------------------------------------------


class ConceptCreate(BaseModel):
    """Payload for POST /concepts."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="A short, descriptive title for the aerodynamic concept.",
        examples=["Double-element beam wing for rear load consistency"],
    )
    description: str = Field(
        ...,
        min_length=20,
        description=(
            "Detailed description of the aerodynamic concept, including "
            "intended mechanism, target operating conditions, and any "
            "known trade-offs."
        ),
        examples=[
            "Introduce a double-element beam wing to improve rear load "
            "consistency in medium-speed corners by energising the rear wake."
        ],
    )
    author: str | None = Field(
        None,
        max_length=255,
        description="Optional name of the engineer or researcher submitting the concept.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional taxonomy tags, e.g. ['downforce', 'beam-wing', 'F1'].",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def _normalise_tags(cls, v: Any) -> list[str]:
        if v is None:
            return []
        return [str(t).strip() for t in v if str(t).strip()]


class ConceptUpdate(BaseModel):
    """Payload for PUT /concepts/{id}.  All fields are optional."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=20)
    author: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    status: ConceptStatus | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def _normalise_tags(cls, v: Any) -> list[str] | None:
        if v is None:
            return None
        return [str(t).strip() for t in v if str(t).strip()]


# ---------------------------------------------------------------------------
# AeroConcept — response schemas
# ---------------------------------------------------------------------------


class ConceptResponse(BaseModel):
    """Full representation of a single concept returned by the API."""

    id: int
    title: str
    description: str
    status: ConceptStatus
    author: str | None
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConceptListResponse(BaseModel):
    """Paginated list of concepts."""

    items: list[ConceptResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# ConceptEvaluation — response schemas
# ---------------------------------------------------------------------------


class SimilarReference(BaseModel):
    title: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)


class EvaluationResponse(BaseModel):
    """Structured AI evaluation result returned to clients."""

    id: int
    concept_id: int
    novelty_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    mechanisms: list[str]
    tradeoffs: dict[str, str]
    regulatory_flags: list[str]
    similar_references: list[SimilarReference]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Error schema — consistent error envelope
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
