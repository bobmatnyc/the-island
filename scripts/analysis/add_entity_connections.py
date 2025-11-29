#!/usr/bin/env python3
"""
Add epstein_connection field to entities with biographies.

This script adds explicit connection descriptions to entities that currently
have narrative biographies but are missing the dedicated epstein_connection field.

Approach: Generate connection summaries from flight log data
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


def normalize_date(date_str: str) -> str:
    """
    Normalize date strings to YYYY-MM-DD format for comparison.

    Handles formats like:
    - 9/19/1998
    - 09/19/1998
    - 1998-09-19
    """
    if not date_str or date_str == "Unknown":
        return None

    # Already in YYYY-MM-DD format
    if '-' in date_str and len(date_str) == 10:
        return date_str

    # Handle M/D/YYYY or MM/DD/YYYY
    if '/' in date_str:
        try:
            parts = date_str.split('/')
            month = parts[0].zfill(2)
            day = parts[1].zfill(2)
            year = parts[2]
            return f"{year}-{month}-{day}"
        except (IndexError, ValueError):
            return None

    return None


def generate_connection_from_flights(entity_data: Dict[str, Any]) -> str:
    """
    Generate connection summary from flight log data.

    Args:
        entity_data: Entity dictionary with document_sources field

    Returns:
        Connection description string
    """
    flight_logs = entity_data.get('document_sources', {}).get('flight_logs', {})
    count = flight_logs.get('count', 0)

    # No flight log data
    if count == 0:
        return "Connection to Epstein case documented in public records."

    # Extract dates from flight entries
    entries = flight_logs.get('entries', [])
    dates = []
    for entry in entries:
        date_str = entry.get('date', '')
        normalized = normalize_date(date_str)
        if normalized:
            dates.append(normalized)

    # Generate connection string
    if dates:
        dates.sort()
        min_date = dates[0]
        max_date = dates[-1]

        # Format dates nicely (YYYY only if same year, otherwise full date)
        min_year = min_date.split('-')[0]
        max_year = max_date.split('-')[0]

        if min_year == max_year:
            date_range = f"{min_year}"
        else:
            date_range = f"{min_year}-{max_year}"

        plural = "time" if count == 1 else "times"
        return f"Appeared on Epstein's flight logs {count} {plural} between {date_range}."
    else:
        # Dates not parseable, just use count
        plural = "time" if count == 1 else "times"
        return f"Appeared on Epstein's flight logs {count} {plural}."


def add_connections(dry_run: bool = False) -> None:
    """
    Add epstein_connection field to entities missing it.

    Args:
        dry_run: If True, show what would be changed without modifying files
    """
    bio_file = Path('data/metadata/entity_biographies.json')

    if not bio_file.exists():
        print(f"❌ Error: Biography file not found at {bio_file}")
        return

    # Load entity biographies
    print(f"📖 Loading entity biographies from {bio_file}")
    with open(bio_file) as f:
        data = json.load(f)

    entities = data.get('entities', {})
    total_entities = len(entities)

    print(f"   Found {total_entities} total entities")

    # Count entities by status
    has_connection = 0
    needs_connection = 0
    updated_entities = []

    for entity_id, entity_data in entities.items():
        if entity_data.get('epstein_connection'):
            has_connection += 1
        else:
            needs_connection += 1

            # Generate connection from flight logs
            connection = generate_connection_from_flights(entity_data)

            if dry_run:
                print(f"\n🔍 Would add connection to {entity_data.get('display_name', entity_id)}:")
                print(f"   \"{connection}\"")
            else:
                entity_data['epstein_connection'] = connection
                updated_entities.append({
                    'id': entity_id,
                    'name': entity_data.get('display_name', entity_id),
                    'connection': connection
                })

    print(f"\n📊 Summary:")
    print(f"   ✅ Entities with connection: {has_connection}")
    print(f"   ⚠️  Entities needing connection: {needs_connection}")

    if dry_run:
        print(f"\n🔍 DRY RUN - No changes made")
        print(f"   Run without --dry-run to apply changes")
        return

    if needs_connection == 0:
        print(f"\n✅ All entities already have connection field")
        return

    # Create backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = bio_file.with_suffix(f'.backup_pre_connections_{timestamp}.json')

    print(f"\n💾 Creating backup at {backup_file}")
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Save updated data
    print(f"💾 Saving updated biographies to {bio_file}")
    with open(bio_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Successfully updated {needs_connection} entities")

    # Show sample of updates
    print(f"\n📋 Sample updates:")
    for update in updated_entities[:5]:
        print(f"   • {update['name']}")
        print(f"     \"{update['connection']}\"")

    if len(updated_entities) > 5:
        print(f"   ... and {len(updated_entities) - 5} more")

    print(f"\n✅ Done! Backup saved to: {backup_file}")
    print(f"\n💡 Next step: Restart backend to load updated entity data")
    print(f"   cd /Users/masa/Projects/epstein")
    print(f"   lsof -ti:8081 | xargs kill -9")
    print(f"   python3 server/app.py 8081 > /tmp/backend.log 2>&1 &")


if __name__ == '__main__':
    import sys

    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)

    add_connections(dry_run=dry_run)
