"""
Database package for entity biography management.

This package provides SQLAlchemy ORM models and database utilities
for managing entity biographical data.
"""

from .connection import get_db_session, init_db
from .models import Entity, EntityBiography, EntityDocumentLink, BiographyEnrichmentLog

__all__ = [
    "get_db_session",
    "init_db",
    "Entity",
    "EntityBiography",
    "EntityDocumentLink",
    "BiographyEnrichmentLog",
]
