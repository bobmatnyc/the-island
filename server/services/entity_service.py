"""
Entity Service - Business logic for entity operations

Design Decision: Centralized Entity Management
Rationale: All entity-related business logic in one place for consistency,
testability, and easy modification. Frontend makes simple API calls.

Handles:
- Entity filtering and searching
- Type detection (person, business, location, organization)
- Biography and tag integration
- Connection graph queries

Pydantic Integration (Phase 1):
- Feature flag: USE_PYDANTIC environment variable
- Backward compatible: Falls back to dict if validation fails
- Dual storage: Both dict and Pydantic models during migration
- Performance: <20% overhead with validation enabled
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import sys

# Import entity filtering utility
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts/utils"))
from entity_filtering import EntityFilter

# Import Pydantic models
from models import Entity, EntityBiography, EntityTag, NetworkNode, NetworkEdge, NetworkGraph
from pydantic import ValidationError

# Feature flag for Pydantic validation
USE_PYDANTIC = os.getenv('USE_PYDANTIC', 'false').lower() == 'true'

# Setup logging
logger = logging.getLogger(__name__)


class EntityService:
    """Service for entity data operations

    Pydantic Integration:
    - USE_PYDANTIC=true: Validates and stores Pydantic models
    - USE_PYDANTIC=false: Uses raw dicts (default, backward compatible)
    - Dual storage during migration for graceful fallback
    """

    def __init__(self, data_path: Path):
        """Initialize entity service

        Args:
            data_path: Path to data directory containing metadata
        """
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"
        self.md_dir = data_path / "md"

        # Initialize entity filter
        self.entity_filter = EntityFilter()

        # Data caches (dict storage - always maintained)
        self.entity_stats: Dict = {}
        self.entity_bios: Dict = {}
        self.entity_tags: Dict = {}
        self.network_data: Dict = {}
        self.semantic_index: Dict = {}

        # Pydantic model storage (when USE_PYDANTIC=true)
        self.entities_pydantic: Dict[str, Entity] = {}
        self.bios_pydantic: Dict[str, EntityBiography] = {}
        self.tags_pydantic: Dict[str, EntityTag] = {}
        self.network_graph: Optional[NetworkGraph] = None

        # Validation statistics
        self.validation_stats = {
            "total_entities": 0,
            "valid_entities": 0,
            "failed_entities": 0,
            "validation_errors": []
        }

        # Load data
        self.load_data()

    def load_data(self):
        """Load all entity-related data from JSON files

        If USE_PYDANTIC=true, validates data with Pydantic models.
        Falls back to dict storage if validation fails.
        """
        # Load entity statistics
        stats_path = self.metadata_dir / "entity_statistics.json"
        if stats_path.exists():
            with open(stats_path) as f:
                data = json.load(f)
                self.entity_stats = data.get("statistics", {})

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_entities()

        # Load biographies
        bio_path = self.metadata_dir / "entity_biographies.json"
        if bio_path.exists():
            with open(bio_path) as f:
                data = json.load(f)
                self.entity_bios = data.get("entities", {})

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_biographies()

        # Load tags
        tags_path = self.metadata_dir / "entity_tags.json"
        if tags_path.exists():
            with open(tags_path) as f:
                data = json.load(f)
                self.entity_tags = data.get("entities", {})

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_tags()

        # Load network
        network_path = self.metadata_dir / "entity_network.json"
        if network_path.exists():
            with open(network_path) as f:
                self.network_data = json.load(f)

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_network()

        # Load semantic index
        semantic_path = self.metadata_dir / "semantic_index.json"
        if semantic_path.exists():
            with open(semantic_path) as f:
                data = json.load(f)
                self.semantic_index = data.get("entity_to_documents", {})

        # Log validation results if Pydantic enabled
        if USE_PYDANTIC:
            logger.info(
                f"Pydantic validation complete: "
                f"{self.validation_stats['valid_entities']}/{self.validation_stats['total_entities']} "
                f"entities valid, {self.validation_stats['failed_entities']} failed"
            )

    def _validate_entities(self):
        """Validate entity_stats with Pydantic Entity model"""
        self.validation_stats["total_entities"] = len(self.entity_stats)

        for name, entity_data in self.entity_stats.items():
            try:
                # Convert dict to Pydantic model
                entity = Entity(**entity_data)
                self.entities_pydantic[name] = entity
                self.validation_stats["valid_entities"] += 1

            except ValidationError as e:
                self.validation_stats["failed_entities"] += 1
                self.validation_stats["validation_errors"].append({
                    "entity": name,
                    "error": str(e),
                    "error_count": e.error_count()
                })
                logger.warning(f"Validation failed for entity '{name}': {e}")

                # Fallback: Keep dict version
                # Entity remains in self.entity_stats for backward compat

    def _validate_biographies(self):
        """Validate entity_bios with Pydantic EntityBiography model"""
        for entity_name, bio_data in self.entity_bios.items():
            try:
                # Prepare data for Pydantic model
                bio_dict = {
                    "entity_name": entity_name,
                    "biography": bio_data.get("biography", ""),
                    "last_updated": bio_data.get("last_updated")
                }
                bio = EntityBiography(**bio_dict)
                self.bios_pydantic[entity_name] = bio

            except ValidationError as e:
                logger.warning(f"Validation failed for biography '{entity_name}': {e}")

    def _validate_tags(self):
        """Validate entity_tags with Pydantic EntityTag model"""
        for entity_name, tag_data in self.entity_tags.items():
            try:
                # Prepare data for Pydantic model
                tag_dict = {
                    "entity_name": entity_name,
                    "tags": tag_data.get("tags", []),
                    "primary_tag": tag_data.get("primary_tag")
                }
                tags = EntityTag(**tag_dict)
                self.tags_pydantic[entity_name] = tags

            except ValidationError as e:
                logger.warning(f"Validation failed for tags '{entity_name}': {e}")

    def _validate_network(self):
        """Validate network_data with Pydantic NetworkGraph model"""
        try:
            # Extract nodes and edges
            nodes_data = self.network_data.get("nodes", [])
            edges_data = self.network_data.get("edges", [])

            # Convert to Pydantic models
            nodes = [NetworkNode(**node) for node in nodes_data]
            edges = [NetworkEdge(**edge) for edge in edges_data]

            # Create graph with validation
            self.network_graph = NetworkGraph(
                nodes=nodes,
                edges=edges,
                metadata=self.network_data.get("metadata")
            )
            logger.info(
                f"Network graph validated: {len(nodes)} nodes, {len(edges)} edges"
            )

        except ValidationError as e:
            logger.error(f"Network graph validation failed: {e}")
            # Fallback: Keep dict version in self.network_data

    def detect_entity_type(self, entity_name: str) -> str:
        """Detect entity type from name

        Args:
            entity_name: Entity name to analyze

        Returns:
            Entity type: 'person', 'business', 'location', or 'organization'
        """
        name = entity_name.lower()

        # Business/Organization indicators
        business_keywords = [
            'corp', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited',
            'company', 'co.', 'enterprises', 'group', 'holdings', 'international',
            'partners', 'associates', 'ventures', 'capital', 'investments',
            'foundation', 'trust', 'fund', 'bank', 'financial', 'consulting'
        ]

        # Location indicators
        location_keywords = [
            'island', 'airport', 'beach', 'estate', 'ranch', 'street', 'avenue',
            'road', 'boulevard', 'drive', 'place', 'manor', 'villa', 'palace',
            'hotel', 'resort', 'club'
        ]

        # Organization indicators (non-profit, government, etc.)
        organization_keywords = [
            'foundation', 'institute', 'university', 'college', 'school',
            'department', 'agency', 'commission', 'board', 'council',
            'society', 'association', 'federation', 'alliance'
        ]

        # Check for business
        if any(keyword in name for keyword in business_keywords):
            return 'business'

        # Check for organization
        if any(keyword in name for keyword in organization_keywords):
            return 'organization'

        # Check for location
        if any(keyword in name for keyword in location_keywords):
            return 'location'

        # Default to person
        return 'person'

    def get_entities(
        self,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        filter_billionaires: bool = False,
        filter_connected: bool = False,
        sort_by: str = "documents",
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """Get filtered and sorted entity list

        Args:
            search: Text search in entity name
            entity_type: Filter by type (person, business, location, organization)
            tag: Filter by tag (from entity_tags.json)
            source: Filter by source (black_book, flight_logs, etc.)
            filter_billionaires: Only show billionaires
            filter_connected: Only show entities with connections
            sort_by: Sort field ('documents', 'connections', 'name')
            limit: Results per page
            offset: Pagination offset

        Returns:
            {
                "entities": List of entities,
                "total": Total matching entities,
                "offset": Pagination offset,
                "limit": Results per page
            }
        """
        entities_list = list(self.entity_stats.values())

        # Filter out generic entities (Male, Female, etc.)
        entities_list = [
            e for e in entities_list
            if not self.entity_filter.is_generic(e.get("name", ""))
        ]

        # Text search
        if search:
            search_lower = search.lower()
            entities_list = [
                e for e in entities_list
                if search_lower in e.get("name", "").lower()
            ]

        # Type filter
        if entity_type:
            entities_list = [
                e for e in entities_list
                if self.detect_entity_type(e.get("name", "")) == entity_type
            ]

        # Tag filter
        if tag:
            entities_list = [
                e for e in entities_list
                if tag in self.entity_tags.get(e.get("name", ""), {}).get("tags", [])
            ]

        # Source filter
        if source:
            entities_list = [
                e for e in entities_list
                if source in e.get("sources", [])
            ]

        # Billionaire filter
        if filter_billionaires:
            entities_list = [
                e for e in entities_list
                if e.get("is_billionaire", False)
            ]

        # Connected filter
        if filter_connected:
            entities_list = [
                e for e in entities_list
                if e.get("connection_count", 0) > 0
            ]

        # Enrich with type and bio/tag data
        for entity in entities_list:
            entity_name = entity.get("name", "")
            entity["entity_type"] = self.detect_entity_type(entity_name)

            # Add bio if available
            if entity_name in self.entity_bios:
                entity["bio"] = self.entity_bios[entity_name]

            # Add tags if available
            if entity_name in self.entity_tags:
                entity["tags"] = self.entity_tags[entity_name].get("tags", [])
                entity["primary_tag"] = self.entity_tags[entity_name].get("primary_tag")

        # Sort
        if sort_by == "documents":
            entities_list.sort(key=lambda e: e.get("total_documents", 0), reverse=True)
        elif sort_by == "connections":
            entities_list.sort(key=lambda e: e.get("connection_count", 0), reverse=True)
        elif sort_by == "name":
            entities_list.sort(key=lambda e: e.get("name", ""))

        # Paginate
        total = len(entities_list)
        entities_page = entities_list[offset:offset+limit]

        return {
            "entities": entities_page,
            "total": total,
            "offset": offset,
            "limit": limit
        }

    def get_entity_by_name(self, name: str) -> Optional[Union[Entity, Dict]]:
        """Get single entity by name

        Args:
            name: Entity name (exact match)

        Returns:
            Entity data (Pydantic model if USE_PYDANTIC=true, dict otherwise)
            or None if not found

        Pydantic Mode:
            Returns Entity model with .model_dump() available for serialization
        Dict Mode:
            Returns enriched dict with bio/tags embedded
        """
        # Check Pydantic storage first if enabled
        if USE_PYDANTIC and name in self.entities_pydantic:
            return self.entities_pydantic[name]

        # Fallback to dict storage
        entity = self.entity_stats.get(name)

        if not entity:
            return None

        # Enrich dict with additional data
        entity["entity_type"] = self.detect_entity_type(name)

        if name in self.entity_bios:
            entity["bio"] = self.entity_bios[name]

        if name in self.entity_tags:
            entity["tags"] = self.entity_tags[name].get("tags", [])
            entity["primary_tag"] = self.entity_tags[name].get("primary_tag")

        # Add document list from semantic index
        if name in self.semantic_index:
            entity["documents"] = self.semantic_index[name]

        return entity

    def get_validation_report(self) -> Dict:
        """Get Pydantic validation statistics

        Returns:
            Validation stats including errors found during load

        Only available when USE_PYDANTIC=true
        """
        if not USE_PYDANTIC:
            return {
                "enabled": False,
                "message": "Pydantic validation not enabled (set USE_PYDANTIC=true)"
            }

        return {
            "enabled": True,
            "total_entities": self.validation_stats["total_entities"],
            "valid_entities": self.validation_stats["valid_entities"],
            "failed_entities": self.validation_stats["failed_entities"],
            "success_rate": (
                self.validation_stats["valid_entities"] / self.validation_stats["total_entities"]
                if self.validation_stats["total_entities"] > 0 else 0
            ),
            "errors": self.validation_stats["validation_errors"][:10],  # First 10 errors
            "total_errors": len(self.validation_stats["validation_errors"])
        }

    def to_dict(self, entity: Union[Entity, Dict]) -> Dict:
        """Convert entity to dict for API responses

        Args:
            entity: Entity (Pydantic model or dict)

        Returns:
            Dict representation

        Design Decision: Transparent serialization
        Rationale: API consumers don't need to know if Pydantic is enabled
        """
        if isinstance(entity, Entity):
            return entity.model_dump()
        return entity

    def get_entity_connections(
        self,
        entity_name: str,
        max_hops: int = 2,
        min_strength: int = 1
    ) -> Dict:
        """Get entity's network connections

        Args:
            entity_name: Entity name
            max_hops: Maximum degrees of separation (1-3)
            min_strength: Minimum connection strength (number of flights)

        Returns:
            {
                "entity": Source entity,
                "direct_connections": List of directly connected entities,
                "network": Subgraph of connections up to max_hops
            }
        """
        # Find entity node
        entity_node = None
        for node in self.network_data.get("nodes", []):
            if node.get("name") == entity_name:
                entity_node = node
                break

        if not entity_node:
            return {
                "entity": None,
                "direct_connections": [],
                "network": {"nodes": [], "edges": []}
            }

        # Get direct connections (1 hop)
        direct_edges = [
            e for e in self.network_data.get("edges", [])
            if (e.get("source") == entity_node["id"] or e.get("target") == entity_node["id"])
            and e.get("flight_count", 0) >= min_strength
        ]

        # Get connected node IDs
        connected_ids = set()
        for edge in direct_edges:
            if edge["source"] == entity_node["id"]:
                connected_ids.add(edge["target"])
            else:
                connected_ids.add(edge["source"])

        # Get connected nodes
        connected_nodes = [
            n for n in self.network_data.get("nodes", [])
            if n["id"] in connected_ids
        ]

        # If max_hops > 1, expand network
        if max_hops > 1:
            # TODO: Implement multi-hop traversal
            pass

        return {
            "entity": entity_node,
            "direct_connections": connected_nodes,
            "network": {
                "nodes": [entity_node] + connected_nodes,
                "edges": direct_edges
            }
        }

    def get_statistics(self) -> Dict:
        """Get entity statistics

        Returns:
            {
                "total_entities": Total count,
                "by_type": Count per type,
                "by_tag": Count per tag,
                "billionaires": Count,
                "connected": Count with connections
            }
        """
        all_entities = list(self.entity_stats.values())

        # Filter generic entities
        real_entities = [
            e for e in all_entities
            if not self.entity_filter.is_generic(e.get("name", ""))
        ]

        # Count by type
        by_type = {}
        for entity in real_entities:
            entity_type = self.detect_entity_type(entity.get("name", ""))
            by_type[entity_type] = by_type.get(entity_type, 0) + 1

        # Count by tag
        by_tag = {}
        for entity_name, tag_data in self.entity_tags.items():
            for tag in tag_data.get("tags", []):
                by_tag[tag] = by_tag.get(tag, 0) + 1

        # Count billionaires
        billionaires = sum(1 for e in real_entities if e.get("is_billionaire", False))

        # Count connected
        connected = sum(1 for e in real_entities if e.get("connection_count", 0) > 0)

        return {
            "total_entities": len(real_entities),
            "by_type": by_type,
            "by_tag": by_tag,
            "billionaires": billionaires,
            "connected": connected,
            "network_nodes": len(self.network_data.get("nodes", [])),
            "network_edges": len(self.network_data.get("edges", []))
        }
