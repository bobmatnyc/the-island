#!/usr/bin/env python3
"""Export entities without biographies for batch generation."""

import sqlite3
import json
from pathlib import Path

def export_missing_entities():
    """Export entities missing biographies to JSON format."""

    # Connect to database
    db_path = Path(__file__).parent.parent.parent / "data/metadata/entities.db"
    conn = sqlite3.connect(str(db_path))

    # Query entities without biographies
    cursor = conn.execute("""
        SELECT id, display_name, entity_type
        FROM v_entities_missing_bio
        ORDER BY display_name
    """)

    missing = []
    entities_dict = {}

    for row in cursor.fetchall():
        entity_id, display_name, entity_type = row
        missing.append({
            "id": entity_id,
            "display_name": display_name,
            "entity_type": entity_type
        })
        entities_dict[entity_id] = {
            "display_name": display_name,
            "entity_type": entity_type
        }

    conn.close()

    # Save to JSON file (format expected by generation script)
    output_path = Path(__file__).parent.parent.parent / "data/metadata/entities_missing_bios.json"
    output_data = {
        "entities": entities_dict,
        "metadata": {
            "total_count": len(missing),
            "exported_at": "2025-11-25"
        }
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Exported {len(missing)} entities without biographies")
    print(f"✓ Output: {output_path}")

    # Print first 10 for verification
    print("\nFirst 10 entities to be processed:")
    for i, entity in enumerate(missing[:10], 1):
        print(f"  {i}. {entity['display_name']} ({entity['entity_type']}) - ID: {entity['id']}")

    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more")

    return output_path

if __name__ == "__main__":
    export_missing_entities()
