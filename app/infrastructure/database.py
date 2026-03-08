from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    # SQLite-specific: allow the same connection across threads (FastAPI uses
    # a thread pool; each request gets its own Session via get_db, so this is
    # safe here).
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)

# Enable WAL mode for better concurrent read performance on SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Declarative base — all ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a DB session scoped to a single request
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Schema initialisation — called once at startup
# ---------------------------------------------------------------------------
def init_db() -> None:
    """Create all tables that are not yet present in the database."""
    # Side-effect import: registers all ORM models with Base.metadata
    from app.domain import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
