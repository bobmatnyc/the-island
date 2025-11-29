"""
SQLAlchemy ORM models for entity biography database.

These models map to the SQLite schema defined in server/database/schema.sql
and provide type-safe database access through SQLAlchemy.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Entity(Base):
    """
    Core entity model representing a person, organization, or location.

    This model stores the basic identity and classification information
    for entities in the system.
    """

    __tablename__ = "entities"

    id = Column(String, primary_key=True)  # Normalized ID (e.g., "jeffrey_epstein")
    display_name = Column(String, nullable=False)  # Full display name
    normalized_name = Column(String)  # Normalized for matching
    entity_type = Column(String)  # person, organization, location
    aliases = Column(Text)  # JSON array of alternative names
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    biography = relationship("EntityBiography", back_populates="entity", uselist=False, cascade="all, delete-orphan")
    document_links = relationship("EntityDocumentLink", back_populates="entity", cascade="all, delete-orphan")
    enrichment_logs = relationship("BiographyEnrichmentLog", back_populates="entity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Entity(id='{self.id}', name='{self.display_name}', type='{self.entity_type}')>"


class EntityBiography(Base):
    """
    Biographical information for entities.

    Stores both structured (birth_date, occupation) and unstructured (summary, key_facts)
    biographical data along with metadata about data quality and sources.
    """

    __tablename__ = "entity_biographies"

    entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True)

    # Core biographical data
    summary = Column(Text)  # Main biographical summary
    birth_date = Column(String)  # Birth date (YYYY-MM-DD or partial)
    death_date = Column(String)  # Death date (YYYY-MM-DD or partial)
    occupation = Column(String)  # Primary occupation/role
    nationality = Column(String)  # Nationality

    # Structured data (stored as JSON text)
    key_facts = Column(Text)  # JSON array of key facts
    timeline = Column(Text)  # JSON array of timeline events
    relationships = Column(Text)  # JSON object of relationship types

    # Metadata
    source = Column(String)  # Source of data (AI/documents/manual)
    model_used = Column(String)  # AI model used for generation
    quality_score = Column(Float)  # Quality score (0.0-1.0)
    word_count = Column(Integer)  # Word count of summary
    has_dates = Column(Boolean, default=False)  # Contains dates
    has_statistics = Column(Boolean, default=False)  # Contains statistics

    # Timestamps
    generated_at = Column(DateTime)  # When biography was generated
    enriched_at = Column(DateTime)  # When enriched from documents
    verified_at = Column(DateTime)  # When manually verified

    # Relationship
    entity = relationship("Entity", back_populates="biography")

    def __repr__(self):
        return f"<EntityBiography(entity_id='{self.entity_id}', words={self.word_count}, quality={self.quality_score})>"


class EntityDocumentLink(Base):
    """
    Links between entities and documents they appear in.

    Tracks which documents mention which entities and how frequently,
    along with context snippets and relevance scores.
    """

    __tablename__ = "entity_document_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String, nullable=False)
    mention_count = Column(Integer, default=0)
    context_snippets = Column(Text)  # JSON array of context snippets
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    entity = relationship("Entity", back_populates="document_links")

    def __repr__(self):
        return f"<EntityDocumentLink(entity='{self.entity_id}', doc='{self.document_id}', mentions={self.mention_count})>"


class BiographyEnrichmentLog(Base):
    """
    Audit trail for biography enrichment operations.

    Tracks all generate, enrich, verify, and update operations
    performed on entity biographies with details and error messages.
    """

    __tablename__ = "biography_enrichment_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    operation = Column(String, nullable=False)  # generate, enrich, verify, update
    source = Column(String)  # AI model or data source
    details = Column(Text)  # JSON with operation details
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    entity = relationship("Entity", back_populates="enrichment_logs")

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<BiographyEnrichmentLog({status} {self.operation} for '{self.entity_id}' at {self.created_at})>"
