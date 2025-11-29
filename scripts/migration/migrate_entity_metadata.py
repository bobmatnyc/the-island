#!/usr/bin/env python3
"""
Entity Metadata Migration Script

Migrates entity metadata files to ID-based schema:
- entity_biographies.json
- entity_name_mappings.json
- entity_tags.json

Usage:
    python migrate_entity_metadata.py [--dry-run] [--backup]

Performance:
    - Expected runtime: <5 seconds
    - Memory usage: <20MB
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path


class EntityMetadataMigrator:
    """Migrate entity metadata files to ID-based schema."""

    def __init__(self, id_mappings: dict[str, str]):
        self.name_to_id = id_mappings
        self.stats = {"biographies_migrated": 0, "tags_migrated": 0, "name_mappings_created": 0}

    def migrate_biographies(self, biographies: dict) -> dict:
        """
        Migrate entity_biographies.json.

        BEFORE:
        {
          "entities": {
            "Epstein, Jeffrey": {...}
          }
        }

        AFTER:
        {
          "entities": {
            "jeffrey_epstein": {
              "id": "jeffrey_epstein",
              "display_name": "Jeffrey Epstein",
              ...
            }
          }
        }
        """
        migrated_entities = {}

        entities = biographies.get("entities", {})
        logging.info(f"Migrating {len(entities)} biographies...")

        for name, bio_data in entities.items():
            if name not in self.name_to_id:
                logging.warning(f"No ID mapping for biography: '{name}'")
                continue

            entity_id = self.name_to_id[name]

            # Add ID and display_name fields
            migrated_bio = {
                "id": entity_id,
                "display_name": bio_data.get("full_name", name),
                **bio_data,
            }

            migrated_entities[entity_id] = migrated_bio
            self.stats["biographies_migrated"] += 1

        logging.info(f"Migrated {self.stats['biographies_migrated']} biographies")

        return {
            **biographies,
            "entities": migrated_entities,
            "migration_info": {"migrated_at": datetime.now().isoformat(), "schema_version": "2.0"},
        }

    def migrate_tags(self, tags_data: dict) -> dict:
        """
        Migrate entity_tags.json.

        BEFORE:
        {
          "entities": {
            "Jeffrey Epstein": {
              "tags": ["Financier"]
            }
          }
        }

        AFTER:
        {
          "entities": {
            "jeffrey_epstein": {
              "id": "jeffrey_epstein",
              "name": "Jeffrey Epstein",
              "tags": ["Financier"]
            }
          }
        }
        """
        migrated_entities = {}

        entities = tags_data.get("entities", {})
        logging.info(f"Migrating {len(entities)} tagged entities...")

        for name, tag_data in entities.items():
            if name not in self.name_to_id:
                logging.warning(f"No ID mapping for tagged entity: '{name}'")
                continue

            entity_id = self.name_to_id[name]

            # Add ID and name fields
            migrated_tag = {"id": entity_id, "name": name, **tag_data}

            migrated_entities[entity_id] = migrated_tag
            self.stats["tags_migrated"] += 1

        logging.info(f"Migrated {self.stats['tags_migrated']} tagged entities")

        return {
            **tags_data,
            "entities": migrated_entities,
            "migration_info": {"migrated_at": datetime.now().isoformat(), "schema_version": "2.0"},
        }

    def migrate_name_mappings(self, mappings: dict) -> dict:
        """
        Migrate entity_name_mappings.json.

        BEFORE:
        {
          "Alan    Alan Dershowitz": "Alan Dershowitz"
        }

        AFTER:
        {
          "name_to_id": {
            "Alan    Alan Dershowitz": "alan_dershowitz",
            "Alan Dershowitz": "alan_dershowitz"
          },
          "id_to_canonical_name": {
            "alan_dershowitz": "Alan Dershowitz"
          }
        }
        """
        name_to_id = {}
        id_to_canonical_name = {}

        logging.info(f"Migrating {len(mappings)} name mappings...")

        for variant_name, canonical_name in mappings.items():
            # Map variant to ID
            if canonical_name in self.name_to_id:
                entity_id = self.name_to_id[canonical_name]
                name_to_id[variant_name] = entity_id
                name_to_id[canonical_name] = entity_id  # Include canonical too

                # Map ID to canonical name
                id_to_canonical_name[entity_id] = canonical_name

                self.stats["name_mappings_created"] += 1
            else:
                logging.warning(f"No ID mapping for canonical name: '{canonical_name}'")

        logging.info(f"Created {self.stats['name_mappings_created']} name mappings")

        return {
            "metadata": {
                "migrated_at": datetime.now().isoformat(),
                "schema_version": "2.0",
                "total_variants": len(name_to_id),
                "unique_entities": len(id_to_canonical_name),
            },
            "name_to_id": name_to_id,
            "id_to_canonical_name": id_to_canonical_name,
        }


def create_backup(filepath: Path) -> Path:
    """Create timestamped backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}.backup_{timestamp}.json"
    shutil.copy2(filepath, backup_path)
    logging.info(f"Created backup: {backup_path}")
    return backup_path


def load_id_mappings(mappings_file: Path) -> dict[str, str]:
    """Load name-to-ID mappings."""
    with open(mappings_file) as f:
        data = json.load(f)
    return data["name_to_id"]


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_dir / "migrate_metadata.log"), logging.StreamHandler()],
    )


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Migrate entity metadata files to ID-based schema")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logging.info("=" * 60)
    logging.info("Entity Metadata Migration - Starting")
    logging.info("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    metadata_dir = project_root / "data" / "metadata"
    migration_dir = project_root / "data" / "migration"

    biographies_file = metadata_dir / "entity_biographies.json"
    tags_file = metadata_dir / "entity_tags.json"
    mappings_file_old = metadata_dir / "entity_name_mappings.json"
    id_mappings_file = migration_dir / "entity_id_mappings.json"

    # Validate ID mappings exist
    if not id_mappings_file.exists():
        logging.error(f"ID mappings not found: {id_mappings_file}")
        logging.error("Run generate_entity_ids.py first")
        return 1

    # Load ID mappings
    name_to_id = load_id_mappings(id_mappings_file)
    migrator = EntityMetadataMigrator(name_to_id)

    backups = []

    try:
        # Migrate biographies
        if biographies_file.exists():
            if not args.no_backup and not args.dry_run:
                backups.append(create_backup(biographies_file))

            with open(biographies_file) as f:
                bio_data = json.load(f)

            migrated_bio = migrator.migrate_biographies(bio_data)

            if not args.dry_run:
                with open(biographies_file, "w") as f:
                    json.dump(migrated_bio, f, indent=2)
                logging.info(f"Migrated: {biographies_file}")

        # Migrate tags
        if tags_file.exists():
            if not args.no_backup and not args.dry_run:
                backups.append(create_backup(tags_file))

            with open(tags_file) as f:
                tags_data = json.load(f)

            migrated_tags = migrator.migrate_tags(tags_data)

            if not args.dry_run:
                with open(tags_file, "w") as f:
                    json.dump(migrated_tags, f, indent=2)
                logging.info(f"Migrated: {tags_file}")

        # Migrate name mappings
        if mappings_file_old.exists():
            if not args.no_backup and not args.dry_run:
                backups.append(create_backup(mappings_file_old))

            with open(mappings_file_old) as f:
                old_mappings = json.load(f)

            migrated_mappings = migrator.migrate_name_mappings(old_mappings)

            if not args.dry_run:
                with open(mappings_file_old, "w") as f:
                    json.dump(migrated_mappings, f, indent=2)
                logging.info(f"Migrated: {mappings_file_old}")

        # Print summary
        print("\n" + "=" * 60)
        print("Entity Metadata Migration - Summary")
        print("=" * 60)
        print(f"Biographies migrated: {migrator.stats['biographies_migrated']}")
        print(f"Tags migrated: {migrator.stats['tags_migrated']}")
        print(f"Name mappings created: {migrator.stats['name_mappings_created']}")

        if backups:
            print(f"\nBackups created: {len(backups)}")
            for backup in backups:
                print(f"  - {backup}")

        if args.dry_run:
            print("\n📋 DRY RUN - No files were modified")
        else:
            print("\n✅ Metadata migration complete")

        print("=" * 60)

        return 0

    except Exception as e:
        logging.error(f"Migration failed: {e}", exc_info=True)
        if backups:
            print("\n⚠️  Backups preserved:")
            for backup in backups:
                print(f"  - {backup}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
