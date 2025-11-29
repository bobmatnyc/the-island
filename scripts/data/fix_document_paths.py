#!/usr/bin/env python3
"""
Fix document paths in entity_statistics.json.

Changes paths from:
  data/ocr/DOJ-OGR-*.txt
To:
  data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-*.txt

Creates backup before modifying the file.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITY_STATS_PATH = PROJECT_ROOT / "data" / "metadata" / "entity_statistics.json"

def load_entity_stats() -> Dict:
    """Load the entity statistics."""
    print(f"Loading entity statistics from: {ENTITY_STATS_PATH}")

    if not ENTITY_STATS_PATH.exists():
        print(f"ERROR: Entity statistics not found at {ENTITY_STATS_PATH}")
        sys.exit(1)

    with open(ENTITY_STATS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_backup(data: Dict) -> Path:
    """Create timestamped backup of entity statistics."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = ENTITY_STATS_PATH.parent / f"entity_statistics.backup_{timestamp}.json"

    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return backup_path

def fix_path(old_path: str) -> str:
    """
    Convert old path format to new path format.

    Args:
        old_path: Path like "data/ocr/DOJ-OGR-12345.txt"

    Returns:
        New path like "data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-12345.txt"
    """
    if not old_path.startswith("data/ocr/"):
        return old_path

    # Extract filename (everything after "data/ocr/")
    filename = old_path.replace("data/ocr/", "")

    # Build new path
    new_path = f"data/sources/house_oversight_nov2025/ocr_text/{filename}"

    return new_path

def verify_path_exists(path: str) -> bool:
    """Check if a path exists on disk."""
    full_path = PROJECT_ROOT / path
    return full_path.exists()

def fix_document_paths(data: Dict) -> Tuple[Dict, Dict[str, int]]:
    """
    Fix all document paths in the entity statistics.

    Returns:
        Tuple of (updated_data, statistics)
    """
    stats = {
        'total_entities': 0,
        'entities_with_documents': 0,
        'total_documents': 0,
        'paths_checked': 0,
        'paths_fixed': 0,
        'paths_verified': 0,
        'paths_not_found': 0,
        'paths_unchanged': 0
    }

    not_found_paths = []

    print("\nProcessing entities...")

    # Process each entity in the statistics
    statistics = data.get('statistics', {})

    for entity_id, entity_data in statistics.items():
        stats['total_entities'] += 1

        if 'documents' not in entity_data or not entity_data['documents']:
            continue

        stats['entities_with_documents'] += 1
        documents = entity_data['documents']
        stats['total_documents'] += len(documents)

        # Fix paths in each document
        for doc in documents:
            if 'path' not in doc:
                continue

            stats['paths_checked'] += 1
            old_path = doc['path']
            new_path = fix_path(old_path)

            # Check if path was changed
            if new_path != old_path:
                stats['paths_fixed'] += 1
                doc['path'] = new_path

                # Verify new path exists
                if verify_path_exists(new_path):
                    stats['paths_verified'] += 1
                else:
                    stats['paths_not_found'] += 1
                    if len(not_found_paths) < 100:  # Limit stored examples
                        not_found_paths.append(new_path)
            else:
                stats['paths_unchanged'] += 1

                # Still verify unchanged paths exist
                if not verify_path_exists(old_path):
                    stats['paths_not_found'] += 1
                    if len(not_found_paths) < 100:
                        not_found_paths.append(old_path)

        # Print progress every 100 entities
        if stats['total_entities'] % 100 == 0:
            print(f"  Processed {stats['total_entities']:,} entities, "
                  f"fixed {stats['paths_fixed']:,} paths...")

    # Store not found paths for reporting
    stats['not_found_paths'] = not_found_paths[:10]  # Store first 10 examples

    return data, stats

def save_entity_stats(data: Dict) -> None:
    """Save updated entity statistics."""
    print(f"\nSaving updated entity statistics to: {ENTITY_STATS_PATH}")

    with open(ENTITY_STATS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def print_statistics(stats: Dict[str, int]) -> None:
    """Print detailed statistics."""
    print("\n" + "="*60)
    print("DOCUMENT PATH FIX RESULTS")
    print("="*60)

    print(f"\nEntities processed: {stats['total_entities']:,}")
    print(f"Entities with documents: {stats['entities_with_documents']:,}")
    print(f"Total documents: {stats['total_documents']:,}")

    print(f"\nPath Operations:")
    print(f"  Paths checked: {stats['paths_checked']:,}")
    print(f"  Paths fixed: {stats['paths_fixed']:,}")
    print(f"  Paths unchanged: {stats['paths_unchanged']:,}")

    print(f"\nVerification:")
    print(f"  Paths verified (exist on disk): {stats['paths_verified']:,}")
    print(f"  Paths NOT found on disk: {stats['paths_not_found']:,}")

    if stats['paths_not_found'] > 0:
        print(f"\n⚠️  WARNING: {stats['paths_not_found']:,} paths not found on disk!")
        print("  Example paths not found:")
        for path in stats.get('not_found_paths', [])[:5]:
            print(f"    - {path}")

    print("\n" + "="*60)

    # Summary
    if stats['paths_fixed'] > 0 and stats['paths_not_found'] == 0:
        print("✅ SUCCESS: All paths fixed and verified!")
    elif stats['paths_fixed'] > 0 and stats['paths_not_found'] > 0:
        print("⚠️  PARTIAL SUCCESS: Paths fixed but some not found on disk")
    elif stats['paths_fixed'] == 0:
        print("ℹ️  NO CHANGES: All paths already correct")

    print("="*60 + "\n")

def main():
    """Main execution."""
    print("="*60)
    print("ENTITY STATISTICS PATH FIXER")
    print("="*60)
    print()

    # Load entity statistics
    data = load_entity_stats()

    # Create backup
    backup_path = create_backup(data)
    print(f"✅ Backup created successfully\n")

    # Fix paths
    updated_data, stats = fix_document_paths(data)

    # Save updated statistics
    save_entity_stats(updated_data)
    print("✅ Entity statistics saved successfully")

    # Print statistics
    print_statistics(stats)

    # Exit code based on results
    if stats['paths_not_found'] > 0:
        print("⚠️  Exiting with warning due to missing files")
        sys.exit(1)
    else:
        print("✅ All operations completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
