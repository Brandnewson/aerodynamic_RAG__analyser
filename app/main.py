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

from app.api import concepts as concepts_router
from app.api import evaluations as evaluations_router
from app.core.config import settings
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
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            diagnostics["components"]["database"] = "healthy"
        except Exception as e:
            diagnostics["components"]["database"] = f"error: {str(e)}"
            diagnostics["status"] = "degraded"
        
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
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred.",
                "code": "INTERNAL_ERROR",
                "error": str(exc),  # Include actual error in development
                "type": type(exc).__name__
            },
        )

    return app


app = create_app()
