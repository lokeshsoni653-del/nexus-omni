"""
OmniMind AI — SQLAlchemy Database Engine & Session Factory

Supports SQLite (dev/test) and PostgreSQL (production) with automatic column migration.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

logger = logging.getLogger("omnimind.db.base")

# ── Declarative Base ──────────────────────────────────────────────────────────
Base = declarative_base()

# ── Engine Factory (created lazily to allow config injection in tests) ─────────
_engine = None
_SessionLocal = None
_tables_created = False


def get_engine(db_url: str = None):
    """Create or return cached SQLAlchemy engine."""
    global _engine
    if _engine is None or db_url is not None:
        from config import settings
        url = db_url or settings.DATABASE_URL
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        engine = create_engine(
            url,
            echo=False,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        if db_url is None:
            _engine = engine
        else:
            return engine
        logger.info(f"Database engine created: {url.split('//')[0]}")
    return _engine


def create_all_tables(db_url: str = None):
    """Create all ORM tables and automatically add missing columns for SQLite."""
    global _tables_created
    from omnimind.db import models  # noqa: F401 — import triggers Base registration
    engine = get_engine(db_url)
    Base.metadata.create_all(bind=engine)

    # Auto-migrate missing columns for SQLite dev environment
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "hashed_password" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"))

        if "documents" in inspector.get_table_names():
            doc_cols = [c["name"] for c in inspector.get_columns("documents")]
            with engine.begin() as conn:
                if "s3_key" not in doc_cols:
                    conn.execute(text("ALTER TABLE documents ADD COLUMN s3_key VARCHAR(500)"))

        if "workflows" in inspector.get_table_names():
            wf_cols = [c["name"] for c in inspector.get_columns("workflows")]
            with engine.begin() as conn:
                if "pdf_report_path" not in wf_cols:
                    conn.execute(text("ALTER TABLE workflows ADD COLUMN pdf_report_path TEXT"))
                if "pdf_report_url" not in wf_cols:
                    conn.execute(text("ALTER TABLE workflows ADD COLUMN pdf_report_url TEXT"))
    except Exception as e:
        logger.warning(f"Auto-migration check skipped: {e}")

    _tables_created = True
    logger.info("All database tables created & migrated successfully.")


def get_session_factory(db_url: str = None):
    """Create or return cached SessionLocal factory."""
    global _SessionLocal, _tables_created
    if not _tables_created:
        create_all_tables(db_url)
    if _SessionLocal is None or db_url is not None:
        engine = get_engine(db_url)
        factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        if db_url is None:
            _SessionLocal = factory
        else:
            return factory
    return _SessionLocal


def drop_all_tables(db_url: str = None):
    """Drop all ORM tables (test teardown)."""
    global _tables_created
    engine = get_engine(db_url)
    Base.metadata.drop_all(bind=engine)
    _tables_created = False


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a database session."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
