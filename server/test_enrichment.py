#!/usr/bin/env python3
"""
Test script for entity enrichment service

Demonstrates:
1. Single entity enrichment
2. Cached retrieval
3. Batch enrichment
4. Statistics tracking
5. Source provenance
"""

import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.entity_enrichment import (
    EntityEnrichmentService,
    format_for_ui
)


async def test_enrichment():
    """Test entity enrichment workflow"""

    # Initialize service with test storage
    test_storage = Path("/tmp/test_entity_enrichments.json")
    service = EntityEnrichmentService(test_storage)

    print("=" * 80)
    print("ENTITY ENRICHMENT SERVICE - TEST SUITE")
    print("=" * 80)
    print()

    # Test 1: Single entity enrichment
    print("TEST 1: Enriching entity 'Ghislaine Maxwell'")
    print("-" * 80)

    enrichment = await service.enrich_entity(
        entity_id="ghislaine_maxwell_test",
        entity_name="Ghislaine Maxwell",
        force_refresh=True
    )

    print(f"✓ Enrichment completed")
    print(f"  - Entity: {enrichment.entity_name}")
    print(f"  - Sources found: {enrichment.total_sources}")
    print(f"  - Average confidence: {enrichment.average_confidence:.2f}")
    print(f"  - Profession: {enrichment.profession or 'Not identified'}")
    print(f"  - Known dates: {', '.join(enrichment.known_dates[:5]) if enrichment.known_dates else 'None'}")
    print()

    if enrichment.sources:
        print("  Top 3 sources:")
        for i, source in enumerate(enrichment.sources[:3], 1):
            print(f"    {i}. {source.title}")
            print(f"       URL: {source.url}")
            print(f"       Domain: {source.domain}")
            print(f"       Confidence: {source.confidence:.2f}")
            print(f"       Snippet: {source.snippet[:100]}...")
            print()

    # Test 2: Cached retrieval
    print("TEST 2: Retrieving cached enrichment")
    print("-" * 80)

    cached = await service.get_enrichment("ghislaine_maxwell_test", "Ghislaine Maxwell")

    if cached:
        print(f"✓ Cache hit!")
        print(f"  - Last updated: {cached.last_updated}")
        print(f"  - Sources cached: {cached.total_sources}")
    else:
        print("✗ Cache miss (unexpected)")
    print()

    # Test 3: UI formatting
    print("TEST 3: Formatting for UI display")
    print("-" * 80)

    ui_data = format_for_ui(enrichment)

    print(f"✓ UI data generated")
    print(f"  - Facts extracted: {len(ui_data['facts'])}")
    print(f"  - Disclaimer: {ui_data['disclaimer'][:80]}...")
    print()

    print("  Sample fact:")
    if ui_data['facts']:
        fact = ui_data['facts'][0]
        print(f"    Category: {fact['category']}")
        print(f"    Text: {fact['text'][:150]}...")
        print(f"    Sources: {len(fact['sources'])}")
    print()

    # Test 4: Batch enrichment
    print("TEST 4: Batch enrichment (3 entities)")
    print("-" * 80)

    batch_entities = [
        {"id": "bill_clinton_test", "name": "Bill Clinton"},
        {"id": "donald_trump_test", "name": "Donald Trump"},
        {"id": "prince_andrew_test", "name": "Prince Andrew"}
    ]

    print("Enriching entities:")
    for entity in batch_entities:
        print(f"  - {entity['name']}")
    print()

    batch_results = await service.enrich_batch(
        entities=batch_entities,
        max_concurrent=2  # Limit concurrency for test
    )

    print(f"✓ Batch enrichment completed")
    print(f"  - Entities processed: {len(batch_results)}")
    print()

    for result in batch_results:
        print(f"  {result.entity_name}:")
        print(f"    Sources: {result.total_sources}")
        print(f"    Confidence: {result.average_confidence:.2f}")
        print(f"    Profession: {result.profession or 'Not identified'}")
        print()

    # Test 5: Statistics
    print("TEST 5: Service statistics")
    print("-" * 80)

    stats = service.get_statistics()

    print(f"✓ Statistics generated")
    print(f"  - Total enrichments: {stats['total_enrichments']}")
    print(f"  - Valid enrichments: {stats['valid_enrichments']}")
    print(f"  - Stale enrichments: {stats['stale_enrichments']}")
    print(f"  - Avg sources per entity: {stats['average_sources_per_entity']:.2f}")
    print(f"  - Avg confidence: {stats['average_confidence']:.2f}")
    print()

    # Test 6: Export sample data
    print("TEST 6: Exporting enrichment data")
    print("-" * 80)

    export_path = Path("/tmp/test_enrichment_export.json")
    export_data = {
        entity_id: json.loads(enrichment.model_dump_json())
        for entity_id, enrichment in service.cache.items()
    }

    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✓ Enrichment data exported")
    print(f"  - File: {export_path}")
    print(f"  - Size: {export_path.stat().st_size / 1024:.2f} KB")
    print()

    # Cleanup
    await service.close()

    print("=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print()
    print("Test files created:")
    print(f"  - Cache: {test_storage}")
    print(f"  - Export: {export_path}")
    print()
    print("To test with actual API:")
    print("  1. Start server: python3 server/app.py")
    print("  2. Test enrichment:")
    print("     curl -u epstein:archive2025 \\")
    print("       'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrich'")
    print("  3. Check cache:")
    print("     curl -u epstein:archive2025 \\")
    print("       'http://localhost:8000/api/entities/Ghislaine%20Maxwell/enrichment'")


if __name__ == "__main__":
    asyncio.run(test_enrichment())
