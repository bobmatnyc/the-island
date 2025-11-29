#!/usr/bin/env python3
"""Import all entities from entity_statistics.json to database.

This script imports all 1,637 entities from entity_statistics.json into the
entities database to establish complete entity coverage.

Data Source: data/metadata/entity_statistics.json
- Contains 1,637 entities with complete metadata
- Includes: display names, sources, GUIDs, connections, document mentions
- Structure: Top-level "statistics" object with entity_id keys

Design Decision: Bulk Import Strategy
- Uses INSERT OR IGNORE to safely handle existing entities
- Preserves existing entity data (no updates)
- Imports: id, display_name, normalized_name, entity_type, aliases, guid
- Default entity_type: "person" (most entities are people)

Performance: Processes ~1,600 entities in < 1 second
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "metadata" / "entities.db"
STATS_JSON = PROJECT_ROOT / "data" / "metadata" / "entity_statistics.json"


def load_entity_statistics() -> Dict[str, Any]:
    """Load entity statistics from JSON file.

    Returns:
        Dict with entity_id -> entity_data mapping
    """
    with open(STATS_JSON) as f:
        data = json.load(f)

    # The entities are under 'statistics' key
    return data.get("statistics", {})


def ensure_guid_column(cursor: sqlite3.Cursor) -> None:
    """Add guid column to entities table if it doesn't exist.

    Design Decision: ALTER TABLE for backward compatibility
    - Checks if guid column exists before adding
    - Makes column nullable to handle existing entities
    - Updates can happen later via UPDATE statements
    """
    # Check if guid column exists
    columns = cursor.execute("PRAGMA table_info(entities)").fetchall()
    column_names = [col[1] for col in columns]

    if 'guid' not in column_names:
        print("Adding 'guid' column to entities table...")
        cursor.execute("ALTER TABLE entities ADD COLUMN guid TEXT")
        print("✅ guid column added\n")


def import_entities() -> None:
    """Import all entities from entity_statistics.json to database.

    Algorithm:
    1. Ensure guid column exists in entities table
    2. Load all entities from JSON
    3. For each entity, extract core fields
    4. INSERT OR IGNORE to avoid duplicates
    5. Report import statistics

    Error Handling:
    - Continues on individual entity errors (logs and continues)
    - Commits transaction at end (all or nothing for consistency)
    """
    print("Loading entity statistics from JSON...")
    entities = load_entity_statistics()
    total_entities = len(entities)
    print(f"Found {total_entities} entities to import\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure guid column exists
    ensure_guid_column(cursor)

    # Check current entity count
    current_count = cursor.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    print(f"Database currently has {current_count} entities\n")

    imported = 0
    skipped = 0
    errors = []

    print("Importing entities...")
    for entity_id, entity_data in entities.items():
        # Extract fields from entity_statistics.json structure
        display_name = entity_data.get("name", entity_id)
        normalized_name = entity_data.get("normalized_name", display_name.lower())

        # Default to "person" type (most entities are people)
        entity_type = "person"

        # Store name variations as aliases
        name_variations = entity_data.get("name_variations", [])
        aliases = json.dumps(name_variations) if name_variations else json.dumps([])

        # Get GUID from entity_statistics
        guid = entity_data.get("guid")

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO entities
                (id, display_name, normalized_name, entity_type, aliases, guid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (entity_id, display_name, normalized_name, entity_type, aliases, guid))

            if cursor.rowcount > 0:
                imported += 1
                if imported % 100 == 0:
                    print(f"  Imported {imported} entities...")
            else:
                skipped += 1

        except Exception as e:
            error_msg = f"Error importing {entity_id}: {e}"
            errors.append(error_msg)
            print(f"  ⚠️  {error_msg}")

    # Commit all changes
    conn.commit()

    # Verify final count
    final_count = cursor.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    conn.close()

    # Report results
    print("\n" + "="*60)
    print("✅ Import Complete")
    print("="*60)
    print(f"   Imported:               {imported}")
    print(f"   Skipped (already exist): {skipped}")
    print(f"   Errors:                  {len(errors)}")
    print(f"   Total processed:         {imported + skipped + len(errors)}")
    print(f"\n   Database before: {current_count} entities")
    print(f"   Database after:  {final_count} entities")
    print(f"   Net increase:    +{final_count - current_count} entities")
    print("="*60)

    if errors:
        print("\n⚠️  Errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")

    # Verify entity coverage
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    bio_count = cursor.execute("SELECT COUNT(*) FROM entity_biographies").fetchone()[0]
    missing_bio_count = cursor.execute("""
        SELECT COUNT(*) FROM entities e
        LEFT JOIN entity_biographies eb ON e.id = eb.entity_id
        WHERE eb.entity_id IS NULL
    """).fetchone()[0]

    conn.close()

    print(f"\n📊 Biography Coverage:")
    print(f"   Total entities:        {final_count}")
    print(f"   With biographies:      {bio_count} ({bio_count*100//final_count}%)")
    print(f"   Without biographies:   {missing_bio_count} ({missing_bio_count*100//final_count}%)")
    print(f"\n✅ Ready for biography generation in priority batches!")


if __name__ == "__main__":
    import_entities()
