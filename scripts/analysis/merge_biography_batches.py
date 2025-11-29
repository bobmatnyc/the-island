#!/usr/bin/env python3
"""
Merge biography batch files into master entity_biographies.json

Design Decision: Selective Batch Merging
Rationale: Instead of automatically merging ALL batch files, allow specifying
which batches to merge. This prevents accidental re-merging of already processed
batches and provides fine-grained control.

Trade-offs:
- Flexibility: Can merge specific batches (e.g., only batch 9)
- Safety: Reduces risk of data corruption from re-merging
- Complexity: Requires user to track which batches are merged

Usage:
    python merge_biography_batches.py [batch_numbers...]
    python merge_biography_batches.py 9          # Merge only batch 9
    python merge_biography_batches.py 9 10       # Merge batches 9 and 10
    python merge_biography_batches.py --all      # Merge all available batches
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set

def create_backup(master_file: Path) -> Path:
    """Create timestamped backup of master file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = master_file.parent / f"entity_biographies_backup_{timestamp}.json"
    shutil.copy2(master_file, backup_file)
    return backup_file

def load_batch_file(batch_file: Path) -> Dict:
    """Load and validate batch file"""
    with open(batch_file, 'r') as f:
        data = json.load(f)

    if 'entities' not in data:
        raise ValueError(f"Batch file {batch_file.name} missing 'entities' key")

    return data

def calculate_statistics(entities_dict: Dict) -> Dict:
    """
    Calculate aggregate statistics across all entities

    Performance: O(n) time complexity, O(1) space
    Handles both nested metadata and top-level field structures
    """
    total_quality = 0
    total_words = 0
    count_quality = 0
    count_words = 0

    for entity in entities_dict.values():
        # Try both structures: nested metadata and top-level fields
        quality_score = entity.get('quality_score') or entity.get('metadata', {}).get('quality_score')
        word_count = entity.get('word_count') or entity.get('metadata', {}).get('word_count')

        if quality_score is not None:
            total_quality += quality_score
            count_quality += 1

        if word_count is not None:
            total_words += word_count
            count_words += 1

    return {
        'average_quality_score': total_quality / count_quality if count_quality > 0 else 0,
        'average_word_count': total_words / count_words if count_words > 0 else 0,
        'entities_with_quality_score': count_quality,
        'entities_with_word_count': count_words
    }

def merge_batches(batch_numbers: List[int] = None, merge_all: bool = False):
    """
    Merge specified biography batch files into master file

    Args:
        batch_numbers: List of batch numbers to merge (e.g., [9, 10])
        merge_all: If True, merge all available batch files
    """
    # Paths
    metadata_dir = Path(__file__).parent.parent.parent / "data" / "metadata"
    master_file = metadata_dir / "entity_biographies.json"

    # Create backup first
    print(f"📦 Creating backup of master file...")
    backup_file = create_backup(master_file)
    print(f"✓ Backup created: {backup_file.name}")

    # Load existing master file
    print(f"\n📖 Loading master file: {master_file.name}")
    with open(master_file, 'r') as f:
        master_data = json.load(f)

    entities_dict = master_data.get('entities', {})
    if not isinstance(entities_dict, dict):
        entities_dict = {}

    original_count = len(entities_dict)
    print(f"✓ Master file loaded: {original_count} entities")

    # Determine which batch files to process
    if merge_all:
        batch_files = sorted(metadata_dir.glob("entity_biographies_batch*.json"))
        # Exclude checkpoint and test files
        batch_files = [f for f in batch_files if 'checkpoint' not in f.name and 'test' not in f.name]
    else:
        batch_files = []
        for batch_num in (batch_numbers or []):
            batch_file = metadata_dir / f"entity_biographies_batch{batch_num}.json"
            if batch_file.exists():
                batch_files.append(batch_file)
            else:
                print(f"⚠️  Batch {batch_num} file not found: {batch_file.name}")

    if not batch_files:
        print("\n⚠️  No batch files to merge")
        return original_count

    print(f"\n📁 Batches to merge ({len(batch_files)}):")
    for batch in batch_files:
        print(f"  - {batch.name}")

    # Merge batches
    total_added = 0
    total_updated = 0
    duplicates_found: Set[str] = set()
    batch_summaries = []

    for batch_file in batch_files:
        print(f"\n📂 Processing {batch_file.name}...")

        try:
            batch_data = load_batch_file(batch_file)
        except Exception as e:
            print(f"  ❌ Error loading batch: {e}")
            continue

        batch_entities = batch_data.get('entities', {})
        batch_metadata = batch_data.get('metadata', {})

        print(f"  Entities: {len(batch_entities)}")
        print(f"  Generator: {batch_metadata.get('generator', 'unknown')}")

        added_in_batch = 0
        updated_in_batch = 0

        for entity_id, entity in batch_entities.items():
            if entity_id in entities_dict:
                # Check if this is truly a duplicate or an update
                duplicates_found.add(entity_id)
                entities_dict[entity_id] = entity
                total_updated += 1
                updated_in_batch += 1
            else:
                entities_dict[entity_id] = entity
                total_added += 1
                added_in_batch += 1

        batch_summaries.append({
            'file': batch_file.name,
            'total': len(batch_entities),
            'added': added_in_batch,
            'updated': updated_in_batch,
            'metadata': batch_metadata
        })

        print(f"  ✓ Added: {added_in_batch}, Updated: {updated_in_batch}")

    # Calculate aggregate statistics
    stats = calculate_statistics(entities_dict)

    # Update master data
    merged_batches = [b['file'] for b in batch_summaries]
    master_data['entities'] = entities_dict
    master_data['metadata'] = {
        'total_entities': len(entities_dict),
        'last_updated': datetime.now().isoformat(),
        'batches_merged': merged_batches,
        **stats
    }

    # Save merged master file
    print(f"\n💾 Saving merged master file...")
    with open(master_file, 'w') as f:
        json.dump(master_data, f, indent=2)

    # Generate merge report
    print(f"\n{'='*60}")
    print(f"✅ MERGE COMPLETE - Summary Report")
    print(f"{'='*60}")
    print(f"\n📊 Entity Counts:")
    print(f"  Before merge: {original_count}")
    print(f"  New entities:  {total_added}")
    print(f"  Updated:       {total_updated}")
    print(f"  After merge:   {len(entities_dict)}")

    print(f"\n📈 Aggregate Statistics:")
    print(f"  Avg quality score: {stats['average_quality_score']:.3f}")
    print(f"  Avg word count:    {stats['average_word_count']:.1f}")

    if duplicates_found:
        print(f"\n⚠️  Duplicates Found: {len(duplicates_found)}")
        print(f"  (These entities existed and were updated)")

    print(f"\n📁 Batch Details:")
    for summary in batch_summaries:
        print(f"  {summary['file']}:")
        print(f"    Total: {summary['total']}, Added: {summary['added']}, Updated: {summary['updated']}")

    print(f"\n💾 Files:")
    print(f"  Master: {master_file}")
    print(f"  Backup: {backup_file}")
    print(f"{'='*60}\n")

    return len(entities_dict)

if __name__ == "__main__":
    try:
        # Parse command line arguments
        args = sys.argv[1:]

        if '--help' in args or '-h' in args:
            print(__doc__)
            sys.exit(0)

        if '--all' in args:
            total = merge_batches(merge_all=True)
        elif args:
            # Parse batch numbers
            batch_numbers = []
            for arg in args:
                try:
                    batch_numbers.append(int(arg))
                except ValueError:
                    print(f"Warning: Ignoring invalid batch number: {arg}")
            total = merge_batches(batch_numbers=batch_numbers)
        else:
            print("Usage: merge_biography_batches.py [batch_numbers...] or --all")
            print("Example: merge_biography_batches.py 9 10")
            sys.exit(1)

        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
