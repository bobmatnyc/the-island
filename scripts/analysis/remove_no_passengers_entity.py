#!/usr/bin/env python3
"""
Remove Invalid Entity: "No Passengers"

This script removes the invalid entity "No Passengers" from all data files.
This entry represents flights with no passengers, not an actual entity.

Files modified:
1. data/md/entities/ENTITIES_INDEX.json
2. data/metadata/entity_network.json
3. data/md/entities/flight_logs_by_flight.json
4. data/metadata/semantic_index.json (if exists)

Creates backups before modification.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Base directory
BASE_DIR = Path("/Users/masa/Projects/Epstein")

# Files to update
FILES_TO_UPDATE = {
    "entities_index": BASE_DIR / "data/md/entities/ENTITIES_INDEX.json",
    "entity_network": BASE_DIR / "data/metadata/entity_network.json",
    "flight_logs": BASE_DIR / "data/md/entities/flight_logs_by_flight.json",
    "semantic_index": BASE_DIR / "data/metadata/semantic_index.json"
}

# Entity to remove (case variations)
INVALID_ENTITIES = ["No Passengers", "no passengers", "No passengers", "NO PASSENGERS"]

# Statistics
stats = {
    "files_updated": 0,
    "entities_removed": 0,
    "flights_updated": 0,
    "network_nodes_removed": 0,
    "network_edges_removed": 0
}


def create_backup(file_path):
    """Create timestamped backup of file"""
    if not file_path.exists():
        print(f"⚠️  File does not exist: {file_path}")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path.name}")
    return True


def remove_from_entities_index(file_path):
    """Remove entity from ENTITIES_INDEX.json"""
    print(f"\n📄 Processing: {file_path.name}")

    if not file_path.exists():
        print(f"⚠️  File not found, skipping")
        return

    create_backup(file_path)

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Remove from entities list
    if "entities" in data:
        original_count = len(data["entities"])
        data["entities"] = [
            e for e in data["entities"]
            if e.get("name") not in INVALID_ENTITIES
        ]
        removed = original_count - len(data["entities"])

        if removed > 0:
            stats["entities_removed"] += removed
            print(f"  ✓ Removed {removed} entity/entities from entities list")

            # Update total count
            data["total_entities"] = len(data["entities"])
            print(f"  ✓ Updated total_entities: {data['total_entities']}")

    # Remove from top_frequent_flyers if present
    if "top_frequent_flyers" in data:
        original_count = len(data["top_frequent_flyers"])
        data["top_frequent_flyers"] = [
            e for e in data["top_frequent_flyers"]
            if e.get("name") not in INVALID_ENTITIES
        ]
        removed = original_count - len(data["top_frequent_flyers"])
        if removed > 0:
            print(f"  ✓ Removed {removed} entry/entries from top_frequent_flyers")

    # Update statistics
    data["statistics"]["normalization_date"] = datetime.now().isoformat()

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    stats["files_updated"] += 1
    print(f"  ✅ Updated: {file_path.name}")


def remove_from_entity_network(file_path):
    """Remove entity from entity_network.json"""
    print(f"\n📄 Processing: {file_path.name}")

    if not file_path.exists():
        print(f"⚠️  File not found, skipping")
        return

    create_backup(file_path)

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Remove from nodes
    if "nodes" in data:
        original_count = len(data["nodes"])
        data["nodes"] = [
            n for n in data["nodes"]
            if n.get("id") not in INVALID_ENTITIES
        ]
        removed = original_count - len(data["nodes"])

        if removed > 0:
            stats["network_nodes_removed"] += removed
            print(f"  ✓ Removed {removed} node(s) from network")

    # Remove from edges (any edge involving the invalid entity)
    if "edges" in data:
        original_count = len(data["edges"])
        data["edges"] = [
            e for e in data["edges"]
            if (e.get("source") not in INVALID_ENTITIES and
                e.get("target") not in INVALID_ENTITIES)
        ]
        removed = original_count - len(data["edges"])

        if removed > 0:
            stats["network_edges_removed"] += removed
            print(f"  ✓ Removed {removed} edge(s) from network")

    # Update metadata
    if "metadata" in data:
        data["metadata"]["total_nodes"] = len(data["nodes"])
        data["metadata"]["total_edges"] = len(data["edges"])
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        print(f"  ✓ Updated metadata: {len(data['nodes'])} nodes, {len(data['edges'])} edges")

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    stats["files_updated"] += 1
    print(f"  ✅ Updated: {file_path.name}")


def remove_from_flight_logs(file_path):
    """Remove entity from flight_logs_by_flight.json"""
    print(f"\n📄 Processing: {file_path.name}")

    if not file_path.exists():
        print(f"⚠️  File not found, skipping")
        return

    create_backup(file_path)

    with open(file_path, 'r') as f:
        data = json.load(f)

    flights_modified = 0
    passengers_removed = 0

    # Process each flight
    if "flights" in data:
        for flight in data["flights"]:
            if "passengers" in flight:
                original_count = len(flight["passengers"])
                flight["passengers"] = [
                    p for p in flight["passengers"]
                    if p not in INVALID_ENTITIES
                ]

                if len(flight["passengers"]) < original_count:
                    flights_modified += 1
                    passengers_removed += original_count - len(flight["passengers"])

    if flights_modified > 0:
        stats["flights_updated"] += flights_modified
        print(f"  ✓ Updated {flights_modified} flight(s)")
        print(f"  ✓ Removed {passengers_removed} passenger reference(s)")
    else:
        print(f"  ℹ️  No passenger references found")

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    stats["files_updated"] += 1
    print(f"  ✅ Updated: {file_path.name}")


def remove_from_semantic_index(file_path):
    """Remove entity from semantic_index.json"""
    print(f"\n📄 Processing: {file_path.name}")

    if not file_path.exists():
        print(f"⚠️  File not found, skipping")
        return

    create_backup(file_path)

    with open(file_path, 'r') as f:
        data = json.load(f)

    removed_count = 0

    # Remove from entity_mentions
    if "entity_mentions" in data:
        original_count = len(data["entity_mentions"])
        # Remove any mention of the invalid entity
        data["entity_mentions"] = {
            entity: mentions
            for entity, mentions in data["entity_mentions"].items()
            if entity not in INVALID_ENTITIES
        }
        removed_count = original_count - len(data["entity_mentions"])

        if removed_count > 0:
            print(f"  ✓ Removed {removed_count} entity/entities from entity_mentions")

    # Update metadata
    if "metadata" in data:
        data["metadata"]["total_entities"] = len(data.get("entity_mentions", {}))
        data["metadata"]["last_updated"] = datetime.now().isoformat()

    # Save updated file
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

    if removed_count > 0:
        stats["files_updated"] += 1
        print(f"  ✅ Updated: {file_path.name}")
    else:
        print(f"  ℹ️  No changes needed")


def print_summary():
    """Print summary of changes"""
    print("\n" + "="*60)
    print("SUMMARY - Invalid Entity Removal")
    print("="*60)
    print(f"Entity removed: 'No Passengers'")
    print(f"\nFiles updated: {stats['files_updated']}")
    print(f"  - Entities removed: {stats['entities_removed']}")
    print(f"  - Network nodes removed: {stats['network_nodes_removed']}")
    print(f"  - Network edges removed: {stats['network_edges_removed']}")
    print(f"  - Flights updated: {stats['flights_updated']}")
    print("\n✅ All changes complete!")
    print("\nBackups created with timestamp suffix: .backup_YYYYMMDD_HHMMSS.json")
    print("To restore: copy backup file back to original name")


def main():
    """Main execution"""
    print("="*60)
    print("Remove Invalid Entity: 'No Passengers'")
    print("="*60)
    print("\nThis script will:")
    print("  1. Create backups of all files")
    print("  2. Remove 'No Passengers' from all entity data")
    print("  3. Update entity counts and statistics")
    print("\nProcessing...\n")

    # Process each file
    remove_from_entities_index(FILES_TO_UPDATE["entities_index"])
    remove_from_entity_network(FILES_TO_UPDATE["entity_network"])
    remove_from_flight_logs(FILES_TO_UPDATE["flight_logs"])
    remove_from_semantic_index(FILES_TO_UPDATE["semantic_index"])

    # Print summary
    print_summary()


if __name__ == "__main__":
    main()
