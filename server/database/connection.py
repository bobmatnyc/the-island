"""
Database connection management for SQLAlchemy.

Provides session management, connection pooling, and initialization utilities
for the entity biography database.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base

# Database path
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "metadata" / "entities.db"

# Database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with optimizations for SQLite
# - check_same_thread=False: Allow connections from different threads (FastAPI needs this)
# - StaticPool: Reuse connections for better performance
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database by creating all tables.

    This is typically only needed for testing or first-time setup.
    In production, use the migration script instead.
    """
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Provide a database session with automatic cleanup.

    Usage:
        with get_db_session() as session:
            entities = session.query(Entity).all()

    The session will be automatically committed on success or
    rolled back on exception.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """
    Dependency injection for FastAPI endpoints.

    Usage:
        @app.get("/entities/{entity_id}")
        def get_entity(entity_id: str, db: Session = Depends(get_db)):
            return db.query(Entity).filter(Entity.id == entity_id).first()

    FastAPI will automatically handle session creation and cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
