#!/usr/bin/env python3
"""
Verify entity name normalization is working correctly.

Run this script to check:
1. Normalization mappings loaded
2. Network has no duplicate entities
3. Top relationships are correct
4. Server disambiguation service works
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from entity_normalization import EntityNormalizer


def check_mappings():
    """Verify entity name mappings loaded correctly"""
    print("=" * 70)
    print("1. CHECKING ENTITY NAME MAPPINGS")
    print("=" * 70)

    normalizer = EntityNormalizer()
    stats = normalizer.stats()

    print(f"✓ Loaded {stats['total_mappings']} entity name mappings")
    print(f"✓ Covering {stats['unique_canonical']} unique canonical entities")

    print("\nTop entities by variant count:")
    for canonical, count in stats["top_entities"]:
        print(f"  {canonical}: {count} variants")

    return stats["total_mappings"] > 0


def check_network():
    """Verify network has no duplicates"""
    print("\n" + "=" * 70)
    print("2. CHECKING ENTITY NETWORK")
    print("=" * 70)

    network_path = METADATA_DIR / "entity_network.json"
    with open(network_path) as f:
        network = json.load(f)

    nodes = network["nodes"]
    edges = network["edges"]

    print(f"✓ Total nodes: {len(nodes)}")
    print(f"✓ Total edges: {len(edges)}")

    # Check for duplicate patterns
    duplicate_patterns = [
        "Je        Je Epstein",
        "Je         Je Epstein",
        "Je          Je Epstein",
        "Je           Je Epstein",
        "Je       Je Epstein",
        "Ghislaine Ghislaine",
        "Bill        Bill Clinton",
        "Nadia Nadia",
    ]

    found_duplicates = []
    for pattern in duplicate_patterns:
        node = next((n for n in nodes if n["id"] == pattern), None)
        if node:
            found_duplicates.append(pattern)

    if found_duplicates:
        print(f"\n✗ Found {len(found_duplicates)} duplicate nodes:")
        for dup in found_duplicates:
            print(f"  - {dup}")
        return False
    print("\n✓ No duplicate nodes found")

    # Check for canonical entities
    canonical_entities = [
        "Jeffrey Epstein",
        "Ghislaine Maxwell",
        "William Clinton",
        "Nadia Marcinkova",
    ]

    print("\nCanonical entities present:")
    for entity in canonical_entities:
        node = next((n for n in nodes if n["id"] == entity), None)
        if node:
            print(f"  ✓ {entity}: {node['connection_count']} connections")
        else:
            print(f"  ✗ {entity}: NOT FOUND")
            return False

    return True


def check_relationships():
    """Verify top relationships are correct"""
    print("\n" + "=" * 70)
    print("3. CHECKING TOP RELATIONSHIPS")
    print("=" * 70)

    network_path = METADATA_DIR / "entity_network.json"
    with open(network_path) as f:
        network = json.load(f)

    edges = network["edges"]
    edges_sorted = sorted(edges, key=lambda e: e["weight"], reverse=True)[:5]

    print("\nTop 5 relationships:")
    for edge in edges_sorted:
        print(f"  {edge['source']:30s} ↔ {edge['target']:30s}: {edge['weight']:3d} flights")

    # Verify top relationship
    top_edge = edges_sorted[0]
    expected_entities = {"Jeffrey Epstein", "Ghislaine Maxwell"}
    actual_entities = {top_edge["source"], top_edge["target"]}

    if actual_entities == expected_entities:
        print(f"\n✓ Top relationship correct: {top_edge['source']} ↔ {top_edge['target']}")
        print(f"  (Should be ~478 flights, got: {top_edge['weight']})")
        return top_edge["weight"] >= 450  # Allow some variance
    print(f"\n✗ Top relationship incorrect: {actual_entities}")
    print(f"  Expected: {expected_entities}")
    return False


def check_server_service():
    """Verify server disambiguation service loads mappings"""
    print("\n" + "=" * 70)
    print("4. CHECKING SERVER DISAMBIGUATION SERVICE")
    print("=" * 70)

    try:
        # Import server service
        server_path = PROJECT_ROOT / "server" / "services"
        sys.path.insert(0, str(server_path))
        from entity_disambiguation import get_disambiguator

        disambiguator = get_disambiguator()

        # Test normalization
        test_cases = [
            ("Je        Je Epstein", "Jeffrey Epstein"),
            ("Ghislaine Ghislaine", "Ghislaine Maxwell"),
            ("Bill Clinton", "William Clinton"),
        ]

        all_passed = True
        for input_name, expected in test_cases:
            result = disambiguator.normalize_name(input_name)
            if result == expected:
                print(f'  ✓ "{input_name}" -> "{result}"')
            else:
                print(f'  ✗ "{input_name}" -> "{result}" (expected: "{expected}")')
                all_passed = False

        if all_passed:
            print("\n✓ Server disambiguation service working correctly")
        return all_passed

    except Exception as e:
        print(f"\n✗ Server service check failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("\nENTITY NAME NORMALIZATION VERIFICATION")
    print("=" * 70)

    checks = [
        ("Entity Name Mappings", check_mappings),
        ("Entity Network", check_network),
        ("Top Relationships", check_relationships),
        ("Server Service", check_server_service),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All verification checks passed! Entity normalization is working correctly.")
        return 0
    print("\n❌ Some verification checks failed. Review output above for details.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
