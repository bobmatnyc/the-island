"""
Entity and Document Enums

Design Decision: Centralized Enum Definitions
Rationale: All enum types in one file for consistency, easy modification,
and preventing duplicate definitions across the codebase.

Trade-offs:
- Simplicity: Single source of truth for entity/document types
- Extensibility: Easy to add new types without touching business logic
- Type Safety: Pydantic enforces valid enum values at runtime

Alternatives Considered:
1. String literals: Rejected due to no validation, typo-prone
2. Constants module: Rejected as enums provide better type hints
3. Database-driven types: Rejected for this phase (future enhancement)
"""

from enum import Enum


class EntityType(str, Enum):
    """Entity classification types.

    Types are auto-detected based on name patterns in entity_service.py.
    See detect_entity_type() for detection logic.
    """
    PERSON = "person"
    BUSINESS = "business"
    LOCATION = "location"
    ORGANIZATION = "organization"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Data source types for entity mentions.

    Tracks where entity information originated from.
    Used for filtering and provenance tracking.
    """
    BLACK_BOOK = "black_book"
    FLIGHT_LOGS = "flight_logs"
    COURT_DOCS = "court_docs"
    NEWS = "news"
    ADMINISTRATIVE = "administrative"
    MEDIA = "media"


class DocumentType(str, Enum):
    """Document classification types.

    Maps to document_types field in entity statistics.
    """
    FLIGHT_LOG = "flight_log"
    BLACK_BOOK = "black_book"
    COURT_DOC = "court_doc"
    NEWS_ARTICLE = "news"
    ADMINISTRATIVE = "administrative"
    MEDIA = "media"
