#!/usr/bin/env python3
"""
Add UUIDs to Entity Files

Adds deterministic UUIDs to all entities in organization and location files.
Also validates and reports on existing UUIDs in entity_statistics.json.

Design Decision: Non-Destructive Update
Rationale: Always backup originals before modifying. If UUID field already
exists, validate it. If missing or invalid, generate new one. This ensures
script is idempotent (safe to run multiple times).

Performance:
- Processes ~1000 entities/second
- File I/O is bottleneck, not UUID generation
- Memory usage: ~50MB for largest entity files

Usage:
    # Add UUIDs to all entity files
    python3 scripts/add_entity_uuids.py

    # Dry run (preview changes without modifying files)
    python3 scripts/add_entity_uuids.py --dry-run

    # Only process specific files
    python3 scripts/add_entity_uuids.py --files organizations,locations
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from entity_uuid import generate_entity_uuid, validate_uuid

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
METADATA_DIR = DATA_DIR / "metadata"

# Entity files to process
ENTITY_FILES = {
    "statistics": METADATA_DIR / "entity_statistics.json",
    "organizations": METADATA_DIR / "entity_organizations.json",
    "locations": METADATA_DIR / "entity_locations.json",
}


def backup_file(file_path: Path) -> Path:
    """
    Create timestamped backup of file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file

    Example:
        entity_organizations.json →
        entity_organizations_backup_20251206_143052.json
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_name(f"{file_path.stem}_backup_{timestamp}{file_path.suffix}")

    # Copy file
    import shutil
    shutil.copy2(file_path, backup_path)

    print(f"✓ Backed up {file_path.name} to {backup_path.name}")
    return backup_path


def add_uuids_to_statistics(dry_run: bool = False) -> dict:
    """
    Validate and report on UUIDs in entity_statistics.json.

    Note: entity_statistics.json already has 'guid' field with UUIDs.
    This function validates them and reports statistics.

    Args:
        dry_run: If True, only report without modifying

    Returns:
        Statistics dict
    """
    file_path = ENTITY_FILES["statistics"]
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {file_path.name}...")

    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return {}

    # Load data
    with open(file_path) as f:
        data = json.load(f)

    entities = data.get("statistics", {})
    print(f"  Loaded {len(entities)} entities")

    # Statistics
    stats = {
        "total": len(entities),
        "has_guid": 0,
        "has_id": 0,
        "valid_guid": 0,
        "invalid_guid": 0,
        "missing_guid": 0,
        "updated": 0,
    }

    # Check each entity
    for entity_key, entity_data in entities.items():
        # Check for 'guid' field (existing UUID field)
        if "guid" in entity_data:
            stats["has_guid"] += 1

            # Validate GUID
            if validate_uuid(entity_data["guid"]):
                stats["valid_guid"] += 1
            else:
                stats["invalid_guid"] += 1
                print(f"    ⚠️  Invalid GUID for '{entity_key}': {entity_data['guid']}")
        else:
            stats["missing_guid"] += 1

        # Check for 'id' field (snake_case identifier)
        if "id" in entity_data:
            stats["has_id"] += 1

    # Report
    print(f"\n  Statistics Report:")
    print(f"    Total entities:        {stats['total']}")
    print(f"    Has 'guid' field:      {stats['has_guid']} ({stats['has_guid']/stats['total']*100:.1f}%)")
    print(f"    Has 'id' field:        {stats['has_id']} ({stats['has_id']/stats['total']*100:.1f}%)")
    print(f"    Valid GUIDs:           {stats['valid_guid']}")
    print(f"    Invalid GUIDs:         {stats['invalid_guid']}")
    print(f"    Missing GUIDs:         {stats['missing_guid']}")

    if stats['has_guid'] == stats['total'] and stats['invalid_guid'] == 0:
        print(f"  ✓ All entities have valid GUIDs!")
    elif stats['missing_guid'] > 0:
        print(f"  ⚠️  {stats['missing_guid']} entities missing GUIDs")

    return stats


def add_uuids_to_file(file_key: str, dry_run: bool = False) -> dict:
    """
    Add UUIDs to entity file (organizations or locations).

    Adds 'uuid' field to each entity based on name + entity_type.
    Skips entities that already have valid UUID.

    Args:
        file_key: Key in ENTITY_FILES dict ("organizations" or "locations")
        dry_run: If True, preview changes without saving

    Returns:
        Statistics dict with counts
    """
    file_path = ENTITY_FILES[file_key]
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {file_path.name}...")

    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return {}

    # Load data
    with open(file_path) as f:
        data = json.load(f)

    entities = data.get("entities", {})
    metadata = data.get("metadata", {})

    print(f"  Loaded {len(entities)} entities")

    # Statistics
    stats = {
        "total": len(entities),
        "has_uuid": 0,
        "valid_uuid": 0,
        "added_uuid": 0,
        "updated_uuid": 0,
        "missing_name": 0,
        "missing_type": 0,
    }

    # Track conflation (same UUID = conflated entities)
    uuid_to_entities = {}

    # Process each entity
    for entity_key, entity_data in entities.items():
        name = entity_data.get("name", entity_key)
        entity_type = entity_data.get("entity_type")

        # Validate required fields
        if not name:
            stats["missing_name"] += 1
            print(f"    ⚠️  Entity '{entity_key}' missing 'name' field")
            continue

        if not entity_type:
            stats["missing_type"] += 1
            print(f"    ⚠️  Entity '{entity_key}' missing 'entity_type' field")
            continue

        # Check existing UUID
        existing_uuid = entity_data.get("uuid")

        if existing_uuid:
            stats["has_uuid"] += 1

            # Validate existing UUID
            if validate_uuid(existing_uuid):
                stats["valid_uuid"] += 1

                # Track for conflation detection
                if existing_uuid not in uuid_to_entities:
                    uuid_to_entities[existing_uuid] = []
                uuid_to_entities[existing_uuid].append(entity_key)

                continue  # Keep existing valid UUID
            else:
                print(f"    ⚠️  Invalid UUID for '{entity_key}': {existing_uuid}")
                stats["updated_uuid"] += 1
        else:
            stats["added_uuid"] += 1

        # Generate new UUID
        new_uuid = generate_entity_uuid(name, entity_type)

        # Track for conflation detection
        if new_uuid not in uuid_to_entities:
            uuid_to_entities[new_uuid] = []
        uuid_to_entities[new_uuid].append(entity_key)

        # Update entity (if not dry run)
        if not dry_run:
            entity_data["uuid"] = new_uuid

    # Report
    print(f"\n  Processing Report:")
    print(f"    Total entities:        {stats['total']}")
    print(f"    Had UUID:              {stats['has_uuid']}")
    print(f"    Valid existing UUIDs:  {stats['valid_uuid']}")
    print(f"    Added UUIDs:           {stats['added_uuid']}")
    print(f"    Updated UUIDs:         {stats['updated_uuid']}")
    print(f"    Missing name:          {stats['missing_name']}")
    print(f"    Missing entity_type:   {stats['missing_type']}")

    # Check for conflation (same UUID = same name + type)
    conflated = {uuid_val: entities_list for uuid_val, entities_list in uuid_to_entities.items() if len(entities_list) > 1}

    if conflated:
        print(f"\n  ⚠️  Conflation Detected ({len(conflated)} UUIDs with multiple entities):")
        for uuid_val, entities_list in list(conflated.items())[:10]:  # Show first 10
            print(f"    UUID {uuid_val}:")
            for entity_key in entities_list:
                entity_name = entities.get(entity_key, {}).get("name", entity_key)
                print(f"      - {entity_key} ({entity_name})")

    # Save updated data (if not dry run)
    if not dry_run and (stats['added_uuid'] > 0 or stats['updated_uuid'] > 0):
        # Backup original
        backup_file(file_path)

        # Update metadata
        metadata["last_updated"] = datetime.now().isoformat()
        if "uuid_generation_date" not in metadata:
            metadata["uuid_generation_date"] = datetime.now().isoformat()

        # Save
        with open(file_path, 'w') as f:
            json.dump({"metadata": metadata, "entities": entities}, f, indent=2)

        print(f"\n  ✓ Saved updated file with {stats['added_uuid']} new UUIDs")

    return stats


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Add UUIDs to entity files for disambiguation"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--files",
        type=str,
        default="all",
        help="Comma-separated list of files to process (statistics,organizations,locations) or 'all'"
    )

    args = parser.parse_args()

    # Determine which files to process
    if args.files == "all":
        files_to_process = ["statistics", "organizations", "locations"]
    else:
        files_to_process = [f.strip() for f in args.files.split(",")]

    # Validate file keys
    invalid_files = [f for f in files_to_process if f not in ENTITY_FILES]
    if invalid_files:
        print(f"Error: Invalid file keys: {invalid_files}")
        print(f"Valid options: {list(ENTITY_FILES.keys())}")
        sys.exit(1)

    # Print header
    print("=" * 70)
    print("Entity UUID Addition Script")
    print("=" * 70)
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Process files
    all_stats = {}

    for file_key in files_to_process:
        if file_key == "statistics":
            # entity_statistics.json already has GUIDs, just validate
            stats = add_uuids_to_statistics(dry_run=args.dry_run)
        else:
            # Add UUIDs to organizations/locations
            stats = add_uuids_to_file(file_key, dry_run=args.dry_run)

        all_stats[file_key] = stats

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    total_added = sum(s.get("added_uuid", 0) for s in all_stats.values())
    total_updated = sum(s.get("updated_uuid", 0) for s in all_stats.values())

    if args.dry_run:
        print(f"\nDRY RUN: Would add {total_added} UUIDs and update {total_updated} invalid UUIDs")
        print("\nRun without --dry-run to apply changes")
    else:
        if total_added > 0 or total_updated > 0:
            print(f"\n✓ Successfully added {total_added} UUIDs and updated {total_updated} invalid UUIDs")
            print("\nBackup files created with timestamp suffix")
        else:
            print("\n✓ All entities already have valid UUIDs - no changes needed")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
