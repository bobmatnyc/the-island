#!/usr/bin/env python3
"""
Verify and test entity GUID generation.

This script demonstrates:
- GUID determinism (same entity ID always produces same GUID)
- GUID uniqueness across all entities
- GUID format validation

Usage:
    python scripts/verify_entity_guids.py
"""

import json
import uuid
from pathlib import Path
from collections import Counter


ENTITY_FILE = Path(__file__).parent.parent / "data" / "metadata" / "entity_statistics.json"


def test_guid_determinism(entity_id: str, expected_guid: str) -> bool:
    """Test that regenerating GUID produces same result.

    Args:
        entity_id: Entity identifier
        expected_guid: Expected GUID from entity data

    Returns:
        True if GUIDs match, False otherwise
    """
    regenerated = str(uuid.uuid5(uuid.NAMESPACE_DNS, entity_id))
    return regenerated == expected_guid


def main() -> None:
    """Main verification function."""
    print("=" * 70)
    print("Entity GUID Verification")
    print("=" * 70)

    # Load entity data
    with open(ENTITY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    statistics = data["statistics"]
    total_entities = len(statistics)

    print(f"\nTotal entities: {total_entities:,}")

    # Collect all GUIDs
    guids = []
    entities_without_guid = []
    determinism_failures = []

    for entity_id, entity_data in statistics.items():
        if "guid" not in entity_data:
            entities_without_guid.append(entity_id)
            continue

        guid = entity_data["guid"]
        guids.append(guid)

        # Test determinism
        if not test_guid_determinism(entity_id, guid):
            determinism_failures.append(entity_id)

    # Check for missing GUIDs
    print(f"\n✓ Entities with GUIDs: {len(guids):,}")
    if entities_without_guid:
        print(f"✗ Entities missing GUIDs: {len(entities_without_guid)}")
        print(f"  First 5: {entities_without_guid[:5]}")
    else:
        print("✓ All entities have GUIDs")

    # Check for duplicates
    guid_counts = Counter(guids)
    duplicates = {guid: count for guid, count in guid_counts.items() if count > 1}

    if duplicates:
        print(f"\n✗ Duplicate GUIDs found: {len(duplicates)}")
        for guid, count in list(duplicates.items())[:5]:
            print(f"  {guid}: appears {count} times")
    else:
        print("✓ All GUIDs are unique")

    # Check determinism
    if determinism_failures:
        print(f"\n✗ Determinism failures: {len(determinism_failures)}")
        print(f"  First 5: {determinism_failures[:5]}")
    else:
        print("✓ All GUIDs are deterministic (regeneration produces same GUID)")

    # Validate GUID format
    invalid_format = []
    for entity_id, entity_data in statistics.items():
        if "guid" in entity_data:
            try:
                uuid.UUID(entity_data["guid"])
            except ValueError:
                invalid_format.append(entity_id)

    if invalid_format:
        print(f"\n✗ Invalid GUID format: {len(invalid_format)}")
        print(f"  First 5: {invalid_format[:5]}")
    else:
        print("✓ All GUIDs have valid UUID format")

    # Show sample notable entities with GUIDs
    print("\n" + "=" * 70)
    print("Sample Notable Entities with GUIDs")
    print("=" * 70)

    notable_entities = [
        "jeffrey_epstein",
        "ghislaine_maxwell",
        "bill_clinton",
        "donald_trump",
        "prince_andrew",
        "alan_dershowitz",
        "les_wexner"
    ]

    for entity_id in notable_entities:
        if entity_id in statistics:
            entity = statistics[entity_id]
            print(f"\n{entity['name']:30s}")
            print(f"  ID:          {entity_id}")
            print(f"  GUID:        {entity.get('guid', 'N/A')}")
            print(f"  Connections: {entity.get('connection_count', 0)}")
            print(f"  Documents:   {entity.get('total_documents', 0)}")

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    all_passed = (
        len(entities_without_guid) == 0 and
        len(duplicates) == 0 and
        len(determinism_failures) == 0 and
        len(invalid_format) == 0
    )

    if all_passed:
        print("✓ All verification checks PASSED")
    else:
        print("✗ Some verification checks FAILED")
        print("\nFailures:")
        if entities_without_guid:
            print(f"  - {len(entities_without_guid)} entities missing GUIDs")
        if duplicates:
            print(f"  - {len(duplicates)} duplicate GUIDs")
        if determinism_failures:
            print(f"  - {len(determinism_failures)} determinism failures")
        if invalid_format:
            print(f"  - {len(invalid_format)} invalid GUID formats")

    print("=" * 70)


if __name__ == "__main__":
    main()
