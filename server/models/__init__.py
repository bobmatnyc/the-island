"""
Models package for Epstein Archive server

Contains Pydantic models for:
- Entity models: Entity, EntityBiography, EntityTag
- Network models: NetworkNode, NetworkEdge, NetworkGraph
- Enums: EntityType, SourceType, DocumentType
- Suggested sources and citations
"""
from .suggested_source import (
    SourcePriority,
    SourceStatus,
    SuggestedSource,
    SuggestedSourceCreate,
    SuggestedSourceUpdate,
)
from .entity import Entity, EntityBiography, EntityTag, DocumentReference, TopConnection
from .network import NetworkNode, NetworkEdge, NetworkGraph
from .enums import EntityType, SourceType, DocumentType


__all__ = [
    # Suggested source models
    "SourcePriority",
    "SourceStatus",
    "SuggestedSource",
    "SuggestedSourceCreate",
    "SuggestedSourceUpdate",
    # Entity models
    "Entity",
    "EntityBiography",
    "EntityTag",
    "DocumentReference",
    "TopConnection",
    # Network models
    "NetworkNode",
    "NetworkEdge",
    "NetworkGraph",
    # Enums
    "EntityType",
    "SourceType",
    "DocumentType",
]
