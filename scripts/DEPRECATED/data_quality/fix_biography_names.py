#!/usr/bin/env python3
"""
Fix Biography Name Format Mismatch

Converts biography keys from "First Last" to "Last, First" format
to match standardized entity name format.

Root Cause:
- Entities use: "Maxwell, Ghislaine" (Last, First format)
- Biographies use: "Ghislaine Maxwell" (First Last format)
- Result: Biography lookups fail due to key mismatch

Solution:
Convert all biography keys to "Last, First" format while preserving all data.

Author: Claude Code
Date: 2025-11-18
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def convert_name_to_last_first(name: str) -> str:
    """Convert 'First Last' to 'Last, First' format.

    Handles:
    - Two-part names: "Ghislaine Maxwell" → "Maxwell, Ghislaine"
    - Single names: "Epstein" → "Epstein" (unchanged)
    - Three+ part names: "William Jefferson Clinton" → "Clinton, William Jefferson"
    - Special cases: "Prince Andrew" → "Andrew, Prince"

    Args:
        name: Original name in "First Last" format

    Returns:
        Name in "Last, First" format
    """
    parts = name.strip().split()

    if len(parts) == 1:
        # Single name, keep as-is (unlikely but handle it)
        return name
    if len(parts) == 2:
        # Standard two-part name
        return f"{parts[1]}, {parts[0]}"
    # Complex names (3+ parts)
    # Strategy: Assume last part is surname, rest is first/middle names
    last_name = parts[-1]
    first_names = " ".join(parts[:-1])
    return f"{last_name}, {first_names}"


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


def convert_biography_names(bio_file: Path) -> Dict[str, Any]:
    """Convert all biography keys from 'First Last' to 'Last, First' format.

    Args:
        bio_file: Path to entity_biographies.json

    Returns:
        Converted biography data with new key format
    """
    print("\n=== Biography Name Format Converter ===\n")
    print(f"Reading: {bio_file}")

    with open(bio_file, encoding="utf-8") as f:
        data = json.load(f)

    # Extract entities dictionary
    entities = data.get("entities", {})
    original_count = len(entities)
    print(f"Found {original_count} biographies to convert")

    # Convert keys
    converted_entities = {}
    conversions = []

    for old_name, bio_data in entities.items():
        new_name = convert_name_to_last_first(old_name)
        converted_entities[new_name] = bio_data

        conversions.append({"from": old_name, "to": new_name, "changed": old_name != new_name})

    # Update data with converted entities
    data["entities"] = converted_entities

    # Log conversions
    print("\n=== Conversion Summary ===\n")
    changed_count = sum(1 for c in conversions if c["changed"])
    print(f"Total biographies: {original_count}")
    print(f"Names converted: {changed_count}")
    print(f"Names unchanged: {original_count - changed_count}")

    print("\n=== Conversions ===\n")
    for conv in conversions:
        if conv["changed"]:
            print(f"  ✓ {conv['from']:<30} → {conv['to']}")
        else:
            print(f"  - {conv['from']:<30} (unchanged)")

    # Validation
    assert (
        len(converted_entities) == original_count
    ), f"Data loss detected! Original: {original_count}, Converted: {len(converted_entities)}"

    print(f"\n✓ Validation passed: All {original_count} biographies preserved")

    return data, conversions


def main():
    """Main execution function."""
    # Paths
    bio_file = Path("/Users/masa/Projects/epstein/data/metadata/entity_biographies.json")

    # Check file exists
    if not bio_file.exists():
        print(f"❌ Error: Biography file not found: {bio_file}")
        return 1

    try:
        # Create backup
        backup_path = backup_file(bio_file)

        # Convert names
        converted_data, conversions = convert_biography_names(bio_file)

        # Write converted data
        with open(bio_file, "w", encoding="utf-8") as f:
            json.dump(converted_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Biography file updated: {bio_file}")

        # Write conversion log
        log_file = bio_file.parent / "biography_name_conversion_log.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "original_file": str(bio_file),
                    "backup_file": str(backup_path),
                    "conversions": conversions,
                    "summary": {
                        "total_biographies": len(conversions),
                        "names_converted": sum(1 for c in conversions if c["changed"]),
                        "names_unchanged": sum(1 for c in conversions if not c["changed"]),
                    },
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"✓ Conversion log saved: {log_file}")

        print("\n=== SUCCESS ===")
        print("Biography names converted to 'Last, First' format")
        print(f"Original backed up to: {backup_path}")
        print("Biographies now match entity name format!")

        return 0

    except Exception as e:
        print(f"\n❌ Error during conversion: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
