#!/usr/bin/env python3
"""
Fix remaining duplicate first names in entity_network.json

Found duplicates:
- Nadia Nadia
- Illegible Illegible
- Baby Baby
- Reposition Reposition
"""

import json
from pathlib import Path

def fix_duplicate_names():
    """Fix duplicate first names in entity network"""

    network_file = Path("/Users/masa/Projects/Epstein/data/metadata/entity_network.json")

    # Load network data
    with open(network_file, 'r') as f:
        data = json.load(f)

    # Name fix mappings
    fixes = {
        "Nadia Nadia": "Nadia",
        "Illegible Illegible": "Illegible",
        "Baby Baby": "Baby",
        "Reposition Reposition": "Reposition"
    }

    changes_made = 0

    # Fix node names
    for node in data.get('nodes', []):
        old_name = node.get('name', '')
        if old_name in fixes:
            new_name = fixes[old_name]
            node['name'] = new_name
            print(f"Fixed node: {old_name} → {new_name}")
            changes_made += 1

    # Fix edge source/target references
    for edge in data.get('edges', []):
        if edge.get('source') in fixes:
            old = edge['source']
            edge['source'] = fixes[old]
            print(f"Fixed edge source: {old} → {edge['source']}")
            changes_made += 1

        if edge.get('target') in fixes:
            old = edge['target']
            edge['target'] = fixes[old]
            print(f"Fixed edge target: {old} → {edge['target']}")
            changes_made += 1

    # Save backup
    backup_file = network_file.with_suffix('.json.backup')
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Backup saved to: {backup_file}")

    # Save fixed version
    with open(network_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed {changes_made} occurrences")
    print(f"✓ Updated: {network_file}")

    return changes_made

if __name__ == "__main__":
    changes = fix_duplicate_names()
    print(f"\n🎉 Complete! Fixed {changes} duplicate names.")
