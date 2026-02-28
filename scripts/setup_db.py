"""Database initialisation script.

Usage:
    uv run python scripts/setup_db.py

Creates all SQLAlchemy-managed tables in the configured SQLite database.
Safe to re-run — existing tables are never dropped.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.infrastructure.database import init_db


def main() -> None:
    print(f"[setup_db] Using database: {settings.DATABASE_URL}")
    init_db()
    print("[setup_db] All tables created (or already exist). Done.")


if __name__ == "__main__":
    main()
