#!/usr/bin/env python3
"""
Update master_document_index.json with correct document counts
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def update_master_index():
    """Update master document index with correct counts"""

    # Paths
    metadata_dir = Path(__file__).parent.parent.parent / "data" / "metadata"
    index_file = metadata_dir / "master_document_index.json"

    print(f"📂 Reading master document index: {index_file}")

    # Load existing index
    with open(index_file, 'r') as f:
        index_data = json.load(f)

    # Get current values
    old_total = index_data.get('total_files', 0)
    old_house_count = index_data['sources']['house_oversight_nov2025']['document_count']

    print(f"\n📊 Current values:")
    print(f"  Total files: {old_total:,}")
    print(f"  house_oversight_nov2025: {old_house_count:,}")

    # Update house_oversight_nov2025 count
    correct_house_count = 33572
    index_data['sources']['house_oversight_nov2025']['document_count'] = correct_house_count

    # Recalculate total_files
    # The total_files includes all files (with duplicates)
    # We need to adjust it by the difference in house_oversight count
    count_difference = old_house_count - correct_house_count
    new_total = old_total - count_difference
    index_data['total_files'] = new_total

    # Update generated_at timestamp
    index_data['generated_at'] = datetime.now().isoformat()

    # Add update note
    if 'update_history' not in index_data:
        index_data['update_history'] = []

    index_data['update_history'].append({
        'date': datetime.now().isoformat(),
        'change': 'Corrected house_oversight_nov2025 count',
        'old_count': old_house_count,
        'new_count': correct_house_count,
        'reason': 'Master index contained phantom documents - corrected to match actual file system'
    })

    print(f"\n✏️  New values:")
    print(f"  Total files: {new_total:,} (adjusted by {-count_difference:,})")
    print(f"  house_oversight_nov2025: {correct_house_count:,}")

    # Save updated index
    print(f"\n💾 Saving updated index...")
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)

    print(f"\n✅ Master document index updated successfully!")
    print(f"\n📄 File: {index_file}")

    # Summary
    print(f"\n📊 Summary of changes:")
    print(f"  house_oversight_nov2025: {old_house_count:,} → {correct_house_count:,} ({-count_difference:,})")
    print(f"  Total files: {old_total:,} → {new_total:,} ({-count_difference:,})")

    return True

if __name__ == "__main__":
    try:
        update_master_index()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
