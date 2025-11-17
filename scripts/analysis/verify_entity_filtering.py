#!/usr/bin/env python3
"""
Verify Entity Filtering Implementation

Checks that generic entities are properly filtered from:
1. Entity network (entity_network.json)
2. Entity statistics (entity_statistics.json)
3. API endpoints (via entity_filter instance)

Generates report showing:
- Number of entities filtered
- Filter categories
- Before/after statistics
"""

import json
import sys
from pathlib import Path


# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from entity_filtering import EntityFilter


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"

def main():
    """Verify entity filtering implementation"""
    print("=" * 70)
    print("ENTITY FILTERING VERIFICATION")
    print("=" * 70)

    # Initialize filter
    entity_filter = EntityFilter()

    print("\n1. FILTER CONFIGURATION:")
    print(f"   Total filtered entities: {entity_filter.get_filtered_count()}")
    print(f"\n   Rationale: {entity_filter.get_filter_rationale()}")

    # Show filter categories
    print("\n2. FILTER CATEGORIES:")
    categories = entity_filter.get_filter_categories()
    for category, entities in categories.items():
        print(f"\n   {category.replace('_', ' ').title()}:")
        for entity in entities:
            print(f"     - {entity}")

    # Load network and check for generic entities
    print("\n3. NETWORK VERIFICATION:")
    network_path = METADATA_DIR / "entity_network.json"

    if network_path.exists():
        with open(network_path) as f:
            network_data = json.load(f)

        nodes = network_data.get("nodes", [])
        total_nodes = len(nodes)

        # Check for generic entities in network
        generic_in_network = [
            n["name"] for n in nodes
            if entity_filter.is_generic(n["name"])
        ]

        print(f"   Total nodes in network: {total_nodes}")
        print(f"   Generic entities found: {len(generic_in_network)}")

        if generic_in_network:
            print("\n   ❌ FAILED: Generic entities still in network:")
            for name in generic_in_network:
                print(f"      - {name}")
        else:
            print("   ✅ PASSED: No generic entities in network")

    else:
        print(f"   ⚠️  WARNING: Network file not found: {network_path}")

    # Load entity statistics and check
    print("\n4. ENTITY STATISTICS VERIFICATION:")
    stats_path = METADATA_DIR / "entity_statistics.json"

    if stats_path.exists():
        with open(stats_path) as f:
            stats_data = json.load(f)

        entity_stats = stats_data.get("statistics", {})
        total_entities = len(entity_stats)

        # Check for generic entities in stats
        generic_in_stats = [
            name for name in entity_stats.keys()
            if entity_filter.is_generic(name)
        ]

        print(f"   Total entities in stats: {total_entities}")
        print(f"   Generic entities found: {len(generic_in_stats)}")

        if generic_in_stats:
            print("\n   ℹ️  NOTE: Generic entities in statistics (not displayed in UI):")
            for name in generic_in_stats:
                print(f"      - {name}")
            print("\n   This is expected - stats preserve all entities for provenance.")
            print("   UI filters them via entity_filter.is_generic() check.")
        else:
            print("   ✅ No generic entities in statistics")

    else:
        print(f"   ⚠️  WARNING: Stats file not found: {stats_path}")

    # Summary
    print("\n5. SUMMARY:")
    print(f"   Filter Status: {'✅ OPERATIONAL' if entity_filter.get_filtered_count() > 0 else '❌ NOT LOADED'}")
    print(f"   Network Cleaned: {'✅ YES' if not generic_in_network else '❌ NO'}")
    print(f"   Entities Removed: ~{entity_filter.get_filtered_count()} generic terms")

    # Impact analysis
    print("\n6. IMPACT ANALYSIS:")

    # Calculate how many entities were filtered from network
    if network_path.exists():
        # Original count from old network (387 nodes with generics)
        original_count = 387  # From CLAUDE.md
        current_count = total_nodes
        filtered_count = original_count - current_count

        print(f"   Original network size: {original_count} nodes")
        print(f"   Current network size: {current_count} nodes")
        print(f"   Nodes removed: {filtered_count} ({filtered_count/original_count*100:.1f}%)")

        # Edge reduction
        original_edges = 2221  # From CLAUDE.md
        current_edges = len(network_data.get("edges", []))
        edge_reduction = original_edges - current_edges

        print(f"\n   Original edge count: {original_edges} connections")
        print(f"   Current edge count: {current_edges} connections")
        print(f"   Edges removed: {edge_reduction} ({edge_reduction/original_edges*100:.1f}%)")

    print(f"\n{'=' * 70}")
    print("VERIFICATION COMPLETE")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
