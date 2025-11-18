#!/usr/bin/env python3
"""
Fix Nested Entity References - Final Cleanup Pass
==================================================

This script fixes entity references in nested data structures:
- top_connections[].name
- name_variations[]

Uses the OCR mappings we already applied to entity keys.

Author: Claude
Date: 2025-11-17
"""

import json
import re
import shutil
import pickle
from pathlib import Path
from datetime import datetime

def detect_ocr_duplicate(name: str):
    """Detect and fix OCR duplicate pattern"""
    normalized = re.sub(r'\s+', ' ', name).strip()
    words = normalized.split()

    if len(words) < 2:
        return None

    if words[0].lower() == words[1].lower() and words[0][0].isupper():
        cleaned = ' '.join(words[1:])
        if cleaned and len(cleaned) > 2:
            return cleaned
    return None

def main():
    # Paths
    data_dir = Path('/Users/masa/Projects/Epstein/data')
    stats_path = data_dir / 'metadata/entity_statistics.json'
    backup_dir = data_dir / 'backups' / f"nested_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Backup
    backup_path = backup_dir / 'entity_statistics.json'
    shutil.copy2(stats_path, backup_path)
    print(f"Backed up to: {backup_path}")

    # Load data
    with open(stats_path, 'r') as f:
        data = json.load(f)

    stats = data.get("statistics", {})

    # Build mappings from current cleaned entity keys
    print("\nBuilding OCR mapping table from cleaned entity names...")

    # Known fixes
    mappings = {
        "Epstein, Je Je": "Epstein, Jeffrey",
        "Je Epstein": "Epstein, Jeffrey",
        "Epstein Je": "Epstein, Jeffrey",
        "Je Je": "Epstein, Jeffrey",
        "Ghislaine Ghislaine": "Maxwell, Ghislaine",
        "Nadia Nadia": "Marcinkova, Nadia",
        "Virginia Virginia Roberts": "Roberts, Virginia",
        "Virginia Virginia": "Roberts, Virginia",
    }

    # Load OCR mappings from backup if available
    backup_stats_path = data_dir / 'backups/cleanup_20251117_154454/entity_statistics.json'
    if backup_stats_path.exists():
        with open(backup_stats_path, 'r') as f:
            backup_data = json.load(f)
            backup_stats = backup_data.get("statistics", {})

        # Detect OCR duplicates from backup
        for entity_name in backup_stats.keys():
            cleaned = detect_ocr_duplicate(entity_name)
            if cleaned:
                mappings[entity_name] = cleaned

    print(f"  Total mappings: {len(mappings)}")

    # Fix nested references
    print("\nFixing nested entity references...")

    total_fixed = 0
    entities_updated = 0

    for entity_name, entity_data in stats.items():
        entity_modified = False

        # Fix top_connections
        if 'top_connections' in entity_data:
            for connection in entity_data['top_connections']:
                old_name = connection.get('name', '')

                # Try known mappings first
                if old_name in mappings:
                    new_name = mappings[old_name]
                    if new_name:
                        connection['name'] = new_name
                        total_fixed += 1
                        entity_modified = True
                # Try OCR detection
                else:
                    cleaned = detect_ocr_duplicate(old_name)
                    if cleaned:
                        connection['name'] = cleaned
                        total_fixed += 1
                        entity_modified = True

        # Fix name_variations
        if 'name_variations' in entity_data:
            cleaned_variations = []
            for variation in entity_data['name_variations']:
                # Try mappings
                if variation in mappings:
                    cleaned = mappings[variation]
                    if cleaned:
                        cleaned_variations.append(cleaned)
                        entity_modified = True
                else:
                    # Try OCR detection
                    cleaned = detect_ocr_duplicate(variation)
                    if cleaned:
                        cleaned_variations.append(cleaned)
                        entity_modified = True
                    else:
                        cleaned_variations.append(variation)

            entity_data['name_variations'] = cleaned_variations

        if entity_modified:
            entities_updated += 1

    # Save updated data
    with open(stats_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Fixed {total_fixed} nested entity references")
    print(f"✓ Updated {entities_updated} entities")

    # Verify
    print("\nVerifying cleanup...")
    with open(stats_path, 'r') as f:
        verify_data = json.load(f)

    verify_stats = verify_data.get("statistics", {})

    # Count remaining whitespace issues
    remaining_issues = []
    for entity_name, entity_data in verify_stats.items():
        if 'top_connections' in entity_data:
            for conn in entity_data['top_connections']:
                conn_name = conn.get('name', '')
                if '  ' in conn_name:  # Multiple spaces
                    remaining_issues.append(conn_name)

    unique_issues = set(remaining_issues)

    if unique_issues:
        print(f"\n⚠ Found {len(remaining_issues)} remaining whitespace issues ({len(unique_issues)} unique):")
        for issue in list(unique_issues)[:10]:
            print(f'    "{issue}"')
    else:
        print("\n✅ No whitespace issues remaining!")

    print("\n" + "=" * 70)
    print("NEXT STEPS")
    print("=" * 70)
    print("1. Restart server:")
    print("   kill -9 $(lsof -ti:8081)")
    print("   cd /Users/masa/Projects/Epstein/server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &")
    print("\n2. Verify in UI at http://localhost:8081")
    print("   - Check entity names are clean")
    print("   - Check connections use canonical names")
    print("   - Search for entities works correctly")

if __name__ == "__main__":
    main()
