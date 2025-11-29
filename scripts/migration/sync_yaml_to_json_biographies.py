#!/usr/bin/env python3
"""
Sync biographical data from entities.yaml to entity_biographies.json

This script reads the comprehensive 500-800 word biographies from entities.yaml
and updates the corresponding entities in entity_biographies.json.

Usage:
    python sync_yaml_to_json_biographies.py [--dry-run]
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
import argparse
import shutil


def load_yaml_entities(yaml_path: Path) -> dict:
    """Load entity data from YAML file."""
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    return data.get('entities', {})


def load_json_biographies(json_path: Path) -> dict:
    """Load existing biography data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


def create_backup(json_path: Path) -> Path:
    """Create timestamped backup of JSON file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = json_path.parent / f"entity_biographies.backup_{timestamp}.json"
    shutil.copy2(json_path, backup_path)
    print(f"✓ Created backup: {backup_path.name}")
    return backup_path


def sync_biography_data(yaml_entities: dict, json_data: dict) -> tuple[dict, list]:
    """
    Sync biographical data from YAML to JSON format.

    Returns:
        Tuple of (updated_json_data, update_log)
    """
    updates = []
    json_entities = json_data.get('entities', {})

    # Primary entities to sync from entities.yaml
    primary_entity_ids = [
        'jeffrey_epstein',
        'ghislaine_maxwell',
        'prince_andrew',
        'william_clinton',
        'donald_trump',
        'alan_dershowitz',
        'leslie_wexner',
        'jeanluc_brunel'
    ]

    for entity_id in primary_entity_ids:
        if entity_id not in yaml_entities:
            print(f"⚠️  Entity {entity_id} not found in YAML")
            continue

        yaml_entity = yaml_entities[entity_id]

        # Get or create JSON entity entry
        if entity_id not in json_entities:
            json_entities[entity_id] = {
                'id': entity_id,
                'display_name': yaml_entity.get('display_name', yaml_entity.get('full_name')),
            }
            updates.append(f"Created new entry for {entity_id}")

        json_entity = json_entities[entity_id]

        # Update biographical fields
        updates_for_entity = []

        # Core biographical data
        if 'full_name' in yaml_entity and json_entity.get('full_name') != yaml_entity['full_name']:
            json_entity['full_name'] = yaml_entity['full_name']
            updates_for_entity.append('full_name')

        if 'display_name' in yaml_entity and json_entity.get('display_name') != yaml_entity['display_name']:
            json_entity['display_name'] = yaml_entity['display_name']
            updates_for_entity.append('display_name')

        if 'born' in yaml_entity:
            json_entity['born'] = yaml_entity['born']
            updates_for_entity.append('born')

        if 'died' in yaml_entity:
            json_entity['died'] = yaml_entity['died']
            updates_for_entity.append('died')

        if 'birth_place' in yaml_entity:
            json_entity['birth_place'] = yaml_entity['birth_place']
            updates_for_entity.append('birth_place')

        if 'nationality' in yaml_entity:
            json_entity['nationality'] = yaml_entity['nationality']
            updates_for_entity.append('nationality')

        if 'occupation' in yaml_entity:
            json_entity['occupation'] = yaml_entity['occupation']
            updates_for_entity.append('occupation')

        # Summary (2-3 sentences)
        if 'summary' in yaml_entity:
            json_entity['summary'] = yaml_entity['summary']
            updates_for_entity.append('summary')

        # Full biography (500-800 words)
        if 'full_biography' in yaml_entity:
            # Add as 'biography' field for compatibility with EntityBio component
            json_entity['biography'] = yaml_entity['full_biography']
            updates_for_entity.append('biography')

            # Also update the old 'summary' if it doesn't exist
            if 'summary' not in json_entity:
                json_entity['summary'] = yaml_entity.get('summary', '')

        # Timeline events
        if 'timeline_events' in yaml_entity and yaml_entity['timeline_events']:
            if 'timeline' not in json_entity:
                json_entity['timeline'] = []
            # Convert YAML timeline to JSON format
            json_entity['timeline'] = [
                {
                    'date': event.get('date', ''),
                    'event': event.get('event', '')
                }
                for event in yaml_entity['timeline_events']
            ]
            updates_for_entity.append('timeline')

        # Relationships
        if 'relationships' in yaml_entity and yaml_entity['relationships']:
            json_entity['relationships'] = [
                {
                    'entity': rel.get('name', ''),
                    'nature': rel.get('nature', ''),
                    'description': rel.get('description', '')
                }
                for rel in yaml_entity['relationships']
            ]
            updates_for_entity.append('relationships')

        # Document references
        if 'document_references' in yaml_entity:
            json_entity['document_references'] = yaml_entity['document_references']
            updates_for_entity.append('document_references')

        if updates_for_entity:
            updates.append(f"{entity_id}: {', '.join(updates_for_entity)}")

    # Update metadata
    if 'metadata' not in json_data:
        json_data['metadata'] = {}

    json_data['metadata']['yaml_sync_date'] = datetime.now().isoformat()
    json_data['metadata']['yaml_sync_entities'] = len(primary_entity_ids)
    json_data['metadata']['last_updated'] = datetime.now().isoformat()

    return json_data, updates


def main():
    parser = argparse.ArgumentParser(description='Sync entities.yaml to entity_biographies.json')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without saving')
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent.parent
    yaml_path = project_root / "data" / "entities.yaml"
    json_path = project_root / "data" / "metadata" / "entity_biographies.json"

    print(f"📖 Reading YAML entities from: {yaml_path}")
    print(f"📖 Reading JSON biographies from: {json_path}")
    print()

    # Validate files exist
    if not yaml_path.exists():
        print(f"❌ Error: {yaml_path} not found")
        return 1

    if not json_path.exists():
        print(f"❌ Error: {json_path} not found")
        return 1

    # Load data
    yaml_entities = load_yaml_entities(yaml_path)
    json_data = load_json_biographies(json_path)

    print(f"✓ Loaded {len(yaml_entities)} entities from YAML")
    print(f"✓ Loaded {len(json_data.get('entities', {}))} entities from JSON")
    print()

    # Sync data
    print("🔄 Syncing biographical data...")
    updated_json, updates = sync_biography_data(yaml_entities, json_data)

    print()
    print("=" * 60)
    print("UPDATES SUMMARY")
    print("=" * 60)
    for update in updates:
        print(f"  • {update}")
    print()
    print(f"Total changes: {len(updates)}")
    print("=" * 60)
    print()

    if args.dry_run:
        print("🔍 DRY RUN - No files modified")
        return 0

    # Create backup
    backup_path = create_backup(json_path)

    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(updated_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved updated biographies to: {json_path}")
    print()
    print("✅ SYNC COMPLETE")

    # Validate JSON
    try:
        with open(json_path, 'r') as f:
            json.load(f)
        print("✓ JSON validation passed")
    except json.JSONDecodeError as e:
        print(f"❌ JSON validation failed: {e}")
        # Restore backup
        shutil.copy2(backup_path, json_path)
        print(f"⚠️  Restored from backup")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
