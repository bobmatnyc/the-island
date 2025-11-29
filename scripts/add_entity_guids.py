#!/usr/bin/env python3
"""
Generate and add deterministic UUIDs (GUIDs) to all entities in entity_statistics.json.

This script:
- Generates deterministic UUIDs using uuid.uuid5 based on entity IDs
- Adds 'guid' field to each entity while preserving all existing data
- Creates timestamped backup before modification
- Is idempotent (can run multiple times safely)
- Generates migration report with statistics

Usage:
    python scripts/add_entity_guids.py
"""

import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


# Constants
ENTITY_FILE = Path(__file__).parent.parent / "data" / "metadata" / "entity_statistics.json"
NAMESPACE = uuid.NAMESPACE_DNS  # Use DNS namespace for deterministic generation
BACKUP_DIR = Path(__file__).parent.parent / "data" / "metadata" / "backups"


def create_backup(file_path: Path) -> Path:
    """Create timestamped backup of the entity file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"entity_statistics_before_guids_{timestamp}.json"

    shutil.copy2(file_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    return backup_path


def generate_guid(entity_id: str) -> str:
    """Generate deterministic UUID for entity ID.

    Uses uuid.uuid5 with DNS namespace to ensure same entity ID
    always generates the same GUID.

    Args:
        entity_id: Entity identifier (e.g., "jeffrey_epstein")

    Returns:
        UUID string (e.g., "a3bb189e-8bf9-3888-9912-ace4e6543002")
    """
    return str(uuid.uuid5(NAMESPACE, entity_id))


def add_guids_to_entities(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add GUID field to all entities in statistics.

    Args:
        data: Entity statistics data structure

    Returns:
        Updated data with GUIDs added

    Raises:
        KeyError: If expected data structure is missing
    """
    if "statistics" not in data:
        raise KeyError("Expected 'statistics' key in entity data")

    statistics = data["statistics"]
    updated_count = 0
    skipped_count = 0

    for entity_id, entity_data in statistics.items():
        # Verify entity ID consistency
        if entity_data.get("id") != entity_id:
            print(f"⚠ Warning: Entity key '{entity_id}' doesn't match id field '{entity_data.get('id')}'")

        # Generate GUID
        guid = generate_guid(entity_id)

        # Check if GUID already exists
        if "guid" in entity_data:
            if entity_data["guid"] == guid:
                skipped_count += 1
            else:
                print(f"⚠ Warning: Updating existing GUID for '{entity_id}'")
                entity_data["guid"] = guid
                updated_count += 1
        else:
            entity_data["guid"] = guid
            updated_count += 1

    return data, updated_count, skipped_count


def generate_migration_report(data: Dict[str, Any], output_path: Path) -> None:
    """Generate report showing sample GUIDs and statistics.

    Args:
        data: Entity statistics with GUIDs
        output_path: Path to save report
    """
    statistics = data["statistics"]
    total_entities = len(statistics)

    # Sample entities (first 10 and some notable ones)
    sample_entities = []
    notable_ids = [
        "jeffrey_epstein",
        "ghislaine_maxwell",
        "bill_clinton",
        "donald_trump",
        "prince_andrew"
    ]

    # Get notable entities if they exist
    for entity_id in notable_ids:
        if entity_id in statistics:
            entity = statistics[entity_id]
            sample_entities.append({
                "id": entity_id,
                "guid": entity.get("guid"),
                "name": entity.get("name"),
                "document_count": entity.get("total_documents", 0),
                "connection_count": entity.get("connection_count", 0)
            })

    # Add first 10 entities not already included
    count = 0
    for entity_id, entity in statistics.items():
        if entity_id not in notable_ids and count < 10:
            sample_entities.append({
                "id": entity_id,
                "guid": entity.get("guid"),
                "name": entity.get("name"),
                "document_count": entity.get("total_documents", 0),
                "connection_count": entity.get("connection_count", 0)
            })
            count += 1

    report = {
        "migration_timestamp": datetime.now().isoformat(),
        "total_entities_processed": total_entities,
        "guid_generation_method": "uuid.uuid5(NAMESPACE_DNS, entity_id)",
        "namespace": "NAMESPACE_DNS",
        "deterministic": True,
        "sample_entities": sample_entities,
        "statistics": {
            "entities_with_guids": sum(1 for e in statistics.values() if "guid" in e),
            "entities_in_black_book": sum(1 for e in statistics.values() if e.get("in_black_book")),
            "entities_with_documents": sum(1 for e in statistics.values() if e.get("total_documents", 0) > 0),
            "entities_with_connections": sum(1 for e in statistics.values() if e.get("has_connections"))
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✓ Generated migration report: {output_path}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("GUID MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Total entities: {total_entities:,}")
    print(f"Entities with GUIDs: {report['statistics']['entities_with_guids']:,}")
    print(f"\nSample GUIDs:")
    for entity in sample_entities[:5]:
        print(f"  {entity['id']:30s} → {entity['guid']}")
    print("=" * 60)


def main() -> None:
    """Main execution function."""
    print("=" * 60)
    print("Entity GUID Generation Script")
    print("=" * 60)
    print(f"Entity file: {ENTITY_FILE}")
    print()

    # Check file exists
    if not ENTITY_FILE.exists():
        print(f"✗ Error: Entity file not found: {ENTITY_FILE}")
        return

    # Load entity data
    print("Loading entity data...")
    with open(ENTITY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = data.get("total_entities", 0)
    print(f"✓ Loaded {original_count:,} entities")

    # Create backup
    backup_path = create_backup(ENTITY_FILE)

    # Add GUIDs
    print("\nGenerating GUIDs...")
    try:
        updated_data, updated_count, skipped_count = add_guids_to_entities(data)
        print(f"✓ Generated {updated_count:,} new GUIDs")
        if skipped_count > 0:
            print(f"  Skipped {skipped_count:,} entities (already had matching GUID)")
    except Exception as e:
        print(f"✗ Error adding GUIDs: {e}")
        print(f"  Data preserved in backup: {backup_path}")
        raise

    # Update metadata
    updated_data["generated"] = datetime.now().isoformat()

    # Write updated data
    print("\nWriting updated data...")
    with open(ENTITY_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Updated {ENTITY_FILE}")

    # Generate migration report
    report_path = ENTITY_FILE.parent / "entity_guid_migration_report.json"
    generate_migration_report(updated_data, report_path)

    print("\n✓ GUID migration completed successfully!")
    print(f"  Backup: {backup_path}")
    print(f"  Report: {report_path}")


if __name__ == "__main__":
    main()
