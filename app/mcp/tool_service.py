from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.domain.models import ConceptStatus
from app.domain.schemas import ConceptCreate, ConceptListResponse, ConceptResponse, EvaluationResponse
from app.infrastructure.database import SessionLocal
from app.services import concept_service
from app.services.rag_service import rag_service


class MCPToolService:
    """Thin service adapter used by MCP tools.

    Keeps MCP transport concerns separate from business/domain logic and reuses
    existing service-layer functions and API schemas for consistent contracts.
    """

    @contextmanager
    def _db_session(self) -> Generator[Session, None, None]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def list_concepts(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        status_enum = self._parse_status(status)

        with self._db_session() as db:
            items, total = concept_service.list_concepts(
                db,
                status=status_enum,
                page=page,
                page_size=page_size,
            )
            payload = ConceptListResponse(
                items=[ConceptResponse.model_validate(item) for item in items],
                total=total,
                page=page,
                page_size=page_size,
            )
            return payload.model_dump(mode="json")

    def create_concept(self, *, title: str, description: str, author: str | None = None, tags: list[str] | None = None) -> dict:
        concept_in = ConceptCreate(
            title=title,
            description=description,
            author=author,
            tags=tags or [],
        )

        with self._db_session() as db:
            concept = concept_service.create_concept(db, concept_in)
            return ConceptResponse.model_validate(concept).model_dump(mode="json")

    def evaluate_concept(self, *, concept_id: int) -> dict:
        with self._db_session() as db:
            concept = concept_service.get_concept_by_id(db, concept_id)
            if concept is None:
                raise ValueError(f"Concept with id={concept_id} was not found.")

            if concept.evaluation is not None:
                raise ValueError(
                    f"Concept id={concept_id} already has an evaluation. "
                    "Delete the concept and resubmit to re-evaluate."
                )

            evaluation_model, retrieved_chunks = rag_service.evaluate_concept(db, concept)
            response = EvaluationResponse(
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
            return response.model_dump(mode="json")

    def get_evaluation(self, *, concept_id: int) -> dict:
        with self._db_session() as db:
            concept = concept_service.get_concept_by_id(db, concept_id)
            if concept is None:
                raise ValueError(f"Concept with id={concept_id} was not found.")

            if concept.evaluation is None:
                raise ValueError(
                    f"Concept id={concept_id} has not been evaluated yet. "
                    "Use evaluate_concept first."
                )

            eval_model = concept.evaluation
            retrieved_chunks = rag_service.get_retrieved_context_for_concept(concept)

            response = EvaluationResponse(
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
            return response.model_dump(mode="json")

    @staticmethod
    def _parse_status(value: str | None) -> ConceptStatus | None:
        if value is None:
            return None

        normalized = value.strip().upper()
        if not normalized:
            return None

        try:
            return ConceptStatus(normalized)
        except ValueError as exc:
            valid = ", ".join([status.value for status in ConceptStatus])
            raise ValueError(f"Invalid status '{value}'. Valid values: {valid}") from exc
