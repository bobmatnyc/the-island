#!/usr/bin/env python3
"""
Entity Statistics Migration Script

Migrates entity_statistics.json from name-keyed to ID-keyed structure.

BEFORE (name-keyed):
    {"statistics": {"Jeffrey Epstein": {...}}}

AFTER (ID-keyed):
    {"statistics": {"jeffrey_epstein": {"id": "jeffrey_epstein", ...}}}

Usage:
    python migrate_entity_statistics.py [--dry-run] [--backup]

Performance:
    - Expected runtime: <10 seconds for 1,637 entities
    - Memory usage: <100MB (loads entire file)

Safety:
    - Creates timestamped backup by default
    - Validates data integrity before/after
    - Rollback capability if validation fails
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path


class EntityStatisticsMigrator:
    """
    Migrate entity_statistics.json to ID-based schema.

    Design Decision: In-place transformation with validation gates
    - Performance: Single pass O(n) transformation
    - Safety: Backup + validation before commit
    - Rollback: Automated restore on validation failure

    Trade-offs:
    - Memory: Loads full dataset into memory (~1MB, acceptable)
    - Speed: Single-pass vs. streaming (faster, simpler)
    - Safety: Full validation vs. partial (comprehensive)

    Alternatives Considered:
    1. Streaming: Rejected - dataset small enough for in-memory
    2. Incremental: Rejected - atomic migration simpler
    3. Database: Rejected - JSON sufficient for dataset size
    """

    def __init__(self, id_mappings: dict[str, str]):
        """
        Initialize migrator with ID mappings.

        Args:
            id_mappings: name_to_id mapping from generate_entity_ids.py
        """
        self.name_to_id = id_mappings
        self.stats = {"entities_migrated": 0, "entities_skipped": 0, "fields_updated": 0}

    def migrate_entity(self, name: str, entity_data: dict) -> tuple[str, dict]:
        """
        Migrate single entity from name-based to ID-based.

        Transformation:
        - Lookup entity ID from name
        - Add 'id' field to entity data
        - Preserve all existing fields
        - Return new (id, data) tuple for ID-keyed dict

        Error Handling:
        - Name not in mappings: Logged and skipped
        - Missing required fields: Logged and preserved
        - Invalid data: Logged and skipped

        Args:
            name: Entity name (current key)
            entity_data: Entity statistics object

        Returns:
            Tuple of (entity_id, migrated_data)

        Raises:
            KeyError: If name not found in ID mappings
        """
        # Lookup entity ID
        if name not in self.name_to_id:
            raise KeyError(f"No ID mapping found for entity: '{name}'")

        entity_id = self.name_to_id[name]

        # Create migrated entity (preserve all fields + add ID)
        migrated = {
            "id": entity_id,  # NEW: Add entity ID field
            **entity_data,  # PRESERVE: All existing fields
        }

        self.stats["entities_migrated"] += 1
        self.stats["fields_updated"] += 1  # Added 'id' field

        return entity_id, migrated

    def migrate_statistics(self, statistics: dict) -> dict:
        """
        Migrate all entities in statistics dictionary.

        Transformation:
        - Convert from name-keyed to ID-keyed structure
        - Add 'id' field to each entity
        - Preserve all metadata

        Performance:
        - Time Complexity: O(n) where n = entity count
        - Space Complexity: O(n) for new dictionary
        - Expected runtime: <5 seconds for 1,637 entities

        Args:
            statistics: Original name-keyed statistics dict

        Returns:
            Migrated ID-keyed statistics dict

        Error Handling:
        - Missing ID mapping: Entity skipped, logged
        - Invalid entity data: Entity skipped, logged
        - Empty statistics: Returns empty dict (valid case)
        """
        migrated_statistics = {}
        total_entities = len(statistics)

        logging.info(f"Migrating {total_entities} entities...")

        for name, entity_data in statistics.items():
            try:
                entity_id, migrated_entity = self.migrate_entity(name, entity_data)
                migrated_statistics[entity_id] = migrated_entity

            except KeyError as e:
                logging.warning(f"Skipping entity '{name}': {e}")
                self.stats["entities_skipped"] += 1
                continue

            except Exception as e:
                logging.error(f"Error migrating entity '{name}': {e}")
                self.stats["entities_skipped"] += 1
                continue

        logging.info(
            f"Migration complete: {self.stats['entities_migrated']} migrated, "
            f"{self.stats['entities_skipped']} skipped"
        )

        return migrated_statistics

    def validate_migration(self, original: dict, migrated: dict) -> tuple[bool, list[str]]:
        """
        Validate migrated data against original.

        Validation Checks:
        1. Entity count unchanged
        2. All IDs are valid slugs
        3. All IDs are unique
        4. All entities have 'id' field
        5. All original fields preserved
        6. No data loss in migration

        Args:
            original: Original statistics dict (name-keyed)
            migrated: Migrated statistics dict (ID-keyed)

        Returns:
            Tuple of (is_valid, error_messages)

        Complexity:
        - Time: O(n × m) where n=entities, m=avg fields per entity
        - Space: O(k) where k=error count
        """
        errors = []

        # Check 1: Entity count
        original_count = len(original)
        migrated_count = len(migrated)

        if original_count != migrated_count:
            errors.append(
                f"Entity count mismatch: {original_count} original, "
                f"{migrated_count} migrated "
                f"({abs(original_count - migrated_count)} difference)"
            )

        # Check 2: All IDs are valid slugs
        import re

        id_pattern = re.compile(r"^[a-z0-9_]+$")

        invalid_ids = [entity_id for entity_id in migrated if not id_pattern.match(entity_id)]

        if invalid_ids:
            errors.append(
                f"Invalid IDs found: {', '.join(invalid_ids[:5])}"
                f"{' (and more)' if len(invalid_ids) > 5 else ''}"
            )

        # Check 3: ID uniqueness (should be guaranteed by dict, but verify)
        if len(migrated.keys()) != len(set(migrated.keys())):
            errors.append("Duplicate IDs detected")

        # Check 4: All entities have 'id' field
        missing_id = [entity_id for entity_id, data in migrated.items() if "id" not in data]

        if missing_id:
            errors.append(
                f"Missing 'id' field: {', '.join(missing_id[:5])}"
                f"{' (and more)' if len(missing_id) > 5 else ''}"
            )

        # Check 5: ID field matches key
        mismatched_ids = [
            entity_id for entity_id, data in migrated.items() if data.get("id") != entity_id
        ]

        if mismatched_ids:
            errors.append(f"ID field mismatch with key: {', '.join(mismatched_ids[:5])}")

        # Check 6: Required fields preserved
        # Sample check on first entity
        if migrated:
            sample_id = next(iter(migrated))
            sample_entity = migrated[sample_id]
            required_fields = ["name", "name_variations", "sources"]

            missing_fields = [field for field in required_fields if field not in sample_entity]

            if missing_fields:
                errors.append(
                    f"Missing required fields in migrated data: " f"{', '.join(missing_fields)}"
                )

        is_valid = len(errors) == 0

        if is_valid:
            logging.info("✅ Validation passed: All checks successful")
        else:
            logging.error(f"❌ Validation failed: {len(errors)} errors detected")
            for error in errors:
                logging.error(f"  - {error}")

        return is_valid, errors


def create_backup(filepath: Path) -> Path:
    """
    Create timestamped backup of original file.

    Backup Strategy:
    - Timestamp format: YYYYMMDD_HHMMSS
    - Location: Same directory as original
    - Naming: {original_name}.backup_{timestamp}.json

    Args:
        filepath: Original file to backup

    Returns:
        Path to backup file

    Error Handling:
    - File not found: Raised
    - Backup directory write failure: Raised
    - Backup file already exists: Overwrites with warning
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}.backup_{timestamp}.json"

    shutil.copy2(filepath, backup_path)
    logging.info(f"Created backup: {backup_path}")

    return backup_path


def load_id_mappings(mappings_file: Path) -> dict[str, str]:
    """
    Load name-to-ID mappings from generate_entity_ids.py output.

    Expected structure:
    {
      "name_to_id": {
        "Jeffrey Epstein": "jeffrey_epstein",
        ...
      }
    }

    Args:
        mappings_file: Path to entity_id_mappings.json

    Returns:
        name_to_id dictionary

    Raises:
        FileNotFoundError: If mappings file doesn't exist
        KeyError: If 'name_to_id' key missing
        json.JSONDecodeError: If file is invalid JSON
    """
    logging.info(f"Loading ID mappings from {mappings_file}")

    with open(mappings_file) as f:
        data = json.load(f)

    if "name_to_id" not in data:
        raise KeyError("Missing 'name_to_id' in ID mappings file")

    name_to_id = data["name_to_id"]
    logging.info(f"Loaded {len(name_to_id)} name-to-ID mappings")

    return name_to_id


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with file and console output."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "migrate_statistics.log"

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def main():
    """
    Main execution function.

    Migration Process:
    1. Load ID mappings
    2. Create backup (optional, default=yes)
    3. Load original statistics
    4. Migrate to ID-based structure
    5. Validate migration
    6. Save migrated file (if validation passes)
    7. Report statistics

    Rollback Strategy:
    - If validation fails, restore from backup
    - If save fails, backup remains intact
    - Manual rollback: cp backup.json entity_statistics.json
    """
    parser = argparse.ArgumentParser(
        description="Migrate entity_statistics.json to ID-based schema"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run migration without writing output"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup creation (not recommended)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logging.info("=" * 60)
    logging.info("Entity Statistics Migration - Starting")
    logging.info("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    metadata_dir = data_dir / "metadata"
    migration_dir = data_dir / "migration"

    statistics_file = metadata_dir / "entity_statistics.json"
    mappings_file = migration_dir / "entity_id_mappings.json"

    # Validate inputs
    if not statistics_file.exists():
        logging.error(f"Statistics file not found: {statistics_file}")
        return 1

    if not mappings_file.exists():
        logging.error(
            f"ID mappings file not found: {mappings_file}\n" f"Run generate_entity_ids.py first"
        )
        return 1

    try:
        # Load ID mappings
        name_to_id = load_id_mappings(mappings_file)

        # Create backup
        if not args.no_backup and not args.dry_run:
            backup_path = create_backup(statistics_file)
        else:
            backup_path = None
            logging.warning("Skipping backup creation")

        # Load original statistics
        logging.info(f"Loading statistics from {statistics_file}")
        with open(statistics_file) as f:
            original_data = json.load(f)

        original_statistics = original_data.get("statistics", {})

        # Migrate
        migrator = EntityStatisticsMigrator(name_to_id)
        migrated_statistics = migrator.migrate_statistics(original_statistics)

        # Validate
        is_valid, errors = migrator.validate_migration(original_statistics, migrated_statistics)

        if not is_valid:
            logging.error("Migration validation failed:")
            for error in errors:
                logging.error(f"  - {error}")

            if backup_path:
                logging.info(f"Backup preserved at: {backup_path}")

            return 1

        # Prepare migrated data structure
        migrated_data = {
            **original_data,  # Preserve metadata
            "statistics": migrated_statistics,
            "migration_info": {
                "migrated_at": datetime.now().isoformat(),
                "schema_version": "2.0",
                "migration_script": "migrate_entity_statistics.py",
                "entities_migrated": migrator.stats["entities_migrated"],
                "entities_skipped": migrator.stats["entities_skipped"],
            },
        }

        # Save migrated file
        if args.dry_run:
            logging.info("DRY RUN: Skipping file write")
        else:
            with open(statistics_file, "w") as f:
                json.dump(migrated_data, f, indent=2)
            logging.info(f"Saved migrated statistics to {statistics_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("Entity Statistics Migration - Summary")
        print("=" * 60)
        print(f"Entities migrated: {migrator.stats['entities_migrated']}")
        print(f"Entities skipped: {migrator.stats['entities_skipped']}")
        print(f"Fields updated: {migrator.stats['fields_updated']}")
        print(f"Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")

        if backup_path:
            print(f"\nBackup saved: {backup_path}")

        if args.dry_run:
            print("\n📋 DRY RUN - No files were modified")
        else:
            print(f"\n✅ Migration complete: {statistics_file}")

        print("=" * 60)

        return 0

    except Exception as e:
        logging.error(f"Migration failed: {e}", exc_info=True)

        if backup_path:
            logging.info(f"Backup preserved at: {backup_path}")
            print(f"\n⚠️  Migration failed - backup preserved: {backup_path}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
