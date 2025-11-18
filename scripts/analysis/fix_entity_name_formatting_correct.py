#!/usr/bin/env python3
"""
Fix Entity Name Formatting Issues - CORRECT VERSION

The CORRECT format is: "LastName, FirstName" (e.g., "Epstein, Jeffrey")

Fixes these specific problems:
- Trailing commas: "Jeffrey, Epstein," → "Epstein, Jeffrey"
- Double commas: "Newman,, Larry Esq." → "Newman, Larry Esq."
- Reversed with trailing: "Ghislaine, Maxwell," → "Maxwell, Ghislaine"

DOES NOT reverse already-correct names like "Epstein, Jeffrey"
"""

import json
import re
from pathlib import Path
from datetime import datetime

def fix_name_formatting(name: str, entity_key: str) -> tuple[str, list[str]]:
    """
    Fix common name formatting issues.

    The correct format is "LastName, FirstName".

    Returns:
        tuple: (fixed_name, list_of_changes_made)
    """
    original = name
    changes = []

    # Step 1: Remove trailing commas and spaces
    name_clean = name.strip().rstrip(',').strip()
    if original.endswith(','):
        changes.append("removed_trailing_comma")

    # Step 2: Fix double commas
    if ',,' in name_clean:
        name_clean = re.sub(r',\s*,', ',', name_clean)
        changes.append("fixed_double_comma")

    # Step 3: Fix double spaces
    name_clean = re.sub(r'\s+', ' ', name_clean)

    # Step 4: Check if reversed by looking at the entity_key
    # The entity_key should match the proper format "LastName, FirstName"
    # If we removed a trailing comma and the key matches "FirstName, LastName" pattern,
    # it was likely reversed
    if changes and ',' in name_clean and ',' in entity_key:
        parts_name = [p.strip() for p in name_clean.split(',', 1)]
        parts_key = [p.strip() for p in entity_key.split(',', 1)]

        if len(parts_name) == 2 and len(parts_key) == 2:
            # If name parts are swapped compared to key, reverse them
            if parts_name[0] == parts_key[1] and parts_name[1] == parts_key[0]:
                name_clean = f"{parts_name[1]}, {parts_name[0]}"
                changes.append("fixed_reversed_name")

    # Step 5: Ensure single space after comma
    name_clean = re.sub(r',\s*', ', ', name_clean)

    return name_clean, changes

def main():
    """Main execution function."""
    # File paths
    stats_file = Path('/Users/masa/Projects/epstein/data/metadata/entity_statistics.json')
    backup_file = stats_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

    print("Entity Name Formatting Fixer (CORRECT VERSION)")
    print("=" * 60)

    # Load data
    print(f"\n1. Loading {stats_file}")
    with open(stats_file) as f:
        data = json.load(f)

    total_entities = data.get('total_entities', 0)
    print(f"   Total entities: {total_entities}")

    # Create backup
    print(f"\n2. Creating backup at {backup_file}")
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Process entities
    print("\n3. Processing entity names...")
    fixed_count = 0
    changes_by_type = {
        'removed_trailing_comma': 0,
        'fixed_double_comma': 0,
        'fixed_reversed_name': 0
    }

    examples = []

    for key, entity in data['statistics'].items():
        if 'name' not in entity:
            continue

        original = entity['name']
        fixed, changes = fix_name_formatting(original, key)

        if original != fixed:
            entity['name'] = fixed
            fixed_count += 1

            # Track change types
            for change in changes:
                changes_by_type[change] = changes_by_type.get(change, 0) + 1

            # Collect examples (first 20)
            if len(examples) < 20:
                examples.append({
                    'key': key,
                    'original': original,
                    'fixed': fixed,
                    'changes': changes
                })

            print(f"   Fixed: \"{original}\" → \"{fixed}\" (key: {key})")

    # Update metadata
    data['generated'] = datetime.now().isoformat()

    # Write back
    print(f"\n4. Writing corrected data back to {stats_file}")
    with open(stats_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Generate report
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"\nTotal entities processed: {len(data['statistics'])}")
    print(f"Entities with name fixes: {fixed_count}")
    print(f"\nChanges by type:")
    for change_type, count in sorted(changes_by_type.items()):
        if count > 0:
            print(f"  - {change_type}: {count}")

    if examples:
        print(f"\nExample corrections:")
        for i, example in enumerate(examples, 1):
            print(f"\n{i}. Key: {example['key']}")
            print(f"   Original: \"{example['original']}\"")
            print(f"   Fixed:    \"{example['fixed']}\"")
            print(f"   Changes:  {', '.join(example['changes'])}")

    # Validation check
    print("\n" + "=" * 60)
    print("VALIDATION CHECK")
    print("=" * 60)

    remaining_issues = []
    for key, entity in data['statistics'].items():
        name = entity.get('name', '')
        if name.endswith(','):
            remaining_issues.append(('trailing_comma', key, name))
        if ',,' in name:
            remaining_issues.append(('double_comma', key, name))

    if remaining_issues:
        print(f"\n⚠️  WARNING: {len(remaining_issues)} issues still remain:")
        for issue_type, key, name in remaining_issues[:10]:
            print(f"   {issue_type}: {key} -> \"{name}\"")
    else:
        print("\n✅ SUCCESS: No formatting issues detected!")

    # Sample check of well-known entities
    print("\n" + "=" * 60)
    print("SAMPLE CHECK - Well-Known Entities")
    print("=" * 60)

    well_known = ['Epstein, Jeffrey', 'Donald Trump', 'Ghislaine Maxwell',
                  'Glenn Dubin', 'Bill Clinton']
    for key in well_known:
        if key in data['statistics']:
            name = data['statistics'][key]['name']
            print(f"✓ {key}: \"{name}\"")

    print(f"\nBackup saved to: {backup_file}")
    print(f"Results saved to: {stats_file}")

if __name__ == '__main__':
    main()
