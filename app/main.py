"""AeroInsight API — application entrypoint.

Run locally:
    uvicorn app.main:app --reload

Interactive docs available at:
    http://127.0.0.1:8000/docs   (Swagger UI)
    http://127.0.0.1:8000/redoc  (ReDoc)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.api import concepts as concepts_router
from app.api import evaluations as evaluations_router
from app.api import reports as reports_router
from app.core.config import settings
from app.core.exceptions import (
    AeroInsightError,
    ConceptNotFoundError,
    ReportNotFoundError,
    EvaluationExistsError,
    EvaluationNotFoundError,
    ValidationError,
    VectorStoreError,
    LLMServiceError,
    DatabaseError,
    RateLimitError,
    ServiceUnavailableError,
)
from app.infrastructure.database import init_db


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise infrastructure on startup; clean up on shutdown."""
    # Create database tables (idempotent — safe to call on every restart)
    init_db()
    yield
    # Nothing to tear down for SQLite / ChromaDB persistent client


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A REST-based AI-augmented aerodynamic concept evaluation platform. "
            "Submit design ideas and receive structured, evidence-based analysis "
            "generated through Retrieval-Augmented Generation (RAG) over curated "
            "aerodynamic literature."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # CORS — permissive for local development; tighten for production
    # ------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    app.include_router(concepts_router.router, prefix="/api/v1")
    app.include_router(evaluations_router.router, prefix="/api/v1")
    app.include_router(reports_router.router, prefix="/api/v1")

    # ------------------------------------------------------------------
    # Health-check endpoint (under /api/v1 for consistency)
    # ------------------------------------------------------------------
    @app.get("/api/v1/health", tags=["system"], summary="Health check")
    async def health() -> dict:
        """Comprehensive health check with system diagnostics."""
        from sqlalchemy import text
        from app.infrastructure.vector_store import vector_store
        from app.infrastructure.database import SessionLocal
        
        diagnostics = {
            "status": "ok",
            "version": settings.APP_VERSION,
            "components": {}
        }
        
        # Check SQLite database
        db = None
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            diagnostics["components"]["database"] = "healthy"
        except Exception as e:
            diagnostics["components"]["database"] = f"error: {str(e)}"
            diagnostics["status"] = "degraded"
        finally:
            if db is not None:
                db.close()
        
        # Check ChromaDB
        try:
            collection = vector_store.get_collection()
            count = collection.count()
            diagnostics["components"]["vector_store"] = f"healthy ({count:,} chunks)"
        except Exception as e:
            diagnostics["components"]["vector_store"] = f"error: {str(e)}"
            diagnostics["status"] = "degraded"
        
        # Check OpenAI API key configured
        if settings.OPENAI_API_KEY:
            diagnostics["components"]["llm"] = f"configured (model: {settings.OPENAI_MODEL})"
        else:
            diagnostics["components"]["llm"] = "not configured (missing API key)"
            diagnostics["status"] = "degraded"
        
        return diagnostics

    @app.get("/health", tags=["system"], include_in_schema=False)
    async def legacy_health() -> dict:
        """Legacy health endpoint maintained for backward compatibility in tests/clients."""
        return await health()

    @app.get("/api/v1/mcp", tags=["system"], summary="MCP integration info")
    async def mcp_info() -> dict:
        """Expose MCP server metadata and startup command for discoverability."""
        return {
            "status": "available",
            "server_name": "AeroInsight RAG MCP Server",
            "transport": "stdio",
            "entrypoint": "python -m app.mcp.server",
            "tools": [
                "list_concepts",
                "create_concept",
                "evaluate_concept",
                "get_evaluation",
            ],
        }

    # ------------------------------------------------------------------
    # Custom exception handlers
    # ------------------------------------------------------------------
    @app.exception_handler(ConceptNotFoundError)
    async def concept_not_found_handler(
        request: Request, exc: ConceptNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": exc.message,
                "code": "CONCEPT_NOT_FOUND",
                **exc.details,
            },
        )

    @app.exception_handler(ReportNotFoundError)
    async def report_not_found_handler(
        request: Request, exc: ReportNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": exc.message,
                "code": "REPORT_NOT_FOUND",
                **exc.details,
            },
        )

    @app.exception_handler(EvaluationExistsError)
    async def evaluation_exists_handler(
        request: Request, exc: EvaluationExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": exc.message,
                "code": "EVALUATION_EXISTS",
                **exc.details,
            },
        )

    @app.exception_handler(EvaluationNotFoundError)
    async def evaluation_not_found_handler(
        request: Request, exc: EvaluationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": exc.message,
                "code": "EVALUATION_NOT_FOUND",
                **exc.details,
            },
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.message,
                "code": "VALIDATION_ERROR",
                **exc.details,
            },
        )

    @app.exception_handler(VectorStoreError)
    async def vector_store_error_handler(
        request: Request, exc: VectorStoreError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": exc.message,
                "code": "VECTOR_STORE_ERROR",
                **exc.details,
            },
        )

    @app.exception_handler(LLMServiceError)
    async def llm_service_error_handler(
        request: Request, exc: LLMServiceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": exc.message,
                "code": "LLM_SERVICE_ERROR",
                **exc.details,
            },
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(
        request: Request, exc: DatabaseError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": exc.message,
                "code": "DATABASE_ERROR",
                **exc.details,
            },
        )

    @app.exception_handler(OperationalError)
    async def sqlalchemy_operational_error_handler(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        """Handle SQLAlchemy OperationalError (connection failures, etc.)."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "code": "DATABASE_OPERATIONAL_ERROR",
            },
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": exc.message,
                "code": "RATE_LIMIT_EXCEEDED",
                **exc.details,
            },
        )

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(
        request: Request, exc: ServiceUnavailableError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": exc.message,
                "code": "SERVICE_UNAVAILABLE",
                **exc.details,
            },
        )

    # ------------------------------------------------------------------
    # Global exception handler — catches unhandled 500s and returns JSON
    # ------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        import traceback
        import logging
        
        logger = logging.getLogger(__name__)
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())

        content: dict = {
            "detail": "An unexpected error occurred.",
            "code": "INTERNAL_ERROR",
        }
        if settings.DEBUG:
            content["error"] = str(exc)
            content["type"] = type(exc).__name__

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
        )

    return app


app = create_app()
