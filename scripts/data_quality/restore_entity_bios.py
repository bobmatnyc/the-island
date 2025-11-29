#!/usr/bin/env python3
"""
Task 1: Restore Entity Bios from Backup

Restores bio fields from backup to current ENTITIES_INDEX.json while preserving
all other current data.
"""

import json
from datetime import datetime
from pathlib import Path


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CURRENT_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
BACKUP_INDEX = PROJECT_ROOT / "data/md/entities/backup_20251117_135528/ENTITIES_INDEX.json"
REPORT_FILE = PROJECT_ROOT / "data/metadata/bio_restoration_report.txt"


def load_json(filepath):
    """Load JSON file"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    """Save JSON file with formatting"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def restore_bios():
    """Restore bios from backup"""
    print("Loading current ENTITIES_INDEX.json...")
    current_data = load_json(CURRENT_INDEX)

    print("Loading backup ENTITIES_INDEX.json...")
    backup_data = load_json(BACKUP_INDEX)

    # Extract entities arrays
    current_entities = current_data.get("entities", [])
    backup_entities = backup_data.get("entities", [])

    # Create backup index by name for fast lookup
    backup_index = {}
    for entity in backup_entities:
        name = entity.get("name")
        if name:
            backup_index[name] = entity

    # Track statistics
    stats = {
        "total_entities": len(current_entities),
        "had_bio": 0,
        "missing_bio": 0,
        "restored_from_backup": 0,
        "not_in_backup": 0,
        "backup_had_no_bio": 0,
    }

    restored_entities = []

    # Process each entity
    for entity in current_entities:
        name = entity.get("name")
        current_bio = entity.get("bio", "").strip()

        if current_bio:
            stats["had_bio"] += 1
        else:
            stats["missing_bio"] += 1

            # Try to restore from backup
            if name in backup_index:
                backup_bio = backup_index[name].get("bio", "").strip()
                if backup_bio:
                    entity["bio"] = backup_bio
                    stats["restored_from_backup"] += 1
                    restored_entities.append({"name": name, "bio_length": len(backup_bio)})
                else:
                    stats["backup_had_no_bio"] += 1
            else:
                stats["not_in_backup"] += 1

    # Update the entities in the current data structure
    current_data["entities"] = current_entities

    # Save updated data
    print("\nSaving updated ENTITIES_INDEX.json...")
    save_json(CURRENT_INDEX, current_data)

    # Generate report
    report_lines = [
        "=" * 80,
        "ENTITY BIO RESTORATION REPORT",
        "=" * 80,
        f"Generated: {datetime.now().isoformat()}",
        "",
        "SUMMARY",
        "-" * 80,
        f"Total entities: {stats['total_entities']}",
        f"Entities with bios (before): {stats['had_bio']}",
        f"Entities missing bios: {stats['missing_bio']}",
        "",
        "RESTORATION RESULTS",
        "-" * 80,
        f"✓ Bios restored from backup: {stats['restored_from_backup']}",
        f"✗ Not found in backup: {stats['not_in_backup']}",
        f"✗ Backup had no bio: {stats['backup_had_no_bio']}",
        "",
        f"Final bio coverage: {stats['had_bio'] + stats['restored_from_backup']}/{stats['total_entities']} "
        f"({100 * (stats['had_bio'] + stats['restored_from_backup']) / stats['total_entities']:.1f}%)",
        "",
    ]

    if restored_entities:
        report_lines.extend(
            [
                "RESTORED ENTITIES (showing first 50)",
                "-" * 80,
            ]
        )
        for i, entity in enumerate(restored_entities[:50], 1):
            report_lines.append(f"{i}. {entity['name']} (bio length: {entity['bio_length']} chars)")

        if len(restored_entities) > 50:
            report_lines.append(f"\n... and {len(restored_entities) - 50} more")

    report_lines.append("\n" + "=" * 80)

    report_text = "\n".join(report_lines)

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Print report
    print(report_text)
    print(f"\nReport saved to: {REPORT_FILE}")

    return stats


if __name__ == "__main__":
    restore_bios()
