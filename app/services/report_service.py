"""Report service for PDF ingestion and report CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError, VectorStoreError
from app.domain.models import Report
from app.domain.schemas import ReportUpdate
from app.infrastructure.vector_store import vector_store

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
_embedding_model = None


def _get_embedding_model():
    global _embedding_model  # noqa: PLW0603
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    vectors = model.encode(chunks, show_progress_bar=False)
    return [vector.tolist() for vector in vectors]


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF byte stream."""
    try:
        reader = PdfReader(BytesIO(file_bytes))
        text_parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text.strip())
        return "\n\n".join(text_parts).strip()
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise ValidationError("Failed to parse PDF file.", field="file") from exc


def _chunk_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    step = max(1, CHUNK_SIZE - CHUNK_OVERLAP)
    chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), step)]
    return [chunk for chunk in chunks if chunk.strip()]


def _normalise_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def _build_vector_ids(report_id: int, chunk_count: int) -> list[str]:
    return [f"report_{report_id}::chunk::{i}" for i in range(chunk_count)]


def _build_metadatas(report: Report, chunk_count: int) -> list[dict]:
    return [
        {
            "report_id": report.id,
            "title": report.title,
            "source_filename": report.source_filename,
            "chunk_index": i,
            "source_type": "report",
        }
        for i in range(chunk_count)
    ]


def get_report_by_id(db: Session, report_id: int) -> Report | None:
    return db.get(Report, report_id)


def list_reports(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Report], int]:
    page_size = min(page_size, 100)
    query = db.query(Report)

    total: int = query.count()
    items: list[Report] = (
        query.order_by(Report.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def create_report_from_upload(
    db: Session,
    *,
    filename: str,
    file_bytes: bytes,
    title: str | None,
    author: str | None,
    tags: list[str] | None,
) -> Report:
    if not filename.lower().endswith(".pdf"):
        raise ValidationError("Only PDF files are supported.", field="file")

    extracted_text = extract_pdf_text(file_bytes)
    if len(extracted_text) < 20:
        raise ValidationError(
            "Extracted report content is too short. Please upload a readable PDF.",
            field="file",
        )

    title_value = (title or "").strip() or Path(filename).stem
    now = datetime.now(timezone.utc)

    report = Report(
        title=title_value,
        source_filename=filename,
        content=extracted_text,
        author=(author or None),
        tags=_normalise_tags(tags),
        chunk_count=0,
        created_at=now,
        updated_at=now,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    chunks = _chunk_text(report.content)
    if not chunks:
        db.delete(report)
        db.commit()
        raise ValidationError("No indexable content found in uploaded report.", field="file")

    ids = _build_vector_ids(report.id, len(chunks))
    metadatas = _build_metadatas(report, len(chunks))
    embeddings = _embed_chunks(chunks)

    try:
        vector_store.add_documents(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
    except Exception as exc:  # pragma: no cover - infrastructure wrapper
        db.delete(report)
        db.commit()
        raise VectorStoreError(
            "Failed to index uploaded report in vector store.",
            operation="add_report_vectors",
        ) from exc

    report.chunk_count = len(chunks)
    report.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report


def update_report(db: Session, report: Report, payload: ReportUpdate) -> Report:
    update_data = payload.model_dump(exclude_none=True)
    should_reindex = False

    if "tags" in update_data:
        update_data["tags"] = _normalise_tags(update_data["tags"])

    if "title" in update_data and update_data["title"] != report.title:
        should_reindex = True

    if "content" in update_data and update_data["content"] != report.content:
        should_reindex = True

    for field, value in update_data.items():
        setattr(report, field, value)

    if should_reindex:
        chunks = _chunk_text(report.content)
        if not chunks:
            raise ValidationError("Report content cannot be empty.", field="content")

        ids = _build_vector_ids(report.id, len(chunks))
        metadatas = _build_metadatas(report, len(chunks))
        embeddings = _embed_chunks(chunks)

        try:
            vector_store.delete_where({"report_id": report.id})
            vector_store.add_documents(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as exc:  # pragma: no cover - infrastructure wrapper
            raise VectorStoreError(
                "Failed to update report vectors in vector store.",
                operation="update_report_vectors",
            ) from exc

        report.chunk_count = len(chunks)

    report.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report: Report) -> None:
    try:
        vector_store.delete_where({"report_id": report.id})
    except Exception as exc:  # pragma: no cover - infrastructure wrapper
        raise VectorStoreError(
            "Failed to delete report vectors from vector store.",
            operation="delete_report_vectors",
        ) from exc

    db.delete(report)
    db.commit()
