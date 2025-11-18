#!/usr/bin/env python3
"""
Fix Entity Name Formatting Issues

Fixes multiple formatting problems:
- Trailing commas: "Jeffrey, Epstein," → "Epstein, Jeffrey"
- Double commas: "Epstein,, Jeffrey," → "Epstein, Jeffrey"
- Reversed names: "Jeffrey, Epstein" → "Epstein, Jeffrey"
- Double spaces and extra whitespace

Validation rules:
- Proper format: "LastName, FirstName" or "LastName, FirstName Suffix"
- No trailing commas
- Single comma only
- No double spaces
"""

import json
import re
from pathlib import Path
from datetime import datetime

def is_likely_reversed(first_part: str, second_part: str) -> bool:
    """
    Detect if name is likely reversed (FirstName, LastName instead of LastName, FirstName).

    Logic:
    - Common first names appearing in first position suggest reversal
    - First part being title case and shorter suggests it's a first name
    - All caps second part suggests last name
    """
    # Known first names from the dataset
    common_first_names = {
        'Jeffrey', 'Ghislaine', 'Bill', 'Donald', 'Glenn', 'Alan', 'Larry',
        'Susan', 'Nadia', 'John', 'Sarah', 'Emmy', 'Eva', 'Celina'
    }

    # Check if first part is a known first name
    if first_part in common_first_names:
        return True

    # Check structural patterns
    if (first_part.istitle() and
        len(first_part) < len(second_part) and
        (second_part.isupper() or second_part.istitle())):
        return True

    return False

def fix_name_formatting(name: str) -> tuple[str, list[str]]:
    """
    Fix common name formatting issues.

    Returns:
        tuple: (fixed_name, list_of_changes_made)
    """
    original = name
    changes = []

    # Step 1: Remove trailing commas and spaces
    name = name.strip().rstrip(',').strip()
    if original != name:
        changes.append("removed_trailing_comma")

    # Step 2: Fix double commas
    if ',,' in name:
        name = re.sub(r',\s*,', ',', name)
        changes.append("fixed_double_comma")

    # Step 3: Fix double spaces
    name = re.sub(r'\s+', ' ', name)

    # Step 4: Check if reversed (FirstName, LastName → LastName, FirstName)
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            first, second = parts

            # Remove suffix/title from second part for analysis
            second_clean = re.sub(r'\s+(Jr\.|Sr\.|Esq\.|III|II|DVM)$', '', second)

            if is_likely_reversed(first, second_clean):
                # Reverse the name
                name = f"{second}, {first}"
                changes.append("reversed_name_order")

    # Step 5: Ensure single space after comma
    name = re.sub(r',\s*', ', ', name)

    return name, changes

def main():
    """Main execution function."""
    # File paths
    stats_file = Path('/Users/masa/Projects/epstein/data/metadata/entity_statistics.json')
    backup_file = stats_file.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')

    print("Entity Name Formatting Fixer")
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
        'reversed_name_order': 0
    }

    examples = []

    for key, entity in data['statistics'].items():
        if 'name' not in entity:
            continue

        original = entity['name']
        fixed, changes = fix_name_formatting(original)

        if original != fixed:
            entity['name'] = fixed
            fixed_count += 1

            # Track change types
            for change in changes:
                changes_by_type[change] = changes_by_type.get(change, 0) + 1

            # Collect examples (first 15)
            if len(examples) < 15:
                examples.append({
                    'key': key,
                    'original': original,
                    'fixed': fixed,
                    'changes': changes
                })

            print(f"   Fixed: \"{original}\" → \"{fixed}\"")

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
        print(f"  - {change_type}: {count}")

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

    print(f"\nBackup saved to: {backup_file}")
    print(f"Results saved to: {stats_file}")

if __name__ == '__main__':
    main()
