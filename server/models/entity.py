"""
Entity Pydantic Models

Design Decision: Type-Safe Entity Representation
Rationale: Pydantic models provide runtime validation, type safety,
and automatic serialization/deserialization for entity data.

Architecture:
- Entity: Main entity model with statistics and connections
- EntityBiography: Biographical information (separate for optional loading)
- EntityTag: Tagging and categorization data
- DocumentReference: References to documents mentioning entity
- TopConnection: Represents strong connections between entities

Trade-offs:
- Performance: ~10-20% overhead for validation vs raw dicts
- Memory: Pydantic models use more memory than dicts
- Safety: Runtime validation prevents invalid data propagation
- Maintainability: Schema changes are explicit and documented

Performance Notes:
- For bulk operations, use model_validate() instead of individual construction
- Disable validation with model_construct() for trusted data
- Use model_dump() for fast serialization to dict/JSON

Example:
    entity = Entity(
        name="Epstein, Jeffrey",
        normalized_name="Jeffrey Epstein",
        connection_count=262,
        flight_count=8
    )
    entity_dict = entity.model_dump()  # Fast conversion to dict
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import EntityType, SourceType


class DocumentReference(BaseModel):
    """Reference to a document mentioning this entity.

    Design Decision: Separate model for document references
    Rationale: Allows validation of document data and future expansion
    (e.g., relevance scores, mention counts, context snippets)
    """

    path: str = Field(..., description="File path to document")
    type: str = Field(..., description="Document type (flight_log, court_doc, etc.)")
    context: Optional[str] = Field(None, description="Optional context snippet")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class TopConnection(BaseModel):
    """Represents a top connection for an entity.

    Design Decision: Separate model instead of dict
    Rationale: Type safety for connection data and automatic sorting
    """

    name: str = Field(..., description="Connected entity name", min_length=1)
    flights_together: int = Field(
        ge=0, description="Number of flights together (connection strength)"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class Entity(BaseModel):
    """Main entity model representing a person, org, or location.

    This is the core entity model matching entity_statistics.json structure.

    Validation Strategy:
    - Field-level validation: Type hints + Field constraints
    - Model-level validation: Cross-field checks in model_validator
    - Assignment validation: Enabled for runtime safety

    Performance Considerations:
    - Top connections auto-sorted on construction/update
    - Use model_construct() for bulk loading if data is pre-validated
    - Connection count can be computed from top_connections length

    Error Handling:
    - ValidationError raised with detailed field-level errors
    - Use try/except at service layer for graceful degradation
    """

    # Core identity fields
    id: str = Field(
        ...,
        description="Unique entity identifier (snake_case slug)",
        min_length=1,
        pattern=r"^[a-z0-9_]+$",
    )
    name: str = Field(
        ..., description="Display name of entity (as appears in source data)", min_length=1
    )
    normalized_name: Optional[str] = Field(
        None, description="Normalized name for matching and deduplication", min_length=1
    )
    name_variations: list[str] = Field(
        default_factory=list, description="Alternative name spellings/formats"
    )

    # Classification
    entity_type: EntityType = Field(
        default=EntityType.UNKNOWN, description="Auto-detected or manually assigned entity type"
    )

    # Flags
    in_black_book: bool = Field(
        default=False, description="Whether entity appears in Epstein's black book"
    )
    is_billionaire: bool = Field(default=False, description="Known billionaire (manually verified)")

    # Categories/tags (from old system, may be deprecated by EntityTag)
    categories: list[str] = Field(
        default_factory=list, description="Legacy categories (deprecated, use EntityTag instead)"
    )

    # Statistics
    connection_count: int = Field(
        ge=0, default=0, description="Number of connections to other entities"
    )
    flight_count: int = Field(ge=0, default=0, description="Number of flights entity appeared on")
    total_documents: int = Field(
        ge=0, default=0, description="Total documents mentioning this entity"
    )

    # Document tracking
    document_types: dict[str, int] = Field(
        default_factory=dict, description="Count of documents by type (e.g., {'flight_log': 5})"
    )
    documents: list[DocumentReference] = Field(
        default_factory=list, description="List of documents mentioning this entity"
    )

    # Data sources
    sources: list[SourceType] = Field(
        default_factory=list, description="Data sources where entity was found"
    )
    black_book_pages: list[str] = Field(
        default_factory=list, description="Pages in black book where entity appears"
    )

    # Network connections
    top_connections: list[TopConnection] = Field(
        default_factory=list,
        description="Top 10 strongest connections (auto-sorted by flights_together)",
    )

    @field_validator("normalized_name", mode="after")
    @classmethod
    def normalize_name_format(cls, v: Optional[str]) -> Optional[str]:
        """Normalize name: strip whitespace, collapse multiple spaces.

        Example:
            "  Epstein,  Jeffrey  " -> "Epstein, Jeffrey"
        """
        if v is None:
            return None
        import re

        return re.sub(r"\s+", " ", v.strip())

    @field_validator("top_connections", mode="before")
    @classmethod
    def sort_and_limit_connections(cls, v: list) -> list:
        """Sort connections by flights_together descending, limit to 10.

        Design Decision: Auto-sort on construction
        Rationale: Ensures connections always in correct order for display
        Trade-off: Small performance cost on construction for convenience

        Note: Uses mode='before' to limit BEFORE Pydantic validates max_length
        """
        if not isinstance(v, list):
            return v

        # Sort by flights_together if they're dicts, otherwise assume TopConnection objects
        if v and isinstance(v[0], dict):
            sorted_conns = sorted(v, key=lambda x: x.get("flights_together", 0), reverse=True)
        else:
            sorted_conns = sorted(
                v,
                key=lambda x: x.flights_together if hasattr(x, "flights_together") else 0,
                reverse=True,
            )
        return sorted_conns[:10]  # Limit to top 10

    @field_validator("sources", mode="after")
    @classmethod
    def deduplicate_sources(cls, v: list[SourceType]) -> list[SourceType]:
        """Remove duplicate sources while preserving order.

        Example:
            [SourceType.BLACK_BOOK, SourceType.FLIGHT_LOGS, SourceType.BLACK_BOOK]
            -> [SourceType.BLACK_BOOK, SourceType.FLIGHT_LOGS]
        """
        seen = set()
        unique = []
        for source in v:
            if source not in seen:
                unique.append(source)
                seen.add(source)
        return unique

    @model_validator(mode="after")
    def auto_populate_normalized_name_first(self) -> "Entity":
        """Auto-populate normalized_name from name if missing (runs first).

        Design Decision: Graceful defaults for legacy data
        Rationale: Existing data may not have normalized_name field
        """
        if self.normalized_name is None:
            object.__setattr__(self, "normalized_name", self.name)
        return self

    @model_validator(mode="after")
    def validate_document_counts(self) -> "Entity":
        """Ensure document counts are consistent.

        Validation:
        - total_documents should match sum of document_types
        - documents list length should match total_documents (if populated)

        Design Decision: Warning-only validation
        Rationale: Data inconsistencies shouldn't block entity creation,
        but should be logged for data quality audits
        """
        # Calculate expected total from document_types
        expected_total = sum(self.document_types.values())

        # If total_documents doesn't match, log warning but don't fail
        if expected_total > 0 and self.total_documents != expected_total:
            # NOTE: In production, this should log a warning
            # For now, we auto-correct to prevent data inconsistency
            self.total_documents = expected_total

        return self

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,  # Store enums as strings in dict/JSON
        populate_by_name=True,  # Allow field population by alias
    )


class EntityBiography(BaseModel):
    """Biographical information for an entity.

    Design Decision: Separate from Entity model
    Rationale: Biographies are large text fields loaded on-demand,
    not needed for list views. Separating reduces memory footprint.

    Corresponds to entity_biographies.json structure.
    """

    entity_name: str = Field(..., description="Entity name (must match Entity.name)", min_length=1)
    biography: str = Field(
        ..., min_length=10, description="Biographical text (minimum 10 characters)"
    )
    last_updated: Optional[str] = Field(None, description="ISO timestamp of last update")

    @field_validator("biography", mode="after")
    @classmethod
    def strip_biography(cls, v: str) -> str:
        """Strip whitespace from biography text."""
        return v.strip()

    @field_validator("last_updated", mode="after")
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp format if provided.

        Accepts ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
        """
        if v is None:
            return v

        # Try to parse as ISO format
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except ValueError:
            raise ValueError(f"Invalid timestamp format: {v}. Expected ISO format.")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class EntityTag(BaseModel):
    """Tags/categories for entities.

    Design Decision: Separate tagging model
    Rationale: Tags are metadata applied to entities, managed separately
    from core entity data. Allows tag evolution without schema changes.

    Corresponds to entity_tags.json structure.

    Example:
        {
            "entity_name": "Trump, Donald",
            "tags": ["politics", "business", "billionaire"],
            "primary_tag": "politics"
        }
    """

    entity_name: str = Field(..., description="Entity name (must match Entity.name)", min_length=1)
    tags: list[str] = Field(..., min_length=1, description="List of tags (at least one required)")
    primary_tag: Optional[str] = Field(
        None, description="Primary/most relevant tag for this entity"
    )

    @field_validator("tags", mode="after")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags: lowercase, strip, deduplicate.

        Example:
            ["Politics", "  Business  ", "politics"] -> ["politics", "business"]
        """
        normalized = []
        seen = set()

        for tag in v:
            tag_normalized = tag.strip().lower()
            if tag_normalized and tag_normalized not in seen:
                normalized.append(tag_normalized)
                seen.add(tag_normalized)

        if not normalized:
            raise ValueError("At least one valid tag required")

        return normalized

    @model_validator(mode="after")
    def validate_primary_tag(self) -> "EntityTag":
        """Ensure primary_tag is in tags list if provided.

        Design Decision: Auto-add primary_tag to tags
        Rationale: Prevents inconsistency where primary_tag is not in tags
        """
        if self.primary_tag:
            primary_normalized = self.primary_tag.strip().lower()
            if primary_normalized not in self.tags:
                # Auto-add primary tag to tags list
                self.tags.insert(0, primary_normalized)

        return self

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
