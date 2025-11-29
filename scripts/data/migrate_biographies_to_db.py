#!/usr/bin/env python3
"""
Migrate entity biographies from JSON to SQLite database.

This script:
1. Creates the SQLite database with schema
2. Imports entities from entity_biographies.json
3. Imports biographical data
4. Imports document links from entity_statistics.json
5. Creates enrichment log entries
6. Validates migration completeness

Usage:
    python3 scripts/data/migrate_biographies_to_db.py [--dry-run] [--verbose]
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data" / "metadata"
DB_PATH = DATA_DIR / "entities.db"
SCHEMA_PATH = PROJECT_ROOT / "server" / "database" / "schema.sql"

# Source JSON files
BIOGRAPHIES_JSON = DATA_DIR / "entity_biographies.json"
STATISTICS_JSON = DATA_DIR / "entity_statistics.json"


class BiographyMigration:
    """Migrate biographical data from JSON to SQLite."""

    def __init__(self, dry_run: bool = False, verbose: bool = False, source_file: Optional[str] = None):
        self.dry_run = dry_run
        self.verbose = verbose
        self.source_file = Path(source_file) if source_file else BIOGRAPHIES_JSON
        self.conn: Optional[sqlite3.Connection] = None
        self.stats = {
            "entities_created": 0,
            "biographies_created": 0,
            "document_links_created": 0,
            "enrichment_logs_created": 0,
            "errors": []
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = "🔍 [DRY RUN]" if self.dry_run else "✓"
        if level == "ERROR":
            prefix = "❌"
        elif level == "WARN":
            prefix = "⚠️"

        if self.verbose or level in ["ERROR", "WARN"]:
            print(f"{prefix} [{timestamp}] {message}")

    def connect_db(self):
        """Connect to SQLite database."""
        if self.dry_run:
            self.log("Would create database at: {DB_PATH}")
            return

        # Create database directory if needed
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Connect to database
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self.log(f"Connected to database: {DB_PATH}")

    def create_schema(self):
        """Create database schema from SQL file."""
        if self.dry_run:
            self.log(f"Would execute schema from: {SCHEMA_PATH}")
            return

        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        self.conn.executescript(schema_sql)
        self.conn.commit()
        self.log("Database schema created successfully")

    def load_biographies_json(self) -> Dict[str, Any]:
        """Load entity_biographies.json."""
        if not self.source_file.exists():
            raise FileNotFoundError(f"Biographies file not found: {self.source_file}")

        with open(self.source_file, 'r') as f:
            data = json.load(f)

        self.log(f"Loaded {len(data.get('entities', {}))} entities from {self.source_file.name}")
        return data

    def load_statistics_json(self) -> Dict[str, Any]:
        """Load entity_statistics.json for document links."""
        if not STATISTICS_JSON.exists():
            self.log("Statistics file not found, skipping document links", "WARN")
            return {"entities": {}}

        with open(STATISTICS_JSON, 'r') as f:
            data = json.load(f)

        self.log(f"Loaded statistics for {len(data.get('entities', {}))} entities")
        return data

    def migrate_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """Migrate a single entity and its biography."""
        try:
            # Extract entity fields
            display_name = entity_data.get("display_name", entity_id)
            normalized_name = entity_data.get("normalized_name")
            entity_type = entity_data.get("type", "person")
            aliases = json.dumps(entity_data.get("aliases", []))

            if self.dry_run:
                self.log(f"Would create entity: {display_name} ({entity_id})")
            else:
                # Insert entity
                self.conn.execute("""
                    INSERT OR REPLACE INTO entities (id, display_name, normalized_name, entity_type, aliases)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity_id, display_name, normalized_name, entity_type, aliases))
                self.stats["entities_created"] += 1

            # Migrate biography if present (check both "summary" and "biography" fields)
            if entity_data.get("summary") or entity_data.get("biography"):
                self.migrate_biography(entity_id, entity_data)

        except Exception as e:
            error_msg = f"Error migrating entity {entity_id}: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append(error_msg)

    def migrate_biography(self, entity_id: str, entity_data: Dict[str, Any]):
        """Migrate biographical data for an entity."""
        try:
            # Handle both "summary" (old format) and "biography" (Grok format)
            summary = entity_data.get("summary") or entity_data.get("biography", "")
            birth_date = entity_data.get("birth_date")
            death_date = entity_data.get("death_date")
            occupation = entity_data.get("occupation")
            nationality = entity_data.get("nationality")

            # Structured data
            key_facts = json.dumps(entity_data.get("key_facts", []))
            timeline = json.dumps(entity_data.get("timeline", []))
            relationships = json.dumps(entity_data.get("relationships", {}))

            # Metadata - handle both formats
            # Grok format: "source_material" list -> join to string
            source_material = entity_data.get("source_material", [])
            if isinstance(source_material, list):
                source = ", ".join(source_material) if source_material else "unknown"
            else:
                source = entity_data.get("source", "unknown")

            # Grok format: "generated_by" vs "model_used"
            model_used = entity_data.get("model_used") or entity_data.get("generated_by")
            quality_score = entity_data.get("quality_score", 0.0)

            # Grok format already has word_count, but validate it
            word_count = entity_data.get("word_count") or (len(summary.split()) if summary else 0)
            has_dates = 1 if birth_date or death_date else 0
            has_statistics = 1 if "statistics" in entity_data else 0

            # Timestamps - handle both formats
            # Grok format: "generation_date" vs "generated_at"
            generated_at = entity_data.get("generated_at") or entity_data.get("generation_date")
            enriched_at = entity_data.get("enriched_at")

            if self.dry_run:
                self.log(f"  Would create biography: {word_count} words, quality={quality_score:.2f}")
            else:
                self.conn.execute("""
                    INSERT OR REPLACE INTO entity_biographies (
                        entity_id, summary, birth_date, death_date, occupation, nationality,
                        key_facts, timeline, relationships,
                        source, model_used, quality_score, word_count, has_dates, has_statistics,
                        generated_at, enriched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id, summary, birth_date, death_date, occupation, nationality,
                    key_facts, timeline, relationships,
                    source, model_used, quality_score, word_count, has_dates, has_statistics,
                    generated_at, enriched_at
                ))
                self.stats["biographies_created"] += 1

                # Create enrichment log entry
                self.create_enrichment_log(entity_id, "migrate", source, {
                    "word_count": word_count,
                    "quality_score": quality_score
                })

        except Exception as e:
            error_msg = f"Error migrating biography for {entity_id}: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append(error_msg)

    def migrate_document_links(self, entity_id: str, stats_data: Dict[str, Any]):
        """Migrate document links from entity_statistics.json."""
        try:
            documents = stats_data.get("documents", [])
            for doc in documents:
                doc_id = doc.get("document_id")
                mention_count = doc.get("mention_count", 0)
                relevance_score = doc.get("relevance_score")

                if self.dry_run:
                    self.log(f"  Would link to document {doc_id} ({mention_count} mentions)")
                else:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO entity_document_links (
                            entity_id, document_id, mention_count, relevance_score
                        ) VALUES (?, ?, ?, ?)
                    """, (entity_id, doc_id, mention_count, relevance_score))
                    self.stats["document_links_created"] += 1

        except Exception as e:
            error_msg = f"Error migrating document links for {entity_id}: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append(error_msg)

    def create_enrichment_log(self, entity_id: str, operation: str, source: str, details: Dict[str, Any]):
        """Create enrichment log entry."""
        try:
            if self.dry_run:
                return

            self.conn.execute("""
                INSERT INTO biography_enrichment_log (entity_id, operation, source, details, success)
                VALUES (?, ?, ?, ?, 1)
            """, (entity_id, operation, source, json.dumps(details)))
            self.stats["enrichment_logs_created"] += 1

        except Exception as e:
            error_msg = f"Error creating enrichment log for {entity_id}: {e}"
            self.log(error_msg, "ERROR")
            self.stats["errors"].append(error_msg)

    def validate_migration(self):
        """Validate migration completeness."""
        if self.dry_run:
            self.log("Skipping validation in dry-run mode")
            return

        cursor = self.conn.cursor()

        # Count entities
        cursor.execute("SELECT COUNT(*) FROM entities")
        entity_count = cursor.fetchone()[0]

        # Count biographies
        cursor.execute("SELECT COUNT(*) FROM entity_biographies")
        bio_count = cursor.fetchone()[0]

        # Count document links
        cursor.execute("SELECT COUNT(*) FROM entity_document_links")
        link_count = cursor.fetchone()[0]

        # Count missing biographies
        cursor.execute("SELECT COUNT(*) FROM v_entities_missing_bio")
        missing_bio_count = cursor.fetchone()[0]

        # Quality statistics
        cursor.execute("""
            SELECT
                source,
                COUNT(*) as count,
                AVG(quality_score) as avg_quality,
                AVG(word_count) as avg_words
            FROM entity_biographies
            GROUP BY source
        """)
        quality_stats = cursor.fetchall()

        self.log("\n" + "="*70)
        self.log("MIGRATION VALIDATION REPORT")
        self.log("="*70)
        self.log(f"Entities migrated:        {entity_count}")
        self.log(f"Biographies migrated:     {bio_count}")
        self.log(f"Document links created:   {link_count}")
        self.log(f"Entities missing bios:    {missing_bio_count}")
        self.log("")
        self.log("Quality Statistics by Source:")
        for row in quality_stats:
            source, count, avg_quality, avg_words = row
            self.log(f"  {source:15s}: {count:3d} bios, quality={avg_quality:.2f}, avg_words={avg_words:.0f}")
        self.log("="*70)

        if self.stats["errors"]:
            self.log(f"\n⚠️  {len(self.stats['errors'])} errors occurred during migration", "WARN")
            for error in self.stats["errors"][:5]:
                self.log(f"  - {error}", "ERROR")
            if len(self.stats["errors"]) > 5:
                self.log(f"  ... and {len(self.stats['errors']) - 5} more", "ERROR")

    def run(self):
        """Execute migration."""
        try:
            self.log("\n" + "="*70)
            self.log("ENTITY BIOGRAPHY MIGRATION")
            self.log("="*70)
            self.log(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
            self.log("")

            # Connect and create schema
            self.connect_db()
            if not self.dry_run:
                self.create_schema()

            # Load source data
            biographies = self.load_biographies_json()
            statistics = self.load_statistics_json()

            # Migrate entities and biographies
            entities_data = biographies.get("entities", {})
            self.log(f"\nMigrating {len(entities_data)} entities...")

            for entity_id, entity_data in entities_data.items():
                self.migrate_entity(entity_id, entity_data)

                # Migrate document links if available
                if entity_id in statistics.get("entities", {}):
                    self.migrate_document_links(entity_id, statistics["entities"][entity_id])

            # Commit changes
            if not self.dry_run:
                self.conn.commit()
                self.log("\nCommitted all changes to database")

            # Validate migration
            self.validate_migration()

            self.log("\n✅ Migration completed successfully!\n")

        except Exception as e:
            self.log(f"Migration failed: {e}", "ERROR")
            if self.conn:
                self.conn.rollback()
            raise

        finally:
            if self.conn:
                self.conn.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate entity biographies to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--source", "-s", type=str, help="Source JSON file (defaults to entity_biographies.json)")
    args = parser.parse_args()

    migration = BiographyMigration(dry_run=args.dry_run, verbose=args.verbose, source_file=args.source)
    migration.run()


if __name__ == "__main__":
    main()
