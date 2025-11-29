#!/usr/bin/env python3
"""
Fix Biography Name Format Mismatch (v2 - Entity-Aware)

Converts biography keys to match ACTUAL entity names in the system.
Uses entity index as source of truth for name formats.

Root Cause:
- Entity system is inconsistent:
  * Some use "Last, First": Maxwell, Ghislaine
  * Some use "First Last": William Clinton, Prince Andrew
- Biographies were blindly converted to "Last, First"
- Need to match actual entity names exactly

Solution:
Map each biography to its corresponding entity name (exact match).

Author: Claude Code
Date: 2025-11-18
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


def load_entity_names(entity_index_path: Path) -> set:
    """Load all entity names from ENTITIES_INDEX.json.

    Args:
        entity_index_path: Path to ENTITIES_INDEX.json

    Returns:
        Set of entity names (exact format from entity system)
    """
    with open(entity_index_path, encoding="utf-8") as f:
        index = json.load(f)

    entities = index.get("entities", [])
    return {e.get("name") for e in entities if e.get("name")}


def find_matching_entity_name(bio_name: str, entity_names: set) -> Tuple[str, bool]:
    """Find the matching entity name for a biography.

    Tries multiple formats to find exact match.

    Args:
        bio_name: Biography name (may be in any format)
        entity_names: Set of valid entity names from entity system

    Returns:
        Tuple of (matched_name, found_exact_match)
    """
    # Try exact match first
    if bio_name in entity_names:
        return bio_name, True

    # Try converting "Last, First" to "First Last"
    if ", " in bio_name:
        parts = bio_name.split(", ", 1)
        if len(parts) == 2:
            alt_name = f"{parts[1]} {parts[0]}"
            if alt_name in entity_names:
                return alt_name, True

    # Try converting "First Last" to "Last, First"
    parts = bio_name.split()
    if len(parts) == 2:
        alt_name = f"{parts[1]}, {parts[0]}"
        if alt_name in entity_names:
            return alt_name, True
    elif len(parts) > 2:
        # Try "Last, First Middle"
        alt_name = f"{parts[-1]}, {' '.join(parts[:-1])}"
        if alt_name in entity_names:
            return alt_name, True

    # No match found, return original
    return bio_name, False


def backup_file(file_path: Path) -> Path:
    """Create timestamped backup of original file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
    shutil.copy2(file_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path


def convert_biography_names_to_entity_format(
    bio_file: Path, entity_index_file: Path
) -> Tuple[Dict[str, Any], list]:
    """Convert biography keys to match entity names exactly.

    Args:
        bio_file: Path to entity_biographies.json
        entity_index_file: Path to ENTITIES_INDEX.json

    Returns:
        Tuple of (converted_data, conversion_log)
    """
    print("\n=== Biography Name Format Converter (v2) ===\n")
    print(f"Reading biographies: {bio_file}")
    print(f"Reading entity index: {entity_index_file}")

    # Load entity names (source of truth)
    entity_names = load_entity_names(entity_index_file)
    print(f"Loaded {len(entity_names)} entity names from system")

    # Load biographies
    with open(bio_file, encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities", {})
    original_count = len(entities)
    print(f"Found {original_count} biographies to process")

    # Convert keys to match entity names
    converted_entities = {}
    conversions = []

    for old_name, bio_data in entities.items():
        new_name, matched = find_matching_entity_name(old_name, entity_names)
        converted_entities[new_name] = bio_data

        conversions.append(
            {
                "from": old_name,
                "to": new_name,
                "matched_entity": matched,
                "changed": old_name != new_name,
            }
        )

    # Update data with converted entities
    data["entities"] = converted_entities

    # Log conversions
    print("\n=== Conversion Summary ===\n")
    matched_count = sum(1 for c in conversions if c["matched_entity"])
    changed_count = sum(1 for c in conversions if c["changed"])

    print(f"Total biographies: {original_count}")
    print(f"Matched to entities: {matched_count}")
    print(f"Not found in system: {original_count - matched_count}")
    print(f"Names changed: {changed_count}")

    print("\n=== Conversions ===\n")
    for conv in conversions:
        status = "✓" if conv["matched_entity"] else "!"
        if conv["changed"]:
            print(f"  {status} {conv['from']:<30} → {conv['to']}")
        else:
            print(f"  {status} {conv['from']:<30} (unchanged)")

    # Show unmatched
    unmatched = [c for c in conversions if not c["matched_entity"]]
    if unmatched:
        print(f"\n=== ⚠️  Unmatched Biographies ({len(unmatched)}) ===\n")
        print("These biographies don't have matching entities in the system:")
        for c in unmatched:
            print(f"  ! {c['to']}")

    # Validation
    assert (
        len(converted_entities) == original_count
    ), f"Data loss detected! Original: {original_count}, Converted: {len(converted_entities)}"

    print(f"\n✓ Validation passed: All {original_count} biographies preserved")

    return data, conversions


def main():
    """Main execution function."""
    # Paths
    project_root = Path("/Users/masa/Projects/epstein")
    bio_file = project_root / "data/metadata/entity_biographies.json"
    entity_index_file = project_root / "data/md/entities/ENTITIES_INDEX.json"

    # Check files exist
    if not bio_file.exists():
        print(f"❌ Error: Biography file not found: {bio_file}")
        return 1

    if not entity_index_file.exists():
        print(f"❌ Error: Entity index not found: {entity_index_file}")
        return 1

    try:
        # Create backup
        backup_path = backup_file(bio_file)

        # Convert names
        converted_data, conversions = convert_biography_names_to_entity_format(
            bio_file, entity_index_file
        )

        # Write converted data
        with open(bio_file, "w", encoding="utf-8") as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Biography file updated: {bio_file}")

        # Write conversion log
        log_file = bio_file.parent / "biography_name_conversion_log_v2.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "original_file": str(bio_file),
                    "backup_file": str(backup_path),
                    "entity_index_file": str(entity_index_file),
                    "conversions": conversions,
                    "summary": {
                        "total_biographies": len(conversions),
                        "matched_to_entities": sum(1 for c in conversions if c["matched_entity"]),
                        "unmatched": sum(1 for c in conversions if not c["matched_entity"]),
                        "names_changed": sum(1 for c in conversions if c["changed"]),
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"✓ Conversion log saved: {log_file}")

        matched_count = sum(1 for c in conversions if c["matched_entity"])
        if matched_count == len(conversions):
            print("\n=== ✓ SUCCESS ===")
            print(f"All {matched_count} biographies matched to entity names!")
        else:
            print("\n=== ⚠️  PARTIAL SUCCESS ===")
            print(f"{matched_count}/{len(conversions)} biographies matched to entities")
            print("Check log for unmatched biographies")

        return 0

    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
