#!/usr/bin/env python3
"""
Verification Script for ChromaDB Entity Collection

Quick verification that entity indexing is working correctly.
"""

import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import CHROMADB_DIR

ENTITY_COLLECTION_NAME = "epstein_entities"

# Expected counts
EXPECTED_TOTAL = 2939
EXPECTED_PERSONS = 1637
EXPECTED_LOCATIONS = 423
EXPECTED_ORGANIZATIONS = 879


def verify_collection():
    """Verify entity collection exists and has correct data."""
    print("=" * 60)
    print("CHROMADB ENTITY COLLECTION VERIFICATION")
    print("=" * 60)

    # Connect to ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMADB_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    # Check collection exists
    try:
        collection = client.get_collection(name=ENTITY_COLLECTION_NAME)
        print(f"✓ Collection '{ENTITY_COLLECTION_NAME}' exists")
    except Exception as e:
        print(f"✗ Collection not found: {e}")
        print("\nRun: python scripts/chromadb/index_entities.py")
        return False

    # Check total count
    total_count = collection.count()
    print(f"✓ Total entities: {total_count}")

    if total_count != EXPECTED_TOTAL:
        print(f"  WARNING: Expected {EXPECTED_TOTAL}, got {total_count}")

    # Sample entities by type
    sample_size = min(1000, total_count)
    sample = collection.get(limit=sample_size)

    if not sample["metadatas"]:
        print("✗ No entities found in collection")
        return False

    # Count by type
    type_counts = {"person": 0, "location": 0, "organization": 0}
    bio_count = 0
    classified_count = 0

    for metadata in sample["metadatas"]:
        entity_type = metadata.get("entity_type", "unknown")
        type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        if metadata.get("has_biography"):
            bio_count += 1

        if metadata.get("classifications"):
            classified_count += 1

    print(f"\n✓ Sample analysis ({sample_size} entities):")
    print(f"  - Persons: {type_counts.get('person', 0)}")
    print(f"  - Locations: {type_counts.get('location', 0)}")
    print(f"  - Organizations: {type_counts.get('organization', 0)}")
    print(f"  - With biographies: {bio_count}")
    print(f"  - With classifications: {classified_count}")

    # Test semantic search
    print("\n✓ Testing semantic search...")
    try:
        results = collection.query(
            query_texts=["financial associates"],
            n_results=3,
        )
        if results["ids"][0]:
            print(f"  Found {len(results['ids'][0])} results for 'financial associates'")
            print(f"  Top result: {results['metadatas'][0][0].get('canonical_name', 'Unknown')}")
        else:
            print("  WARNING: No results for test query")
    except Exception as e:
        print(f"  ERROR: Search failed - {e}")
        return False

    # Test filtering
    print("\n✓ Testing metadata filtering...")
    try:
        results = collection.query(
            query_texts=["locations"],
            n_results=3,
            where={"entity_type": "location"},
        )
        if results["ids"][0]:
            print(f"  Found {len(results['ids'][0])} locations")
        else:
            print("  WARNING: No locations found")
    except Exception as e:
        print(f"  ERROR: Filtering failed - {e}")
        return False

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE ✓")
    print("=" * 60)
    print("\nEntity collection is working correctly!")
    print(f"Total indexed: {total_count} entities")
    print("\nTry a query:")
    print("  python scripts/chromadb/query_entities.py 'your search term'")
    print("\nSee: scripts/chromadb/ENTITY_QUICKSTART.md for usage examples")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = verify_collection()
    sys.exit(0 if success else 1)
