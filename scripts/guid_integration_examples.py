#!/usr/bin/env python3
"""
GUID Integration Examples

Demonstrates how to integrate entity GUID lookups into your existing codebase.
These patterns show best practices for using GUIDs in APIs, databases, and UIs.

Usage:
    python scripts/guid_integration_examples.py
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional


ENTITY_FILE = Path(__file__).parent.parent / "data" / "metadata" / "entity_statistics.json"


class EntityService:
    """Service layer for entity operations with GUID support.

    Example service showing how to integrate GUID lookups into your application.
    """

    def __init__(self, entity_file: Path = ENTITY_FILE):
        """Initialize entity service.

        Args:
            entity_file: Path to entity statistics JSON file
        """
        self.entity_file = entity_file
        self._entities: Optional[Dict[str, Any]] = None
        self._guid_index: Optional[Dict[str, str]] = None

    def _load_entities(self) -> None:
        """Load entities from JSON file and build GUID index.

        Builds O(1) lookup index for GUID searches.
        """
        if self._entities is not None:
            return

        with open(self.entity_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._entities = data["statistics"]

        # Build GUID -> entity_id index for O(1) lookups
        self._guid_index = {
            entity["guid"]: entity_id
            for entity_id, entity in self._entities.items()
            if "guid" in entity
        }

        print(f"✓ Loaded {len(self._entities)} entities")
        print(f"✓ Built GUID index with {len(self._guid_index)} entries")

    def get_entity(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID or GUID (auto-detect).

        Args:
            identifier: Entity ID or GUID

        Returns:
            Entity data or None if not found
        """
        self._load_entities()

        # Try as GUID first (36 characters with hyphens)
        if len(identifier) == 36 and identifier.count("-") == 4:
            entity_id = self._guid_index.get(identifier)
            if entity_id:
                return self._entities[entity_id]

        # Try as entity ID
        return self._entities.get(identifier)

    def generate_guid_for_id(self, entity_id: str) -> str:
        """Generate GUID for entity ID (for validation/testing).

        Args:
            entity_id: Entity identifier

        Returns:
            Generated GUID
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, entity_id))

    def search_entities(
        self,
        query: str,
        in_black_book: Optional[bool] = None,
        min_connections: int = 0
    ) -> list[Dict[str, Any]]:
        """Search entities with filters.

        Args:
            query: Search term (matches name or ID)
            in_black_book: Filter by black book status
            min_connections: Minimum connection count

        Returns:
            List of matching entities
        """
        self._load_entities()

        results = []
        query_lower = query.lower()

        for entity_id, entity in self._entities.items():
            # Text search
            if query_lower not in entity_id.lower() and query_lower not in entity["name"].lower():
                continue

            # Black book filter
            if in_black_book is not None and entity.get("in_black_book") != in_black_book:
                continue

            # Connection count filter
            if entity.get("connection_count", 0) < min_connections:
                continue

            results.append(entity)

        return results


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_1_basic_lookup():
    """Example 1: Basic entity lookup by ID or GUID."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Entity Lookup")
    print("=" * 70)

    service = EntityService()

    # Lookup by entity ID
    entity = service.get_entity("jeffrey_epstein")
    if entity:
        print(f"\n✓ Found by ID: {entity['name']}")
        print(f"  GUID: {entity['guid']}")

    # Lookup by GUID
    guid = "43886eef-f28a-549d-8ae0-8409c2be68c4"
    entity = service.get_entity(guid)
    if entity:
        print(f"\n✓ Found by GUID: {entity['name']}")
        print(f"  ID: {entity['id']}")


def example_2_rest_api_pattern():
    """Example 2: REST API endpoint accepting both ID and GUID."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: REST API Pattern")
    print("=" * 70)

    service = EntityService()

    def get_entity_endpoint(identifier: str) -> Dict[str, Any]:
        """
        REST API endpoint: GET /api/entities/{identifier}

        Accepts both entity ID and GUID for backward compatibility.

        Args:
            identifier: Entity ID or GUID

        Returns:
            API response with entity data
        """
        entity = service.get_entity(identifier)

        if not entity:
            return {
                "status": "error",
                "message": f"Entity not found: {identifier}",
                "code": 404
            }

        return {
            "status": "success",
            "data": {
                "id": entity["id"],
                "guid": entity["guid"],
                "name": entity["name"],
                "connections": entity.get("connection_count", 0),
                "documents": entity.get("total_documents", 0),
                "in_black_book": entity.get("in_black_book", False)
            }
        }

    # Test with ID
    response = get_entity_endpoint("jeffrey_epstein")
    print(f"\nAPI call with ID: {json.dumps(response, indent=2)}")

    # Test with GUID
    response = get_entity_endpoint("43886eef-f28a-549d-8ae0-8409c2be68c4")
    print(f"\nAPI call with GUID: {json.dumps(response, indent=2)}")


def example_3_url_generation():
    """Example 3: Generating URLs with GUIDs."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: URL Generation with GUIDs")
    print("=" * 70)

    service = EntityService()

    def generate_entity_url(entity: Dict[str, Any]) -> str:
        """Generate URL for entity detail page using GUID.

        Args:
            entity: Entity data

        Returns:
            URL string
        """
        guid = entity.get("guid")
        name_slug = entity["id"]  # Already in slug format

        # Use GUID for URL (more stable, URL-safe)
        return f"/entities/{guid}/{name_slug}"

    # Generate URLs for notable entities
    notable_ids = ["jeffrey_epstein", "ghislaine_maxwell", "donald_trump"]

    print("\nGenerated URLs:")
    for entity_id in notable_ids:
        entity = service.get_entity(entity_id)
        if entity:
            url = generate_entity_url(entity)
            print(f"  {entity['name']:30s} → {url}")


def example_4_database_migration():
    """Example 4: Database migration pattern."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Database Migration Pattern")
    print("=" * 70)

    print("""
    -- SQL migration to add GUID column to entities table

    -- Step 1: Add GUID column (nullable initially)
    ALTER TABLE entities ADD COLUMN guid UUID;

    -- Step 2: Populate GUIDs from entity_id
    UPDATE entities
    SET guid = uuid_generate_v5(
        'dns'::uuid,
        entity_id
    );

    -- Step 3: Add NOT NULL constraint
    ALTER TABLE entities ALTER COLUMN guid SET NOT NULL;

    -- Step 4: Add unique constraint
    ALTER TABLE entities ADD CONSTRAINT entities_guid_unique UNIQUE (guid);

    -- Step 5: Create index for fast GUID lookups
    CREATE INDEX entities_guid_idx ON entities (guid);

    -- Step 6: Update foreign keys to use GUID (optional, for new relationships)
    ALTER TABLE connections ADD COLUMN entity_guid UUID;

    -- Query examples:
    SELECT * FROM entities WHERE guid = '43886eef-f28a-549d-8ae0-8409c2be68c4';
    SELECT * FROM entities WHERE entity_id = 'jeffrey_epstein';  -- Still works!
    """)


def example_5_search_with_filters():
    """Example 5: Advanced search with filters."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Advanced Entity Search")
    print("=" * 70)

    service = EntityService()

    # Search for entities named "Maxwell" in black book with connections
    results = service.search_entities(
        query="maxwell",
        in_black_book=True,
        min_connections=1
    )

    print(f"\nSearch results for 'maxwell' (in black book, with connections):")
    for entity in results[:5]:  # Show first 5
        print(f"  {entity['name']:30s} | GUID: {entity['guid']}")
        print(f"    Connections: {entity.get('connection_count', 0)}")


def example_6_guid_validation():
    """Example 6: GUID validation and generation."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: GUID Validation")
    print("=" * 70)

    service = EntityService()

    # Validate existing entity GUID
    entity_id = "jeffrey_epstein"
    entity = service.get_entity(entity_id)

    if entity:
        stored_guid = entity["guid"]
        generated_guid = service.generate_guid_for_id(entity_id)

        print(f"\nEntity ID:       {entity_id}")
        print(f"Stored GUID:     {stored_guid}")
        print(f"Generated GUID:  {generated_guid}")
        print(f"Match:           {stored_guid == generated_guid} ✓")


def main():
    """Run all examples."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                  ENTITY GUID INTEGRATION EXAMPLES                  ║")
    print("╚════════════════════════════════════════════════════════════════════╝")

    example_1_basic_lookup()
    example_2_rest_api_pattern()
    example_3_url_generation()
    example_4_database_migration()
    example_5_search_with_filters()
    example_6_guid_validation()

    print("\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Integrate EntityService into your FastAPI application")
    print("  2. Update API endpoints to accept both ID and GUID")
    print("  3. Migrate database schema to include GUID column")
    print("  4. Update frontend to use GUIDs in URLs")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
