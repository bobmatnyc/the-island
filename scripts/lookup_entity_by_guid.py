#!/usr/bin/env python3
"""
Look up entity by GUID or entity ID.

Demonstrates how to use the new GUID system for entity lookups.

Usage:
    python scripts/lookup_entity_by_guid.py <guid_or_id>

Examples:
    python scripts/lookup_entity_by_guid.py 43886eef-f28a-549d-8ae0-8409c2be68c4
    python scripts/lookup_entity_by_guid.py jeffrey_epstein
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional


ENTITY_FILE = Path(__file__).parent.parent / "data" / "metadata" / "entity_statistics.json"


def load_entities() -> Dict[str, Any]:
    """Load entity statistics from JSON file.

    Returns:
        Dictionary with entity statistics
    """
    with open(ENTITY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def lookup_by_id(entity_id: str, statistics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Look up entity by entity ID.

    Args:
        entity_id: Entity identifier (e.g., "jeffrey_epstein")
        statistics: Entity statistics dictionary

    Returns:
        Entity data or None if not found
    """
    return statistics.get(entity_id)


def lookup_by_guid(guid: str, statistics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Look up entity by GUID.

    Args:
        guid: Entity GUID (e.g., "43886eef-f28a-549d-8ae0-8409c2be68c4")
        statistics: Entity statistics dictionary

    Returns:
        Entity data or None if not found
    """
    # Linear search through entities to find matching GUID
    # For production, consider building a GUID index for O(1) lookup
    for entity_data in statistics.values():
        if entity_data.get("guid") == guid:
            return entity_data
    return None


def is_guid(value: str) -> bool:
    """Check if string looks like a GUID.

    Args:
        value: String to check

    Returns:
        True if string matches UUID format
    """
    # UUIDs are 36 characters: 8-4-4-4-12 hex digits with hyphens
    if len(value) != 36:
        return False
    if value.count("-") != 4:
        return False
    return True


def format_entity_display(entity: Dict[str, Any]) -> str:
    """Format entity data for display.

    Args:
        entity: Entity data dictionary

    Returns:
        Formatted string for display
    """
    lines = [
        "=" * 70,
        "ENTITY DETAILS",
        "=" * 70,
        f"Name:               {entity.get('name', 'N/A')}",
        f"Entity ID:          {entity.get('id', 'N/A')}",
        f"GUID:               {entity.get('guid', 'N/A')}",
        "",
        "Statistics:",
        f"  Connection Count: {entity.get('connection_count', 0)}",
        f"  Document Count:   {entity.get('total_documents', 0)}",
        f"  Flight Count:     {entity.get('flight_count', 0)}",
        f"  In Black Book:    {entity.get('in_black_book', False)}",
        f"  Is Billionaire:   {entity.get('is_billionaire', False)}",
        "",
        "Sources:",
    ]

    sources = entity.get('sources', [])
    if sources:
        for source in sources:
            lines.append(f"  - {source}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Categories:")
    categories = entity.get('categories', [])
    if categories:
        for category in categories:
            lines.append(f"  - {category}")
    else:
        lines.append("  (none)")

    if entity.get('has_connections'):
        lines.append("")
        lines.append("Top Connections:")
        top_connections = entity.get('top_connections', [])
        for conn in top_connections[:5]:  # Show top 5
            lines.append(f"  - {conn}")

    lines.append("=" * 70)
    return "\n".join(lines)


def main() -> None:
    """Main execution function."""
    if len(sys.argv) < 2:
        print("Usage: python lookup_entity_by_guid.py <guid_or_id>")
        print("\nExamples:")
        print("  python lookup_entity_by_guid.py 43886eef-f28a-549d-8ae0-8409c2be68c4")
        print("  python lookup_entity_by_guid.py jeffrey_epstein")
        sys.exit(1)

    search_value = sys.argv[1].strip()

    # Load entity data
    data = load_entities()
    statistics = data["statistics"]

    print(f"Searching for: {search_value}")
    print()

    # Determine if searching by GUID or ID
    if is_guid(search_value):
        print("Detected GUID format, searching by GUID...")
        entity = lookup_by_guid(search_value, statistics)
    else:
        print("Detected entity ID format, searching by ID...")
        entity = lookup_by_id(search_value, statistics)

    if entity:
        print(format_entity_display(entity))
    else:
        print("✗ Entity not found")
        print("\nTips:")
        print("  - For GUID search: Use full UUID (36 characters)")
        print("  - For ID search: Use snake_case entity ID")
        print("\nExample GUIDs:")
        print("  Jeffrey Epstein:    43886eef-f28a-549d-8ae0-8409c2be68c4")
        print("  Ghislaine Maxwell:  2b3bdb1f-adb2-5050-b437-e16a1fb476e8")
        print("  Donald Trump:       6467fdc0-0874-575d-b28e-96b06d131063")


if __name__ == "__main__":
    main()
