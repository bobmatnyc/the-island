#!/usr/bin/env python3
"""
Fix Biography Name Format Mismatch (v3 - Manual Mapping)

Converts biography keys to match ACTUAL entity names using:
1. Automatic format detection
2. Manual override mappings for special cases

Special Cases Handled:
- "Marcinkova, Nadia" → "Nadia" (goes by first name only in system)
- "Wexner, Les" → "Leslie Wexner" (full first name)
- "Giuffre, Virginia" → "Roberts, Virginia" (maiden name)
- "Richardson, Bill" → "William Richardson" (full first name)
- "Ross, Adriana" → "Mucinska, Adriana" (different last name)

Author: Claude Code
Date: 2025-11-18
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Manual overrides for special cases
BIOGRAPHY_TO_ENTITY_MAPPING = {
    # Names that exist under different formats in entity system
    "Marcinkova, Nadia": "Nadia",  # Goes by first name only
    "Wexner, Les": "Leslie Wexner",  # Full first name
    "Giuffre, Virginia": "Roberts, Virginia",  # Maiden name
    "Richardson, Bill": "William Richardson",  # Full first name
    "Tucker, Chris": None,  # Not in entity system (humanitarian trip passenger)
    "Mitchell, George": None,  # Not in entity system (alleged, no flight logs)
    "Ross, Adriana": "Mucinska, Adriana",  # Different last name
    "Groff, Lesley": None,  # Not in entity system (assistant, limited public data)
}


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


def find_matching_entity_name(bio_name: str, entity_names: set) -> tuple[str, bool, str]:
    """Find the matching entity name for a biography.

    Args:
        bio_name: Biography name (may be in any format)
        entity_names: Set of valid entity names from entity system

    Returns:
        Tuple of (matched_name, found_exact_match, match_method)
    """
    # Check manual mapping first
    if bio_name in BIOGRAPHY_TO_ENTITY_MAPPING:
        mapped_name = BIOGRAPHY_TO_ENTITY_MAPPING[bio_name]
        if mapped_name is None:
            return bio_name, False, "not_in_system"
        if mapped_name in entity_names:
            return mapped_name, True, "manual_mapping"
        return bio_name, False, "manual_mapping_failed"

    # Try exact match
    if bio_name in entity_names:
        return bio_name, True, "exact_match"

    # Try converting "Last, First" to "First Last"
    if ", " in bio_name:
        parts = bio_name.split(", ", 1)
        if len(parts) == 2:
            alt_name = f"{parts[1]} {parts[0]}"
            if alt_name in entity_names:
                return alt_name, True, "reversed_format"

    # Try converting "First Last" to "Last, First"
    parts = bio_name.split()
    if len(parts) == 2:
        alt_name = f"{parts[1]}, {parts[0]}"
        if alt_name in entity_names:
            return alt_name, True, "comma_format"
    elif len(parts) > 2:
        # Try "Last, First Middle"
        alt_name = f"{parts[-1]}, {' '.join(parts[:-1])}"
        if alt_name in entity_names:
            return alt_name, True, "comma_format"

    # No match found
    return bio_name, False, "no_match"


def backup_file(file_path: Path) -> Path:
    """Create timestamped backup of original file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
    shutil.copy2(file_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path


def convert_biography_names_to_entity_format(
    bio_file: Path, entity_index_file: Path
) -> tuple[dict[str, Any], list]:
    """Convert biography keys to match entity names exactly."""
    print("\n=== Biography Name Format Converter (v3 - Final) ===\n")
    print(f"Reading biographies: {bio_file}")
    print(f"Reading entity index: {entity_index_file}")

    # Load entity names
    entity_names = load_entity_names(entity_index_file)
    print(f"Loaded {len(entity_names)} entity names from system")

    # Load biographies
    with open(bio_file, encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities", {})
    original_count = len(entities)
    print(f"Found {original_count} biographies to process")

    # Convert keys
    converted_entities = {}
    conversions = []

    for old_name, bio_data in entities.items():
        new_name, matched, method = find_matching_entity_name(old_name, entity_names)
        converted_entities[new_name] = bio_data

        conversions.append(
            {
                "from": old_name,
                "to": new_name,
                "matched_entity": matched,
                "match_method": method,
                "changed": old_name != new_name,
            }
        )

    # Update data
    data["entities"] = converted_entities

    # Log results
    print("\n=== Conversion Summary ===\n")
    matched_count = sum(1 for c in conversions if c["matched_entity"])
    changed_count = sum(1 for c in conversions if c["changed"])
    not_in_system = sum(1 for c in conversions if c["match_method"] == "not_in_system")

    print(f"Total biographies: {original_count}")
    print(f"Matched to entities: {matched_count}")
    print(f"Not in entity system: {not_in_system}")
    print(f"Names changed: {changed_count}")

    print("\n=== Conversions ===\n")
    for conv in conversions:
        if conv["match_method"] == "not_in_system":
            status = "!"
            note = " (biography only, not in entity system)"
        elif conv["matched_entity"]:
            status = "✓"
            note = f" ({conv['match_method']})" if conv["changed"] else ""
        else:
            status = "✗"
            note = " (ERROR: no match found)"

        if conv["changed"]:
            print(f"  {status} {conv['from']:<30} → {conv['to']}{note}")
        else:
            print(f"  {status} {conv['from']:<30}{note}")

    # Show not-in-system biographies
    not_in_system_list = [c for c in conversions if c["match_method"] == "not_in_system"]
    if not_in_system_list:
        print(f"\n=== ℹ️  Biographies Not in Entity System ({len(not_in_system_list)}) ===\n")
        print("These are legitimate biographies without corresponding entity entries:")
        for c in not_in_system_list:
            print(f"  ! {c['to']}")

    # Validation
    assert (
        len(converted_entities) == original_count
    ), f"Data loss! Original: {original_count}, Converted: {len(converted_entities)}"

    print(f"\n✓ Validation passed: All {original_count} biographies preserved")

    return data, conversions


def main():
    """Main execution."""
    project_root = Path("/Users/masa/Projects/epstein")
    bio_file = project_root / "data/metadata/entity_biographies.json"
    entity_index_file = project_root / "data/md/entities/ENTITIES_INDEX.json"

    if not bio_file.exists():
        print(f"❌ Biography file not found: {bio_file}")
        return 1

    if not entity_index_file.exists():
        print(f"❌ Entity index not found: {entity_index_file}")
        return 1

    try:
        backup_path = backup_file(bio_file)
        converted_data, conversions = convert_biography_names_to_entity_format(
            bio_file, entity_index_file
        )

        # Write converted data
        with open(bio_file, "w", encoding="utf-8") as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Biography file updated: {bio_file}")

        # Write log
        log_file = bio_file.parent / "biography_name_conversion_log_final.json"
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
                        "not_in_system": sum(
                            1 for c in conversions if c["match_method"] == "not_in_system"
                        ),
                        "names_changed": sum(1 for c in conversions if c["changed"]),
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"✓ Conversion log: {log_file}")

        matched = sum(1 for c in conversions if c["matched_entity"])
        not_in_system = sum(1 for c in conversions if c["match_method"] == "not_in_system")

        print("\n=== ✓ SUCCESS ===")
        print(f"Biographies matched to entities: {matched}/{len(conversions)}")
        print(f"Biographies without entities: {not_in_system} (expected)")
        print("Biography keys now match entity system format!")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
