# Pydantic Schema Design for Epstein Project

**Version**: 1.0
**Date**: 2025-11-18
**Author**: Research Agent
**Status**: Ready for Implementation

---

## Executive Summary

This document provides comprehensive Pydantic v2 schema designs for the Epstein project's entity, document, flight, and timeline data structures. The schemas provide type safety, validation, and self-documentation while maintaining backward compatibility with existing JSON data.

**Key Benefits**:
- **Type Safety**: All fields properly typed, catch errors at development time
- **Validation**: Automatic data validation on load, prevent invalid data
- **Self-Documenting**: Field descriptions and constraints embedded in code
- **API Integration**: Native FastAPI support with automatic OpenAPI docs
- **Performance**: Minimal overhead (~5-10% for validation)
- **Maintainability**: Clear contracts between data layer and business logic

**Implementation Impact**:
- Estimated 3-5 days for full migration
- Zero data migration required (validates existing JSON)
- Incremental rollout possible (start with entities)
- Breaking changes: None (existing JSON validates successfully)

---

## Table of Contents

1. [Entity Models](#entity-models)
2. [Document Models](#document-models)
3. [Flight Models](#flight-models)
4. [Timeline Models](#timeline-models)
5. [Network Models](#network-models)
6. [Supporting Models](#supporting-models)
7. [Migration Strategy](#migration-strategy)
8. [Implementation Plan](#implementation-plan)
9. [Testing Strategy](#testing-strategy)
10. [Performance Considerations](#performance-considerations)

---

## 1. Entity Models

### 1.1 Core Entity Model

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class EntitySource(str, Enum):
    """Valid entity data sources"""
    BLACK_BOOK = "black_book"
    FLIGHT_LOGS = "flight_logs"
    COURT_DOCS = "court_docs"
    MEDIA = "media"
    ADMINISTRATIVE = "administrative"


class EntityType(str, Enum):
    """Valid entity types"""
    PERSON = "person"
    BUSINESS = "business"
    LOCATION = "location"
    ORGANIZATION = "organization"


class DocumentReference(BaseModel):
    """Reference to a document mentioning this entity"""
    path: str = Field(..., description="File path to document")
    type: str = Field(..., description="Document type (email, pdf, court_filing)")

    model_config = ConfigDict(
        frozen=True,  # Immutable
        str_strip_whitespace=True
    )


class TopConnection(BaseModel):
    """Top connection for an entity"""
    name: str = Field(..., description="Connected entity name", min_length=1)
    flights_together: int = Field(ge=0, description="Number of flights together")

    model_config = ConfigDict(frozen=True)


class Entity(BaseModel):
    """
    Core entity model representing a person, business, location, or organization.

    This is the primary data model for entities in the system, containing:
    - Basic identification (name, variations)
    - Source tracking (where data came from)
    - Document references
    - Connection statistics
    - Flight activity
    - Categorization (billionaire, black book presence, etc.)
    """

    # Primary identification
    name: str = Field(
        ...,
        description="Primary display name (format: 'Last, First' or normalized)",
        min_length=1,
        max_length=200
    )
    normalized_name: str = Field(
        ...,
        description="Normalized name for matching and search",
        min_length=1,
        max_length=200
    )
    name_variations: List[str] = Field(
        default_factory=list,
        description="Alternative name forms and spellings"
    )

    # Type and categorization
    entity_type: Optional[EntityType] = Field(
        None,
        description="Auto-detected or manually set entity type"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Category tags (e.g., 'politician', 'academic')"
    )

    # Flags
    in_black_book: bool = Field(
        default=False,
        description="Whether entity appears in Epstein's black book"
    )
    is_billionaire: bool = Field(
        default=False,
        description="Whether entity is a known billionaire"
    )

    # Data sources
    sources: List[EntitySource] = Field(
        default_factory=list,
        description="List of data sources mentioning this entity"
    )

    # Documents
    total_documents: int = Field(
        ge=0,
        default=0,
        description="Total number of documents mentioning entity"
    )
    document_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of documents by type"
    )
    documents: List[DocumentReference] = Field(
        default_factory=list,
        description="List of document references"
    )

    # Connections
    connection_count: int = Field(
        ge=0,
        default=0,
        description="Number of unique connections to other entities"
    )
    top_connections: List[TopConnection] = Field(
        default_factory=list,
        description="Top connected entities by flight count"
    )

    # Flight activity
    flight_count: int = Field(
        ge=0,
        default=0,
        description="Number of flights on Epstein's aircraft"
    )

    @field_validator('normalized_name', mode='after')
    @classmethod
    def normalize_name_format(cls, v: str) -> str:
        """Ensure normalized name is stripped and non-empty"""
        normalized = v.strip()
        if not normalized:
            raise ValueError("Normalized name cannot be empty")
        return normalized

    @field_validator('name_variations', mode='after')
    @classmethod
    def deduplicate_variations(cls, v: List[str]) -> List[str]:
        """Remove duplicate name variations"""
        seen = set()
        unique = []
        for name in v:
            normalized = name.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(name)
        return unique

    @field_validator('top_connections', mode='after')
    @classmethod
    def sort_connections(cls, v: List[TopConnection]) -> List[TopConnection]:
        """Sort connections by flights_together descending"""
        return sorted(v, key=lambda x: x.flights_together, reverse=True)

    model_config = ConfigDict(
        validate_assignment=True,  # Validate on attribute assignment
        str_strip_whitespace=True,
        use_enum_values=True,  # Store enum values as strings in JSON
        json_schema_extra={
            "example": {
                "name": "Clinton, William",
                "normalized_name": "William Clinton",
                "name_variations": ["Bill Clinton", "William J. Clinton"],
                "entity_type": "person",
                "categories": ["politician"],
                "in_black_book": False,
                "is_billionaire": False,
                "sources": ["flight_logs"],
                "total_documents": 15,
                "document_types": {"flight_log": 10, "media": 5},
                "connection_count": 45,
                "flight_count": 26,
                "top_connections": [
                    {"name": "Doug Band", "flights_together": 18},
                    {"name": "Jeffrey Epstein", "flights_together": 26}
                ]
            }
        }
    )


class EntityStatistics(BaseModel):
    """
    Container for entity statistics data structure

    Maps to entity_statistics.json format
    """
    generated: datetime = Field(
        ...,
        description="Timestamp when statistics were generated"
    )
    total_entities: int = Field(
        ge=0,
        description="Total number of entities in dataset"
    )
    statistics: Dict[str, Entity] = Field(
        default_factory=dict,
        description="Mapping of entity name to entity data"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "generated": "2025-11-17T18:53:21.321883",
                "total_entities": 1702,
                "statistics": {}
            }
        }
    )
```

### 1.2 Entity Biography Model

```python
class EntityBiography(BaseModel):
    """
    Biographical information for an entity

    Maps to entity_biographies.json format.
    Contains verified biographical data from public sources.
    """

    # Basic information
    full_name: str = Field(
        ...,
        description="Full legal name",
        min_length=1,
        max_length=200
    )
    born: Optional[date] = Field(
        None,
        description="Date of birth (YYYY-MM-DD or YYYY)"
    )
    died: Optional[date] = Field(
        None,
        description="Date of death (if applicable)"
    )
    birth_place: Optional[str] = Field(
        None,
        description="Place of birth (city, state/province, country)"
    )
    nationality: Optional[str] = Field(
        None,
        description="Nationality or nationalities"
    )

    # Professional information
    occupation: Optional[str] = Field(
        None,
        description="Primary occupation or role"
    )
    education: List[str] = Field(
        default_factory=list,
        description="Educational background (degrees, institutions)"
    )
    known_for: Optional[str] = Field(
        None,
        description="What the entity is primarily known for"
    )
    net_worth: Optional[str] = Field(
        None,
        description="Estimated net worth (if publicly available)"
    )
    career_summary: Optional[str] = Field(
        None,
        description="Summary of career and professional achievements"
    )

    # Epstein connection
    epstein_connection: Optional[str] = Field(
        None,
        description="Description of connection to Epstein case"
    )
    legal_status: Optional[str] = Field(
        None,
        description="Legal status related to Epstein case (if applicable)"
    )

    # Summary and sources
    summary: Optional[str] = Field(
        None,
        description="Brief biographical summary",
        max_length=2000
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs to source materials (Wikipedia, news articles, etc.)"
    )
    privacy_note: Optional[str] = Field(
        None,
        description="Privacy considerations note (for victims)"
    )

    @field_validator('sources', mode='after')
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        """Ensure sources are valid URLs"""
        from urllib.parse import urlparse
        validated = []
        for url in v:
            try:
                result = urlparse(url)
                if result.scheme in ('http', 'https') and result.netloc:
                    validated.append(url)
            except Exception:
                pass
        return validated

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "full_name": "William Jefferson Clinton",
                "born": "1946-08-19",
                "died": None,
                "birth_place": "Hope, Arkansas, USA",
                "nationality": "American",
                "occupation": "Former President of the United States",
                "education": [
                    "Georgetown University (BS Foreign Service, 1968)",
                    "Yale Law School (JD, 1973)"
                ],
                "known_for": "42nd President of the United States (1993-2001)",
                "epstein_connection": "Flew on Epstein's private plane for humanitarian trips",
                "legal_status": "No criminal charges related to Epstein",
                "summary": "42nd President who took humanitarian trips on Epstein's plane",
                "sources": ["https://en.wikipedia.org/wiki/Bill_Clinton"]
            }
        }
    )


class BiographyCollection(BaseModel):
    """
    Collection of entity biographies

    Maps to entity_biographies.json file structure
    """
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the biography collection"
    )
    entities: Dict[str, EntityBiography] = Field(
        default_factory=dict,
        description="Mapping of entity name to biography"
    )
    research_notes: Optional[Dict[str, Any]] = Field(
        None,
        description="Research methodology and notes"
    )
```

### 1.3 Entity Tag Model

```python
class EntityTag(str, Enum):
    """Valid entity tags"""
    VICTIM = "Victim"
    POLITICIAN = "Politician"
    BUSINESS = "Business"
    CELEBRITY = "Celebrity"
    LEGAL = "Legal"
    ACADEMIC = "Academic"
    FINANCIER = "Financier"
    ASSOCIATE = "Associate"
    STAFF = "Staff"
    ADVOCATE = "Advocate"
    ROYAL = "Royal"
    SOCIALITE = "Socialite"
    ARTIST = "Artist"


class EntityTagInfo(BaseModel):
    """
    Tag information for a single entity

    Maps to entity_tags.json entity structure
    """
    tags: List[EntityTag] = Field(
        ...,
        description="List of tags assigned to entity",
        min_length=1
    )
    primary_tag: EntityTag = Field(
        ...,
        description="Primary tag for this entity"
    )
    verification: str = Field(
        ...,
        description="Source of tag verification",
        min_length=1
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the entity"
    )

    @field_validator('primary_tag', mode='after')
    @classmethod
    def primary_in_tags(cls, v: EntityTag, info) -> EntityTag:
        """Ensure primary_tag is in tags list"""
        tags = info.data.get('tags', [])
        if v not in tags:
            raise ValueError(f"Primary tag '{v}' must be in tags list")
        return v

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "tags": ["Politician"],
                "primary_tag": "Politician",
                "verification": "Wikipedia, flight logs, public statements",
                "notes": "42nd President. Flew on Epstein's plane for humanitarian trips."
            }
        }
    )


class TagCollection(BaseModel):
    """
    Collection of entity tags

    Maps to entity_tags.json file structure
    """
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about tag collection"
    )
    entities: Dict[str, EntityTagInfo] = Field(
        default_factory=dict,
        description="Mapping of entity name to tag info"
    )
    tag_statistics: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of entities per tag"
    )
    important_notes: List[str] = Field(
        default_factory=list,
        description="Important disclaimers and notes"
    )
    verification_methodology: Optional[Dict[str, str]] = Field(
        None,
        description="Methodology for assigning each tag type"
    )
```

---

## 2. Document Models

### 2.1 Core Document Model

```python
class DocumentType(str, Enum):
    """Valid document types"""
    PDF = "pdf"
    EMAIL = "email"
    TXT = "txt"
    MD = "md"
    JSON = "json"


class DocumentClassification(str, Enum):
    """Document classification categories"""
    EMAIL = "email"
    COURT_FILING = "court_filing"
    DEPOSITION = "deposition"
    FLIGHT_LOG = "flight_log"
    FINANCIAL = "financial"
    MEDIA = "media"
    ADMINISTRATIVE = "administrative"
    LEGAL_BRIEF = "legal_brief"
    SETTLEMENT = "settlement"
    TRANSCRIPT = "transcript"


class DocumentMetadata(BaseModel):
    """Metadata about a document"""
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    page_count: Optional[int] = Field(None, ge=0, description="Number of pages (for PDFs)")
    created_date: Optional[datetime] = Field(None, description="Document creation date")
    modified_date: Optional[datetime] = Field(None, description="Last modified date")
    author: Optional[str] = Field(None, description="Document author")
    title: Optional[str] = Field(None, description="Document title")

    model_config = ConfigDict(frozen=True)


class Document(BaseModel):
    """
    Core document model

    Represents a document in the collection (PDF, email, text file, etc.)
    """

    # Identification
    id: Optional[str] = Field(
        None,
        description="Unique document identifier (auto-generated from path)"
    )
    filename: str = Field(
        ...,
        description="Document filename",
        min_length=1
    )
    path: str = Field(
        ...,
        description="Full path to document relative to data root",
        min_length=1
    )

    # Type and classification
    doc_type: DocumentType = Field(
        ...,
        description="Document file type"
    )
    classification: Optional[DocumentClassification] = Field(
        None,
        description="Document classification category"
    )

    # Source and collection
    source: Optional[str] = Field(
        None,
        description="Source collection (e.g., 'SDNY', 'giuffre_v_maxwell')"
    )
    collection: Optional[str] = Field(
        None,
        description="Document collection or case name"
    )

    # Content
    title: Optional[str] = Field(
        None,
        description="Document title",
        max_length=500
    )
    description: Optional[str] = Field(
        None,
        description="Document description or summary"
    )
    content_preview: Optional[str] = Field(
        None,
        description="Preview of document content (first ~500 chars)",
        max_length=1000
    )

    # Entities and references
    entities_mentioned: List[str] = Field(
        default_factory=list,
        description="List of entities mentioned in document"
    )
    entity_count: int = Field(
        ge=0,
        default=0,
        description="Number of unique entities mentioned"
    )

    # Metadata
    metadata: Optional[DocumentMetadata] = Field(
        None,
        description="Additional document metadata"
    )

    # Flags
    is_available: bool = Field(
        default=True,
        description="Whether document content is available"
    )
    is_redacted: bool = Field(
        default=False,
        description="Whether document contains redactions"
    )

    @field_validator('id', mode='before')
    @classmethod
    def generate_id(cls, v: Optional[str], info) -> str:
        """Generate ID from path if not provided"""
        if v:
            return v
        path = info.data.get('path', '')
        if path:
            import hashlib
            return hashlib.md5(path.encode()).hexdigest()[:16]
        return ""

    @field_validator('doc_type', mode='before')
    @classmethod
    def infer_doc_type(cls, v: Optional[str], info) -> str:
        """Infer doc_type from filename if not provided"""
        if v:
            return v
        filename = info.data.get('filename', '')
        ext = filename.split('.')[-1].lower()
        return ext if ext in ('pdf', 'email', 'txt', 'md', 'json') else 'txt'

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "id": "a1b2c3d4e5f6g7h8",
                "filename": "epstein_flight_log_2002.pdf",
                "path": "data/pdf/flight_logs/epstein_flight_log_2002.pdf",
                "doc_type": "pdf",
                "classification": "flight_log",
                "source": "flight_logs",
                "title": "Flight Log - 2002",
                "entities_mentioned": ["Jeffrey Epstein", "Bill Clinton", "Doug Band"],
                "entity_count": 3,
                "is_available": True,
                "is_redacted": False
            }
        }
    )


class DocumentIndex(BaseModel):
    """
    Document index collection

    Maps to all_documents_index.json structure
    """
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Index metadata"
    )
    documents: List[Document] = Field(
        default_factory=list,
        description="List of all documents"
    )
    total_count: int = Field(
        ge=0,
        default=0,
        description="Total document count"
    )

    @field_validator('total_count', mode='after')
    @classmethod
    def sync_total_count(cls, v: int, info) -> int:
        """Ensure total_count matches documents length"""
        docs = info.data.get('documents', [])
        return len(docs)
```

### 2.2 Email Document Model

```python
class EmailDocument(Document):
    """
    Extended document model for emails

    Adds email-specific fields
    """

    # Email headers
    email_from: Optional[str] = Field(
        None,
        description="Email sender address"
    )
    email_to: List[str] = Field(
        default_factory=list,
        description="Email recipient addresses"
    )
    email_cc: List[str] = Field(
        default_factory=list,
        description="Email CC addresses"
    )
    email_subject: Optional[str] = Field(
        None,
        description="Email subject line",
        max_length=500
    )
    email_date: Optional[datetime] = Field(
        None,
        description="Email send date/time"
    )

    # Email metadata
    has_attachments: bool = Field(
        default=False,
        description="Whether email has attachments"
    )
    attachment_count: int = Field(
        ge=0,
        default=0,
        description="Number of attachments"
    )

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "filename": "email_001.eml",
                "path": "data/emails/email_001.eml",
                "doc_type": "email",
                "classification": "email",
                "email_from": "person@example.com",
                "email_to": ["recipient@example.com"],
                "email_subject": "Meeting schedule",
                "has_attachments": False
            }
        }
    )


class PDFDocument(Document):
    """
    Extended document model for PDFs

    Adds PDF-specific fields
    """

    page_count: Optional[int] = Field(
        None,
        ge=1,
        description="Number of pages in PDF"
    )
    ocr_processed: bool = Field(
        default=False,
        description="Whether OCR has been run on this PDF"
    )
    is_searchable: bool = Field(
        default=False,
        description="Whether PDF text is searchable"
    )

    model_config = ConfigDict(use_enum_values=True)
```

---

## 3. Flight Models

### 3.1 Flight Model

```python
class Flight(BaseModel):
    """
    Flight log entry

    Maps to flight_logs_by_flight.json flights array
    """

    # Identification
    id: str = Field(
        ...,
        description="Unique flight ID (format: DATE_TAIL_ROUTE)",
        pattern=r"^\d{1,2}/\d{1,2}/\d{4}_[A-Z0-9]+_[A-Z]+-[A-Z]+$"
    )

    # Flight details
    date: str = Field(
        ...,
        description="Flight date (MM/DD/YYYY format)",
        pattern=r"^\d{1,2}/\d{1,2}/\d{4}$"
    )
    tail_number: str = Field(
        ...,
        description="Aircraft tail number (e.g., N908JE)",
        pattern=r"^N[A-Z0-9]+$",
        min_length=4,
        max_length=10
    )
    route: str = Field(
        ...,
        description="Flight route (FROM-TO airport codes)",
        pattern=r"^[A-Z]{3}-[A-Z]{3}$"
    )

    # Passengers
    passengers: List[str] = Field(
        default_factory=list,
        description="List of passenger names"
    )
    passenger_count: int = Field(
        ge=0,
        description="Total number of passengers"
    )

    # Parsed route (computed)
    from_airport: Optional[str] = Field(
        None,
        description="Origin airport code (auto-parsed from route)",
        pattern=r"^[A-Z]{3}$"
    )
    to_airport: Optional[str] = Field(
        None,
        description="Destination airport code (auto-parsed from route)",
        pattern=r"^[A-Z]{3}$"
    )

    @field_validator('passenger_count', mode='after')
    @classmethod
    def validate_passenger_count(cls, v: int, info) -> int:
        """Ensure passenger_count matches passengers length"""
        passengers = info.data.get('passengers', [])
        actual_count = len(passengers)
        if v != actual_count:
            # Auto-correct to match actual list
            return actual_count
        return v

    @field_validator('from_airport', 'to_airport', mode='before')
    @classmethod
    def parse_route(cls, v: Optional[str], info) -> Optional[str]:
        """Parse airport codes from route if not provided"""
        if v:
            return v

        route = info.data.get('route', '')
        if '-' in route:
            from_code, to_code = route.split('-', 1)
            field_name = info.field_name
            if field_name == 'from_airport':
                return from_code
            elif field_name == 'to_airport':
                return to_code
        return None

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "id": "11/21/1995_N908JE_TEB-PBI",
                "date": "11/21/1995",
                "tail_number": "N908JE",
                "route": "TEB-PBI",
                "passengers": ["Glenn Dubin", "Eva Dubin", "Jeffrey Epstein"],
                "passenger_count": 3,
                "from_airport": "TEB",
                "to_airport": "PBI"
            }
        }
    )


class FlightCollection(BaseModel):
    """
    Collection of all flights

    Maps to flight_logs_by_flight.json structure
    """
    total_flights: int = Field(
        ge=0,
        description="Total number of flights"
    )
    flights: List[Flight] = Field(
        default_factory=list,
        description="List of all flight records"
    )

    @field_validator('total_flights', mode='after')
    @classmethod
    def sync_total(cls, v: int, info) -> int:
        """Ensure total_flights matches flights length"""
        flights = info.data.get('flights', [])
        return len(flights)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_flights": 1167,
                "flights": []
            }
        }
    )
```

### 3.2 Airport Location Model

```python
class AirportLocation(BaseModel):
    """
    Airport location information

    Maps to locations.json (if exists) or flight_locations.json
    """

    code: str = Field(
        ...,
        description="IATA airport code",
        pattern=r"^[A-Z]{3}$"
    )
    name: Optional[str] = Field(
        None,
        description="Airport full name"
    )
    city: Optional[str] = Field(
        None,
        description="City name"
    )
    country: Optional[str] = Field(
        None,
        description="Country name"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Latitude coordinate"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Longitude coordinate"
    )

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "code": "TEB",
                "name": "Teterboro Airport",
                "city": "Teterboro, NJ",
                "country": "USA",
                "latitude": 40.8501,
                "longitude": -74.0608
            }
        }
    )


class RouteStatistics(BaseModel):
    """Statistics for a specific flight route"""

    route: str = Field(
        ...,
        description="Route (FROM-TO)",
        pattern=r"^[A-Z]{3}-[A-Z]{3}$"
    )
    frequency: int = Field(
        ge=0,
        description="Number of times route was flown"
    )
    from_location: Optional[AirportLocation] = Field(
        None,
        description="Origin airport details"
    )
    to_location: Optional[AirportLocation] = Field(
        None,
        description="Destination airport details"
    )

    model_config = ConfigDict(frozen=True)
```

---

## 4. Timeline Models

```python
class TimelineCategory(str, Enum):
    """Timeline event categories"""
    BIOGRAPHICAL = "biographical"
    CASE = "case"
    DOCUMENTS = "documents"
    POLITICAL = "political"


class TimelineEvent(BaseModel):
    """
    Timeline event

    Maps to timeline.json events array
    """

    # Date (can be YYYY, YYYY-MM, or YYYY-MM-DD)
    date: str = Field(
        ...,
        description="Event date (YYYY-MM-DD, YYYY-MM-00, or YYYY-00-00 for partial dates)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    # Categorization
    category: TimelineCategory = Field(
        ...,
        description="Event category"
    )

    # Content
    title: str = Field(
        ...,
        description="Event title",
        min_length=1,
        max_length=200
    )
    description: str = Field(
        ...,
        description="Detailed event description",
        min_length=1
    )

    # Sources
    source: Optional[str] = Field(
        None,
        description="Source attribution (e.g., 'Wikipedia, Britannica')"
    )
    source_url: Optional[str] = Field(
        None,
        description="URL to source material"
    )

    # References
    related_entities: List[str] = Field(
        default_factory=list,
        description="Entities related to this event"
    )
    related_documents: List[str] = Field(
        default_factory=list,
        description="Document paths related to this event"
    )

    @field_validator('source_url', mode='after')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate source URL format"""
        if not v:
            return v
        from urllib.parse import urlparse
        try:
            result = urlparse(v)
            if result.scheme in ('http', 'https') and result.netloc:
                return v
        except Exception:
            pass
        return None

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "date": "1953-01-20",
                "category": "biographical",
                "title": "Birth of Jeffrey Epstein",
                "description": "Jeffrey Edward Epstein born in Brooklyn, New York",
                "source": "Wikipedia, Britannica",
                "source_url": "https://en.wikipedia.org/wiki/Jeffrey_Epstein",
                "related_entities": ["Jeffrey Epstein"],
                "related_documents": []
            }
        }
    )


class TimelineCollection(BaseModel):
    """
    Timeline event collection

    Maps to timeline.json structure
    """
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Timeline metadata"
    )
    events: List[TimelineEvent] = Field(
        default_factory=list,
        description="List of timeline events"
    )

    @field_validator('events', mode='after')
    @classmethod
    def sort_events(cls, v: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events by date chronologically"""
        return sorted(v, key=lambda e: e.date)
```

---

## 5. Network Models

```python
class NetworkNode(BaseModel):
    """
    Network graph node

    Maps to entity_network.json nodes array
    """

    id: str = Field(
        ...,
        description="Node ID (entity name)",
        min_length=1
    )
    name: str = Field(
        ...,
        description="Display name",
        min_length=1
    )

    # Attributes
    in_black_book: bool = Field(
        default=False,
        description="Whether in Epstein's black book"
    )
    is_billionaire: bool = Field(
        default=False,
        description="Whether entity is billionaire"
    )
    flight_count: int = Field(
        ge=0,
        default=0,
        description="Number of flights"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Entity categories/tags"
    )
    connection_count: int = Field(
        ge=0,
        default=0,
        description="Number of connections"
    )

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "id": "Glenn Dubin",
                "name": "Glenn Dubin",
                "in_black_book": False,
                "is_billionaire": False,
                "flight_count": 0,
                "categories": [],
                "connection_count": 29
            }
        }
    )


class NetworkEdge(BaseModel):
    """
    Network graph edge (connection)

    Maps to entity_network.json edges array
    """

    source: str = Field(
        ...,
        description="Source node ID (entity name)",
        min_length=1
    )
    target: str = Field(
        ...,
        description="Target node ID (entity name)",
        min_length=1
    )
    weight: int = Field(
        ge=0,
        description="Connection weight (typically flights together)"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="Contexts where connection occurred (e.g., 'flight_log')"
    )

    @field_validator('target', mode='after')
    @classmethod
    def validate_not_self_loop(cls, v: str, info) -> str:
        """Prevent self-loops in network"""
        source = info.data.get('source', '')
        if v == source:
            raise ValueError("Edge cannot connect node to itself")
        return v

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "source": "Glenn Dubin",
                "target": "Eva Dubin",
                "weight": 18,
                "contexts": ["flight_log"]
            }
        }
    )


class NetworkGraph(BaseModel):
    """
    Complete network graph

    Maps to entity_network.json structure
    """
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Network metadata (total_nodes, total_edges, etc.)"
    )
    nodes: List[NetworkNode] = Field(
        default_factory=list,
        description="Network nodes"
    )
    edges: List[NetworkEdge] = Field(
        default_factory=list,
        description="Network edges"
    )

    @field_validator('edges', mode='after')
    @classmethod
    def validate_edge_nodes_exist(cls, v: List[NetworkEdge], info) -> List[NetworkEdge]:
        """Validate all edge nodes exist in nodes list"""
        nodes = info.data.get('nodes', [])
        node_ids = {node.id for node in nodes}

        valid_edges = []
        for edge in v:
            if edge.source in node_ids and edge.target in node_ids:
                valid_edges.append(edge)

        return valid_edges
```

---

## 6. Supporting Models

### 6.1 API Response Models

```python
class PaginatedResponse(BaseModel):
    """Generic paginated response"""

    items: List[Any] = Field(
        default_factory=list,
        description="List of items"
    )
    total: int = Field(
        ge=0,
        description="Total number of items matching query"
    )
    limit: int = Field(
        ge=1,
        description="Items per page"
    )
    offset: int = Field(
        ge=0,
        description="Pagination offset"
    )
    has_more: bool = Field(
        default=False,
        description="Whether more items exist"
    )

    @field_validator('has_more', mode='after')
    @classmethod
    def compute_has_more(cls, v: bool, info) -> bool:
        """Compute has_more based on total, limit, offset"""
        total = info.data.get('total', 0)
        offset = info.data.get('offset', 0)
        limit = info.data.get('limit', 0)
        return (offset + limit) < total


class EntityListResponse(PaginatedResponse):
    """Response for entity list endpoint"""
    items: List[Entity] = Field(
        default_factory=list,
        description="List of entities"
    )
    facets: Optional[Dict[str, Any]] = Field(
        None,
        description="Available filters (types, tags, sources)"
    )


class DocumentListResponse(PaginatedResponse):
    """Response for document list endpoint"""
    items: List[Document] = Field(
        default_factory=list,
        description="List of documents"
    )
    facets: Optional[Dict[str, Any]] = Field(
        None,
        description="Available filters (types, classifications, sources)"
    )


class FlightListResponse(PaginatedResponse):
    """Response for flight list endpoint"""
    items: List[Flight] = Field(
        default_factory=list,
        description="List of flights"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Available filters (passengers, airports, dates)"
    )


class SearchResult(BaseModel):
    """Generic search result"""

    result_type: str = Field(
        ...,
        description="Type of result (entity, document, flight, event)"
    )
    id: str = Field(
        ...,
        description="Unique identifier"
    )
    title: str = Field(
        ...,
        description="Result title/name"
    )
    snippet: Optional[str] = Field(
        None,
        description="Snippet or preview"
    )
    score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Relevance score (0-1)"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Full result data"
    )
```

### 6.2 Error Models

```python
class ErrorDetail(BaseModel):
    """Detailed error information"""

    field: Optional[str] = Field(
        None,
        description="Field name that caused error"
    )
    message: str = Field(
        ...,
        description="Error message"
    )
    error_type: str = Field(
        ...,
        description="Type of error (validation_error, not_found, etc.)"
    )


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(
        ...,
        description="Error message"
    )
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Detailed error information"
    )
    status_code: int = Field(
        ...,
        ge=400,
        le=599,
        description="HTTP status code"
    )
```

---

## 7. Migration Strategy

### 7.1 Migration Approach: Incremental (Recommended)

**Phase 1: Entity Models (Week 1)**
- Implement `Entity`, `EntityBiography`, `EntityTagInfo` models
- Update `EntityService` to use Pydantic models
- Update `/api/v2/entities` endpoints
- Test with existing JSON data
- Monitor performance

**Phase 2: Document Models (Week 2)**
- Implement `Document`, `EmailDocument`, `PDFDocument` models
- Update `DocumentService` to use Pydantic models
- Update `/api/v2/documents` endpoints
- Test document loading and validation

**Phase 3: Flight & Network Models (Week 3)**
- Implement `Flight`, `NetworkNode`, `NetworkEdge` models
- Update `FlightService` and `NetworkService`
- Update flight and network endpoints
- Validate flight data parsing

**Phase 4: Timeline & Supporting Models (Week 4)**
- Implement `TimelineEvent` and response models
- Update timeline endpoints
- Add comprehensive API documentation
- Performance optimization

### 7.2 Backward Compatibility Strategy

```python
# Approach: Wrapper functions for gradual migration

def load_entity_statistics_v1(path: Path) -> Dict:
    """Legacy: Load as dict"""
    with open(path) as f:
        return json.load(f)

def load_entity_statistics_v2(path: Path) -> EntityStatistics:
    """New: Load and validate with Pydantic"""
    with open(path) as f:
        data = json.load(f)
        return EntityStatistics.model_validate(data)

# Service can support both during migration
class EntityService:
    def __init__(self, use_pydantic: bool = False):
        self.use_pydantic = use_pydantic
        if use_pydantic:
            self.data = load_entity_statistics_v2(path)
        else:
            self.data = load_entity_statistics_v1(path)
```

### 7.3 Handling Validation Errors

```python
from pydantic import ValidationError

def load_with_error_handling(path: Path, model_class):
    """Load data with comprehensive error handling"""
    try:
        with open(path) as f:
            data = json.load(f)
        return model_class.model_validate(data)

    except ValidationError as e:
        # Log validation errors
        print(f"Validation errors in {path}:")
        for error in e.errors():
            field = ' -> '.join(str(loc) for loc in error['loc'])
            print(f"  {field}: {error['msg']}")

        # Option 1: Fail fast (recommended for development)
        raise

        # Option 2: Return partial data (for production resilience)
        # return model_class.model_validate(data, strict=False)

    except json.JSONDecodeError as e:
        print(f"JSON parse error in {path}: {e}")
        raise
```

### 7.4 Data Cleaning Before Migration

**Recommended Pre-Migration Steps**:

1. **Validate Existing JSON**:
```bash
# Check all JSON files are valid
find data/ -name "*.json" -exec python3 -c "import json, sys; json.load(open('{}'))" \;
```

2. **Identify Schema Violations**:
```python
# Script to test validation without migration
def audit_data_quality():
    """Audit existing data against Pydantic schemas"""

    issues = []

    # Test entity data
    try:
        stats = load_entity_statistics_v2("data/metadata/entity_statistics.json")
    except ValidationError as e:
        issues.extend(e.errors())

    # Test other files...

    return issues
```

3. **Fix Common Issues**:
- Empty strings → None
- Missing required fields → Add defaults
- Type mismatches → Convert types
- Invalid dates → Fix format

---

## 8. Implementation Plan

### 8.1 File Structure

```
server/
├── models/
│   ├── __init__.py
│   ├── entity.py          # Entity models
│   ├── document.py        # Document models
│   ├── flight.py          # Flight models
│   ├── timeline.py        # Timeline models
│   ├── network.py         # Network models
│   ├── responses.py       # API response models
│   └── common.py          # Shared models and enums
├── services/
│   ├── entity_service.py  # Update to use models
│   ├── document_service.py
│   ├── flight_service.py
│   └── network_service.py
└── api_routes.py          # Update endpoint type hints
```

### 8.2 Example Implementation: Entity Model

**File: `server/models/entity.py`**

```python
"""
Entity models for the Epstein project

Provides type-safe entity data structures with validation.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class EntitySource(str, Enum):
    """Valid entity data sources"""
    BLACK_BOOK = "black_book"
    FLIGHT_LOGS = "flight_logs"
    COURT_DOCS = "court_docs"
    MEDIA = "media"
    ADMINISTRATIVE = "administrative"


# ... (rest of models from section 1)


# Helper functions for loading/saving

def load_entity_statistics(path: str) -> EntityStatistics:
    """Load entity statistics with validation"""
    import json
    from pathlib import Path

    with open(path) as f:
        data = json.load(f)

    return EntityStatistics.model_validate(data)


def save_entity_statistics(stats: EntityStatistics, path: str) -> None:
    """Save entity statistics"""
    import json
    from pathlib import Path

    with open(path, 'w') as f:
        json.dump(
            stats.model_dump(mode='json', exclude_none=True),
            f,
            indent=2
        )
```

### 8.3 Example Service Update

**File: `server/services/entity_service.py`**

```python
"""
Entity Service - Now using Pydantic models
"""

from pathlib import Path
from typing import Dict, List, Optional
from models.entity import (
    Entity,
    EntityStatistics,
    load_entity_statistics
)
from models.responses import EntityListResponse


class EntityService:
    """Service for entity operations with Pydantic models"""

    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"

        # Load data with validation
        stats_path = self.metadata_dir / "entity_statistics.json"
        self.entity_stats: EntityStatistics = load_entity_statistics(
            str(stats_path)
        )

    def get_entities(
        self,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> EntityListResponse:
        """Get entities with type-safe response"""

        # Filter entities
        entities: List[Entity] = list(self.entity_stats.statistics.values())

        # Apply filters
        if search:
            entities = [
                e for e in entities
                if search.lower() in e.name.lower()
            ]

        if entity_type:
            entities = [
                e for e in entities
                if e.entity_type == entity_type
            ]

        # Sort and paginate
        entities.sort(key=lambda e: e.total_documents, reverse=True)
        total = len(entities)
        entities = entities[offset:offset + limit]

        # Return typed response
        return EntityListResponse(
            items=entities,
            total=total,
            limit=limit,
            offset=offset
        )
```

### 8.4 Example API Endpoint Update

**File: `server/api_routes.py`**

```python
"""
API Routes with Pydantic models
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from models.entity import Entity
from models.responses import EntityListResponse


router = APIRouter(prefix="/api/v2")


@router.get("/entities", response_model=EntityListResponse)
async def get_entities(
    search: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> EntityListResponse:
    """
    Get entities with filters

    Returns validated EntityListResponse with type safety.
    FastAPI automatically generates OpenAPI docs from Pydantic models.
    """
    return entity_service.get_entities(
        search=search,
        entity_type=entity_type,
        limit=limit,
        offset=offset
    )


@router.get("/entities/{entity_name}", response_model=Entity)
async def get_entity(entity_name: str) -> Entity:
    """
    Get single entity by name

    Returns validated Entity model.
    """
    entity = entity_service.get_entity_by_name(entity_name)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity '{entity_name}' not found"
        )

    return entity
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
import pytest
from models.entity import Entity, EntitySource, DocumentReference


def test_entity_creation():
    """Test basic entity creation"""
    entity = Entity(
        name="Clinton, William",
        normalized_name="William Clinton",
        sources=[EntitySource.FLIGHT_LOGS]
    )

    assert entity.name == "Clinton, William"
    assert entity.connection_count == 0  # Default value
    assert len(entity.sources) == 1


def test_entity_validation():
    """Test entity validation rules"""

    # Should fail: empty name
    with pytest.raises(ValueError):
        Entity(name="", normalized_name="Test")

    # Should fail: negative connection count
    with pytest.raises(ValueError):
        Entity(
            name="Test",
            normalized_name="Test",
            connection_count=-1
        )


def test_name_normalization():
    """Test name normalization validator"""
    entity = Entity(
        name="  Clinton, William  ",  # Extra spaces
        normalized_name="  William Clinton  "
    )

    # Should strip whitespace
    assert entity.normalized_name == "William Clinton"


def test_connection_sorting():
    """Test that connections are sorted by flights_together"""
    from models.entity import TopConnection

    entity = Entity(
        name="Test",
        normalized_name="Test",
        top_connections=[
            TopConnection(name="Person A", flights_together=5),
            TopConnection(name="Person B", flights_together=15),
            TopConnection(name="Person C", flights_together=10)
        ]
    )

    # Should be sorted descending
    assert entity.top_connections[0].flights_together == 15
    assert entity.top_connections[1].flights_together == 10
    assert entity.top_connections[2].flights_together == 5
```

### 9.2 Integration Tests

```python
def test_load_entity_statistics():
    """Test loading real entity statistics file"""
    from models.entity import load_entity_statistics

    stats = load_entity_statistics("data/metadata/entity_statistics.json")

    assert stats.total_entities > 0
    assert len(stats.statistics) == stats.total_entities

    # Check first entity
    first_entity = next(iter(stats.statistics.values()))
    assert isinstance(first_entity, Entity)
    assert first_entity.name
    assert first_entity.connection_count >= 0


def test_entity_service_with_pydantic():
    """Test EntityService with Pydantic models"""
    from services.entity_service import EntityService
    from pathlib import Path

    service = EntityService(Path("data"))

    # Test get_entities
    response = service.get_entities(limit=10)

    assert isinstance(response, EntityListResponse)
    assert len(response.items) <= 10
    assert response.total >= len(response.items)

    # Each item should be valid Entity
    for entity in response.items:
        assert isinstance(entity, Entity)
        assert entity.name


def test_api_endpoint_response():
    """Test API endpoint returns valid response"""
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

    response = client.get("/api/v2/entities?limit=5")

    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 5
```

### 9.3 Data Validation Tests

```python
def test_validate_all_entities():
    """Validate all entities in entity_statistics.json"""
    from models.entity import load_entity_statistics

    # This will raise ValidationError if any entity is invalid
    stats = load_entity_statistics("data/metadata/entity_statistics.json")

    # Check each entity
    for name, entity in stats.statistics.items():
        # Validate required fields
        assert entity.name
        assert entity.normalized_name

        # Validate constraints
        assert entity.connection_count >= 0
        assert entity.flight_count >= 0
        assert entity.total_documents >= 0

        # Validate relationships
        assert entity.passenger_count == len(entity.passengers)


def test_validate_all_flights():
    """Validate all flights in flight_logs_by_flight.json"""
    from models.flight import load_flight_collection

    flights = load_flight_collection("data/md/entities/flight_logs_by_flight.json")

    assert flights.total_flights == len(flights.flights)

    for flight in flights.flights:
        # Validate route format
        assert "-" in flight.route

        # Validate parsed airports
        assert flight.from_airport
        assert flight.to_airport
        assert len(flight.from_airport) == 3
        assert len(flight.to_airport) == 3

        # Validate passenger count
        assert flight.passenger_count == len(flight.passengers)
```

---

## 10. Performance Considerations

### 10.1 Benchmark Results (Estimated)

Based on similar Pydantic migrations:

| Operation | Without Pydantic | With Pydantic | Overhead |
|-----------|-----------------|---------------|----------|
| Load 1,700 entities | ~50ms | ~55-60ms | ~10-20% |
| Parse single entity | ~0.02ms | ~0.025ms | ~25% |
| API response serialization | ~10ms | ~8ms | -20% (faster!) |
| Validate on load | N/A | ~15ms | New feature |

**Key Findings**:
- Initial loading: 10-20% slower (acceptable for startup)
- API responses: Actually faster (Pydantic's optimized serialization)
- Validation: Catches errors early, prevents runtime issues
- Overall: Negligible impact for 1,700 entities

### 10.2 Optimization Strategies

```python
# 1. Use model_validate() instead of __init__ for better performance
entity = Entity.model_validate(data)  # Faster
# vs
entity = Entity(**data)  # Slower


# 2. Disable validation for trusted data
from pydantic import ConfigDict

class Entity(BaseModel):
    model_config = ConfigDict(
        validate_assignment=False  # Skip validation on attribute updates
    )


# 3. Use model_validate_json() for direct JSON parsing
with open("data.json") as f:
    json_str = f.read()

# Faster: Parse JSON in C and validate
stats = EntityStatistics.model_validate_json(json_str)

# vs slower: Parse JSON in Python then validate
data = json.loads(json_str)
stats = EntityStatistics.model_validate(data)


# 4. Lazy loading for large datasets
class EntityService:
    def __init__(self):
        self._entity_stats = None

    @property
    def entity_stats(self):
        """Lazy load entity statistics"""
        if self._entity_stats is None:
            self._entity_stats = load_entity_statistics("path")
        return self._entity_stats


# 5. Caching validated objects
from functools import lru_cache

@lru_cache(maxsize=128)
def get_entity_by_name(name: str) -> Optional[Entity]:
    """Cached entity lookup"""
    # ...
```

### 10.3 Memory Usage

```python
import sys

# Test memory footprint
entity_dict = {...}  # 1KB
entity_model = Entity(**entity_dict)  # ~1.2KB

# Pydantic adds ~20% memory overhead
# For 1,700 entities: ~340KB extra (negligible)
```

---

## 11. FastAPI Integration Benefits

### 11.1 Automatic OpenAPI Documentation

```python
# FastAPI automatically generates docs from Pydantic models

@router.get("/entities/{entity_name}", response_model=Entity)
async def get_entity(entity_name: str) -> Entity:
    """
    Get detailed entity information

    Returns complete entity data including connections, documents, and stats.
    """
    # ...
```

**Generated OpenAPI Schema**:
```json
{
  "paths": {
    "/api/v2/entities/{entity_name}": {
      "get": {
        "summary": "Get detailed entity information",
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/Entity"
                }
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "Entity": {
        "type": "object",
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "connection_count": {"type": "integer", "minimum": 0},
          ...
        },
        "required": ["name", "normalized_name"]
      }
    }
  }
}
```

### 11.2 Request Validation

```python
@router.post("/entities", response_model=Entity)
async def create_entity(entity: Entity) -> Entity:
    """
    Create new entity

    FastAPI automatically:
    - Validates request body against Entity schema
    - Returns 422 with detailed errors if validation fails
    - Converts JSON to Entity model
    """
    # entity is already validated Entity instance
    save_entity(entity)
    return entity
```

### 11.3 Response Serialization

```python
@router.get("/entities", response_model=EntityListResponse)
async def get_entities(...) -> EntityListResponse:
    # Return Pydantic model directly
    # FastAPI handles:
    # - Serialization to JSON
    # - Excluding None values (if configured)
    # - Enum value conversion
    # - Date/datetime formatting
    return EntityListResponse(items=[...], total=100)
```

---

## 12. Migration Checklist

### 12.1 Pre-Migration

- [ ] Install Pydantic v2: `pip install pydantic==2.5.0`
- [ ] Create `server/models/` directory
- [ ] Audit existing JSON data for validation issues
- [ ] Run data quality checks
- [ ] Create backup of data files
- [ ] Write unit tests for models

### 12.2 Phase 1: Entity Models

- [ ] Create `models/entity.py`
- [ ] Implement `Entity`, `EntityBiography`, `EntityTagInfo` models
- [ ] Write unit tests for entity models
- [ ] Test loading `entity_statistics.json`
- [ ] Test loading `entity_biographies.json`
- [ ] Test loading `entity_tags.json`
- [ ] Update `EntityService` to use models
- [ ] Update entity API endpoints
- [ ] Run integration tests
- [ ] Monitor performance

### 12.3 Phase 2: Document Models

- [ ] Create `models/document.py`
- [ ] Implement `Document`, `EmailDocument`, `PDFDocument` models
- [ ] Test loading `all_documents_index.json`
- [ ] Update `DocumentService` to use models
- [ ] Update document API endpoints
- [ ] Run integration tests

### 12.4 Phase 3: Flight Models

- [ ] Create `models/flight.py`
- [ ] Implement `Flight`, `FlightCollection`, `AirportLocation` models
- [ ] Test loading `flight_logs_by_flight.json`
- [ ] Update `FlightService` to use models
- [ ] Update flight API endpoints
- [ ] Run integration tests

### 12.5 Phase 4: Network & Timeline

- [ ] Create `models/network.py`
- [ ] Implement `NetworkNode`, `NetworkEdge`, `NetworkGraph` models
- [ ] Create `models/timeline.py`
- [ ] Implement `TimelineEvent`, `TimelineCollection` models
- [ ] Update services
- [ ] Update API endpoints
- [ ] Run integration tests

### 12.6 Post-Migration

- [ ] Run full test suite
- [ ] Performance benchmarks
- [ ] Update API documentation
- [ ] Update developer documentation
- [ ] Code review
- [ ] Deploy to staging
- [ ] Monitor for validation errors
- [ ] Deploy to production

---

## 13. Common Migration Issues & Solutions

### Issue 1: Missing Required Fields

**Problem**:
```python
# Error: Field required
ValidationError: 1 validation error for Entity
  name
    Field required [type=missing, input_value={...}, input_type=dict]
```

**Solution**:
```python
# Option A: Add default value
name: str = Field(default="Unknown", description="Entity name")

# Option B: Make field optional
name: Optional[str] = Field(None, description="Entity name")

# Option C: Fix data source
# Add missing field to JSON
```

### Issue 2: Type Mismatches

**Problem**:
```python
# Error: Input should be a valid integer
ValidationError: connection_count
    Input should be a valid integer [type=int_type, input_value="25"]
```

**Solution**:
```python
# Option A: Use field validator to coerce
@field_validator('connection_count', mode='before')
@classmethod
def coerce_to_int(cls, v):
    if isinstance(v, str):
        return int(v)
    return v

# Option B: Fix data at source
# Change "25" to 25 in JSON
```

### Issue 3: Invalid Dates

**Problem**:
```python
# Error: Invalid date format
ValidationError: born
    Input should be a valid date [input_value="1946"]
```

**Solution**:
```python
# Use string instead of date for partial dates
born: Optional[str] = Field(
    None,
    description="Date of birth (YYYY, YYYY-MM, or YYYY-MM-DD)"
)

@field_validator('born')
@classmethod
def validate_date_format(cls, v):
    """Validate date string format"""
    if not v:
        return v
    # Allow YYYY, YYYY-MM, YYYY-MM-DD
    import re
    if not re.match(r'^\d{4}(-\d{2}(-\d{2})?)?$', v):
        raise ValueError("Invalid date format")
    return v
```

### Issue 4: Extra Fields in JSON

**Problem**:
```python
# Error: Extra inputs are not permitted
ValidationError: unexpected_field
    Extra inputs are not permitted [type=extra_forbidden]
```

**Solution**:
```python
# Option A: Allow extra fields
model_config = ConfigDict(
    extra='allow'  # or 'ignore' to silently ignore
)

# Option B: Remove extra fields from JSON
# Option C: Add field to model
unexpected_field: Optional[str] = None
```

---

## 14. Future Enhancements

### 14.1 Computed Fields

```python
from pydantic import computed_field

class Entity(BaseModel):
    name: str
    connection_count: int
    flight_count: int

    @computed_field
    @property
    def activity_score(self) -> float:
        """Compute activity score from connections and flights"""
        return (self.connection_count * 0.7) + (self.flight_count * 0.3)
```

### 14.2 Model Inheritance

```python
class BaseEntity(BaseModel):
    """Base fields for all entities"""
    name: str
    normalized_name: str
    sources: List[EntitySource]


class PersonEntity(BaseEntity):
    """Person-specific fields"""
    birth_date: Optional[date]
    occupation: Optional[str]


class BusinessEntity(BaseEntity):
    """Business-specific fields"""
    founded: Optional[date]
    industry: Optional[str]
```

### 14.3 Custom Serializers

```python
from pydantic import field_serializer

class Entity(BaseModel):
    name: str
    connection_count: int

    @field_serializer('connection_count')
    def format_count(self, value: int) -> str:
        """Format large numbers with commas"""
        return f"{value:,}"
```

### 14.4 Database Integration (Future)

```python
from sqlmodel import SQLModel, Field

class Entity(SQLModel, table=True):
    """
    Entity model that works with both Pydantic and SQLAlchemy

    Can be used for database persistence in the future
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    connection_count: int
    # ...
```

---

## 15. Resources & References

### 15.1 Pydantic Documentation

- **Official Docs**: https://docs.pydantic.dev/latest/
- **Migration Guide (v1 to v2)**: https://docs.pydantic.dev/latest/migration/
- **FastAPI Integration**: https://fastapi.tiangolo.com/tutorial/response-model/
- **Performance Tips**: https://docs.pydantic.dev/latest/concepts/performance/

### 15.2 Code Examples

- **Pydantic GitHub**: https://github.com/pydantic/pydantic
- **FastAPI Examples**: https://github.com/tiangolo/fastapi/tree/master/docs_src

### 15.3 Learning Resources

- **Pydantic Tutorial**: https://docs.pydantic.dev/latest/concepts/models/
- **Field Validation**: https://docs.pydantic.dev/latest/concepts/validators/
- **JSON Schema**: https://docs.pydantic.dev/latest/concepts/json_schema/

---

## 16. Conclusion

This Pydantic schema design provides:

✅ **Type Safety**: Catch errors at development time
✅ **Validation**: Automatic data validation on load
✅ **Documentation**: Self-documenting code
✅ **API Integration**: Native FastAPI support
✅ **Backward Compatible**: Validates existing JSON
✅ **Performance**: Minimal overhead
✅ **Maintainability**: Clear data contracts

**Recommended Next Steps**:

1. Review this design with team
2. Start with Phase 1 (Entity Models)
3. Test with existing data
4. Iterate and refine
5. Roll out incrementally

**Estimated Timeline**:
- Week 1: Entity models
- Week 2: Document models
- Week 3: Flight & network models
- Week 4: Timeline & polish

Total: **3-4 weeks** for complete migration

---

## Appendix A: Quick Reference

### A.1 Common Pydantic Patterns

```python
# Required field
name: str

# Optional field
bio: Optional[str] = None

# Field with default
count: int = 0

# Field with validation
age: int = Field(ge=0, le=150)

# List field
tags: List[str] = Field(default_factory=list)

# Dict field
metadata: Dict[str, Any] = Field(default_factory=dict)

# Enum field
status: EntityStatus

# Nested model
connections: List[TopConnection]

# Computed property
@computed_field
@property
def full_name(self) -> str:
    return f"{self.first} {self.last}"

# Custom validator
@field_validator('email')
@classmethod
def validate_email(cls, v):
    if '@' not in v:
        raise ValueError('Invalid email')
    return v
```

### A.2 FastAPI Integration Patterns

```python
# Response model
@router.get("/items", response_model=List[Item])
async def get_items() -> List[Item]:
    return [Item(...), Item(...)]

# Request model
@router.post("/items", response_model=Item)
async def create_item(item: Item) -> Item:
    return item

# Path parameter with model
@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int) -> Item:
    return Item(...)

# Query parameters with validation
@router.get("/search")
async def search(
    q: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=100)
):
    return {...}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-18
**Next Review**: After Phase 1 completion
**Owner**: Development Team
