"""
Models package for Epstein Archive server

Contains Pydantic models for:
- Entity models: Entity, EntityBiography, EntityTag
- Network models: NetworkNode, NetworkEdge, NetworkGraph
- Document models: Document, EmailDocument, PDFDocument, DocumentIndex
- Flight models: Flight, FlightCollection, AirportLocation
- Timeline models: TimelineEvent, TimelineCollection, TimelineFilter
- Enums: EntityType, SourceType, DocumentType, TimelineCategory
- Suggested sources and citations
"""

# Phase 2 models
from .document import (
    Document,
    DocumentClassification,
    DocumentIndex,
    DocumentIndexStatistics,
    DocumentMetadata,
    DocumentSource,
    EmailDocument,
    PDFDocument,
)
from .document import DocumentType as DocType
from .entity import DocumentReference, Entity, EntityBiography, EntityTag, TopConnection
from .enums import DocumentType, EntityType, SourceType
from .flight import (
    AirportLocation,
    Flight,
    FlightCollection,
    FlightRoute,
    RouteStatistics,
)
from .network import NetworkEdge, NetworkGraph, NetworkNode
from .suggested_source import (
    SourcePriority,
    SourceStatus,
    SuggestedSource,
    SuggestedSourceCreate,
    SuggestedSourceUpdate,
)
from .timeline import (
    TimelineCategory,
    TimelineCollection,
    TimelineEvent,
    TimelineFilter,
)


__all__ = [
    "AirportLocation",
    "DocType",
    # Document models (Phase 2)
    "Document",
    "DocumentClassification",
    "DocumentIndex",
    "DocumentIndexStatistics",
    "DocumentMetadata",
    "DocumentReference",
    "DocumentSource",
    "DocumentType",
    "EmailDocument",
    # Entity models
    "Entity",
    "EntityBiography",
    "EntityTag",
    # Enums
    "EntityType",
    # Flight models (Phase 2)
    "Flight",
    "FlightCollection",
    "FlightRoute",
    "NetworkEdge",
    "NetworkGraph",
    # Network models
    "NetworkNode",
    "PDFDocument",
    "RouteStatistics",
    # Suggested source models
    "SourcePriority",
    "SourceStatus",
    "SourceType",
    "SuggestedSource",
    "SuggestedSourceCreate",
    "SuggestedSourceUpdate",
    "TimelineCategory",
    "TimelineCollection",
    # Timeline models (Phase 2)
    "TimelineEvent",
    "TimelineFilter",
    "TopConnection",
]
