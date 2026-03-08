"""ConceptService — all business logic for AeroConcept CRUD.

The service layer sits between the API routers and the infrastructure
(database).  Routers are responsible for HTTP concerns (parsing requests,
returning responses); the service is responsible for domain rules.

Dependency injection:
  Each method receives a SQLAlchemy Session injected via FastAPI's
  ``Depends(get_db)`` at the router level — keeping this module
  framework-agnostic and easy to unit-test.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.models import AeroConcept, ConceptStatus
from app.domain.schemas import ConceptCreate, ConceptUpdate


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_concept_by_id(db: Session, concept_id: int) -> AeroConcept | None:
    """Return a single concept or ``None`` if not found."""
    return db.get(AeroConcept, concept_id)


def list_concepts(
    db: Session,
    *,
    status: ConceptStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AeroConcept], int]:
    """Return a paginated list of concepts and the total count.

    Args:
        db: Active SQLAlchemy session.
        status: Optional filter by lifecycle status.
        page: 1-based page number.
        page_size: Number of records per page (max 100).

    Returns:
        A (items, total) tuple.
    """
    page_size = min(page_size, 100)
    query = db.query(AeroConcept)

    if status is not None:
        query = query.filter(AeroConcept.status == status)

    total: int = query.count()
    items: list[AeroConcept] = (
        query.order_by(AeroConcept.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------


def create_concept(db: Session, payload: ConceptCreate) -> AeroConcept:
    """Persist a new concept and return the created record."""
    now = datetime.now(timezone.utc)
    concept = AeroConcept(
        title=payload.title,
        description=payload.description,
        author=payload.author,
        tags=payload.tags,
        status=ConceptStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
    )
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return concept


def update_concept(
    db: Session,
    concept: AeroConcept,
    payload: ConceptUpdate,
) -> AeroConcept:
    """Apply partial updates to an existing concept.

    Only fields explicitly provided in the payload (i.e. not ``None``)
    are written.  This implements HTTP PATCH semantics even though the
    route uses PUT, which is acceptable for a resource of this shape.
    """
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(concept, field, value)

    concept.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(concept)
    return concept


def delete_concept(db: Session, concept: AeroConcept) -> None:
    """Hard-delete a concept and its evaluation (cascade handles the FK)."""
    db.delete(concept)
    db.commit()
