"""
Admin database module.

Instead of creating a new SQLAlchemy engine (which would use direct psycopg2 and
may fail DNS resolution in some environments), we reuse the existing EMS engine
and session factory from the main database module.
This is safe because both portals share the same PostgreSQL database.
"""

import os
from sqlalchemy.orm import declarative_base, sessionmaker

# ─── Reuse EMS engine ─────────────────────────────────────────────────────────
# The EMS `database.py` already establishes the connection successfully via
# DATABASE_URL or SUPABASE_DB_URL. We import it so we use the same connection pool.
try:
    from database import engine as _ems_engine
    admin_engine = _ems_engine
    AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)
    _using_ems_engine = True
except Exception as _import_err:
    # Fallback: build own engine from env vars if database.py is not importable
    _using_ems_engine = False
    from sqlalchemy import create_engine

    _DATABASE_URL = os.getenv(
        "DATABASE_URL",
        os.getenv("SUPABASE_DB_URL", "")
    )
    if not _DATABASE_URL:
        raise RuntimeError(
            "Admin module could not reuse EMS engine and DATABASE_URL is not set."
        ) from _import_err

    admin_engine = create_engine(
        _DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
    AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields an admin DB session."""
    db = AdminSessionLocal()
    try:
        yield db
    finally:
        db.close()
