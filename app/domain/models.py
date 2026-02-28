"""SQLAlchemy ORM models.

These are the *only* classes that map directly to database tables.
Domain logic lives in the service layer; these models are intentionally
kept as pure data structures.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ConceptStatus(str, enum.Enum):
    """Lifecycle state of an AeroConcept."""

    SUBMITTED = "SUBMITTED"   # Created, not yet evaluated
    ANALYSED = "ANALYSED"     # RAG + LLM evaluation complete
    ARCHIVED = "ARCHIVED"     # Soft-removed from active queries


# ---------------------------------------------------------------------------
# AeroConcept
# ---------------------------------------------------------------------------


class AeroConcept(Base):
    """Core entity: an aerodynamic design idea submitted for evaluation."""

    __tablename__ = "aero_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConceptStatus] = mapped_column(
        Enum(ConceptStatus),
        default=ConceptStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Stored as a JSON array of strings, e.g. ["downforce", "beam-wing"]
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # One-to-one relationship: a concept has at most one evaluation
    evaluation: Mapped[ConceptEvaluation | None] = relationship(
        "ConceptEvaluation",
        back_populates="concept",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AeroConcept id={self.id} title={self.title!r} status={self.status}>"


# ---------------------------------------------------------------------------
# ConceptEvaluation
# ---------------------------------------------------------------------------


class ConceptEvaluation(Base):
    """Stores the structured AI-generated analysis for a single concept."""

    __tablename__ = "concept_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("aero_concepts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # enforce one-to-one
    )

    # Scores (0.0 – 1.0)
    novelty_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Structured LLM output fields
    # e.g. ["Rear wake energisation", "Beam wing vortex interaction"]
    mechanisms: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # e.g. {"downforce_gain": "Moderate", "drag_penalty": "High"}
    tradeoffs: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    # e.g. ["May conflict with 2022 FIA beam wing restrictions"]
    regulatory_flags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # e.g. [{"title": "...", "similarity_score": 0.87}]
    similar_references: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Full raw LLM response — kept for debugging / audit
    llm_raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    concept: Mapped[AeroConcept] = relationship(
        "AeroConcept",
        back_populates="evaluation",
    )

    def __repr__(self) -> str:
        return (
            f"<ConceptEvaluation concept_id={self.concept_id} "
            f"novelty={self.novelty_score:.2f}>"
        )
