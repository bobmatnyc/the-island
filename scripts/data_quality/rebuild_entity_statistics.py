#!/usr/bin/env python3
"""
Rebuild entity_statistics.json from ENTITIES_INDEX.json
Fixes duplicate entities and removes stale data
"""
import json
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
ENTITY_STATS = PROJECT_ROOT / "data/metadata/entity_statistics.json"


def rebuild_statistics():
    """Rebuild entity_statistics.json from clean primary index"""

    # Read clean primary index
    with open(ENTITIES_INDEX, encoding="utf-8") as f:
        entities_index = json.load(f)

    # Extract entities array
    entities = entities_index.get("entities", [])

    print(f"📊 Reading from primary index: {ENTITIES_INDEX}")
    print(f"   Found {len(entities)} entities")

    # Transform to entity_statistics format (keyed by normalized_name for frontend)
    entity_statistics = {
        "generated": datetime.now().isoformat(),
        "total_entities": len(entities),
        "statistics": {},
    }

    for idx, entity_data in enumerate(entities):
        # Use normalized_name as key (frontend expects this)
        name = entity_data.get("normalized_name") or entity_data.get("name")

        if not name:
            print(f"⚠️  Skipping entity at index {idx} - no name found")
            continue

        # Count connections from flight logs
        connection_count = 0
        if "routes" in entity_data and entity_data.get("routes"):
            connection_count = len(entity_data.get("routes", []))

        # Build statistics entry
        entity_statistics["statistics"][name] = {
            "name": entity_data.get("name"),
            "name_variations": [entity_data.get("name"), entity_data.get("normalized_name")],
            "in_black_book": "black_book" in entity_data.get("sources", []),
            "is_billionaire": entity_data.get("is_billionaire", False),
            "categories": entity_data.get("categories", []),
            "sources": entity_data.get("sources", []),
            "total_documents": 0,  # Will be populated by document processing
            "document_types": {},
            "documents": [],
            "flight_count": entity_data.get("flights", 0),
            "connection_count": connection_count,
            "top_connections": [],  # Can be enhanced later
            "has_connections": connection_count > 0,
            "appears_in_multiple_sources": len(entity_data.get("sources", [])) > 1,
        }

    # Write rebuilt statistics
    with open(ENTITY_STATS, "w", encoding="utf-8") as f:
        json.dump(entity_statistics, f, indent=2, ensure_ascii=False)

    print("\n✅ Rebuilt entity_statistics.json")
    print(f"   Total entities: {entity_statistics['total_entities']}")
    print(f"   Statistics entries: {len(entity_statistics['statistics'])}")
    print(f"   Timestamp: {entity_statistics['generated']}")

    # Check for Jeffrey Epstein
    epstein_entries = [
        k for k in entity_statistics["statistics"] if "Epstein" in k and "Jeffrey" in k
    ]
    print(f"\n🔍 Jeffrey Epstein entries found: {len(epstein_entries)}")
    for entry in epstein_entries:
        print(f"   - {entry}")

    # Check for PORTABLES
    portables_entries = [k for k in entity_statistics["statistics"] if "PORTABLES" in k.upper()]
    print(f"\n🔍 PORTABLES entries found: {len(portables_entries)}")
    for entry in portables_entries:
        print(f"   - {entry}")

    return entity_statistics["total_entities"]


if __name__ == "__main__":
    count = rebuild_statistics()
    print("\n🎯 Entity statistics rebuilt successfully!")
    print(f"   {count} entities ready for display")
