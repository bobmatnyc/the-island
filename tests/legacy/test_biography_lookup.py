#!/usr/bin/env python3
"""
Test Biography Lookup After Name Fix

Demonstrates that entity names can now successfully look up biographies.
Run this to verify the fix is working correctly.

Author: Claude Code
Date: 2025-11-18
"""

import json
import sys
from pathlib import Path


def test_biography_lookup():
    """Test that entity names can find their biographies."""

    # Load data
    project_root = Path("/Users/masa/Projects/epstein")

    with open(project_root / "data/md/entities/ENTITIES_INDEX.json") as f:
        entity_index = json.load(f)

    with open(project_root / "data/metadata/entity_biographies.json") as f:
        biographies = json.load(f)

    # Get entity names and biography keys
    entities = {e.get("name"): e for e in entity_index.get("entities", []) if e.get("name")}
    bio_dict = biographies.get("entities", {})

    print("="*70)
    print("BIOGRAPHY LOOKUP TEST - Post-Fix Validation")
    print("="*70)

    # Test key entities that should have biographies
    test_entities = [
        "Maxwell, Ghislaine",
        "Epstein, Jeffrey",
        "William Clinton",
        "Prince Andrew",
        "Nadia",  # Marcinkova
        "Leslie Wexner",
        "Roberts, Virginia",  # Giuffre
        "Kellen, Sarah",
        "Band, Doug",
        "Dubin, Glenn"
    ]

    print(f"\nTesting {len(test_entities)} key entities...\n")

    success_count = 0
    for entity_name in test_entities:
        # Check if entity exists
        if entity_name not in entities:
            print(f"❌ {entity_name:<25} - Entity not found in system")
            continue

        # Check if biography exists
        if entity_name not in bio_dict:
            print(f"⚠️  {entity_name:<25} - No biography (expected for some)")
            continue

        # Success! Can look up biography
        bio = bio_dict[entity_name]
        success_count += 1

        print(f"✅ {entity_name:<25}")
        print(f"   Full Name: {bio.get('full_name', 'N/A')}")
        print(f"   Born: {bio.get('born', 'N/A')}")
        print(f"   Summary: {bio.get('summary', '')[:80]}...")
        print()

    # Statistics
    print("="*70)
    print("RESULTS")
    print("="*70)
    print(f"Total entities tested: {len(test_entities)}")
    print(f"Successful lookups: {success_count}")
    print(f"Success rate: {success_count}/{len(test_entities)} ({100*success_count//len(test_entities)}%)")

    # Overall stats
    total_bios = len(bio_dict)
    matched_bios = len(set(bio_dict.keys()) & set(entities.keys()))

    print(f"\nTotal biographies in system: {total_bios}")
    print(f"Matched to entities: {matched_bios}/{total_bios} ({100*matched_bios//total_bios}%)")

    if success_count == len(test_entities):
        print("\n✅ ALL TESTS PASSED - Biography lookup working correctly!")
        return 0
    if success_count >= len(test_entities) * 0.8:
        print("\n✅ TESTS MOSTLY PASSED - Some mismatches expected")
        return 0
    print("\n❌ TESTS FAILED - Biography lookup not working")
    return 1


if __name__ == "__main__":
    sys.exit(test_biography_lookup())
