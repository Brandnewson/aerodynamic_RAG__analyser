"""Reports router — CRUD endpoints for uploaded PDF reports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import ReportNotFoundError, ValidationError
from app.domain.schemas import (
    ErrorResponse,
    ReportListResponse,
    ReportResponse,
    ReportSummaryResponse,
    ReportVectorIndexListResponse,
    ReportVectorIndexSummaryResponse,
    ReportUpdate,
)
from app.infrastructure.database import get_db
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and create a report from PDF",
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def create_report(
    file: UploadFile = File(..., description="PDF report file"),
    title: str | None = Form(None),
    author: str | None = Form(None),
    tags: str | None = Form(None, description="Comma-separated tags"),
    db: Session = Depends(get_db),
) -> ReportResponse:
    if not file.filename:
        raise ValidationError("Uploaded file must have a filename.", field="file")

    file_bytes = await file.read()
    if not file_bytes:
        raise ValidationError("Uploaded file is empty.", field="file")

    parsed_tags = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]

    report = report_service.create_report_from_upload(
        db,
        filename=file.filename,
        file_bytes=file_bytes,
        title=title,
        author=author,
        tags=parsed_tags,
    )
    return report  # type: ignore[return-value]


@router.get(
    "",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="List reports",
)
def list_reports(
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Records per page."),
    db: Session = Depends(get_db),
) -> ReportListResponse:
    items, total = report_service.list_reports(db, page=page, page_size=page_size)
    summaries = [ReportSummaryResponse.model_validate(item) for item in items]
    return ReportListResponse(items=summaries, total=total, page=page, page_size=page_size)


@router.get(
    "/index",
    response_model=ReportVectorIndexListResponse,
    status_code=status.HTTP_200_OK,
    summary="Read reports from vector-store index",
    responses={
        503: {"model": ErrorResponse, "description": "Vector store unavailable"},
    },
)
def list_indexed_reports(
    query: str | None = Query(
        None,
        min_length=1,
        description="Optional free-text search over indexed report metadata and chunk content.",
    ),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(20, ge=1, le=100, description="Records per page."),
    db: Session = Depends(get_db),
) -> ReportVectorIndexListResponse:
    items, total = report_service.list_indexed_reports(
        db,
        query=query,
        page=page,
        page_size=page_size,
    )
    summaries = [ReportVectorIndexSummaryResponse.model_validate(item) for item in items]
    return ReportVectorIndexListResponse(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        query=query,
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single report",
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> ReportResponse:
    report = report_service.get_report_by_id(db, report_id)
    if report is None:
        raise ReportNotFoundError(report_id)
    return report  # type: ignore[return-value]


@router.put(
    "/{report_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Update report metadata/content",
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
        400: {"model": ErrorResponse, "description": "Validation error"},
    },
)
def update_report(
    report_id: int,
    payload: ReportUpdate,
    db: Session = Depends(get_db),
) -> ReportResponse:
    report = report_service.get_report_by_id(db, report_id)
    if report is None:
        raise ReportNotFoundError(report_id)
    updated = report_service.update_report(db, report, payload)
    return updated  # type: ignore[return-value]


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a report",
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
) -> None:
    report = report_service.get_report_by_id(db, report_id)
    if report is None:
        raise ReportNotFoundError(report_id)
    report_service.delete_report(db, report)
