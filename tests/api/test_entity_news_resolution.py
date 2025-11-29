#!/usr/bin/env python3
"""
Test script to verify entity name resolution bug fix in NewsService

Tests that all entity name formats return the same results:
- entity ID format: "jeffrey_epstein"
- canonical format: "Epstein, Jeffrey"
- display format: "Jeffrey Epstein"

Success Criteria:
✅ All formats return same total count
✅ All formats return same articles
✅ Case-insensitive matching works
✅ Backend logs show name normalization
"""

import requests
import json
from typing import Dict, List

API_BASE_URL = "http://localhost:8081"

def test_entity_search(entity_param: str) -> Dict:
    """Test news search with specific entity parameter"""
    url = f"{API_BASE_URL}/api/news/articles"
    params = {"entity": entity_param, "limit": 5}

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    return {
        "total": data["total"],
        "returned": len(data["articles"]),
        "first_title": data["articles"][0]["title"] if data["articles"] else None,
        "article_ids": [a["id"] for a in data["articles"]]
    }

def main():
    print("=" * 80)
    print("ENTITY NAME RESOLUTION TEST")
    print("=" * 80)

    test_cases = [
        ("jeffrey_epstein", "Entity ID format (underscore)"),
        ("Epstein, Jeffrey", "Canonical format (Last, First)"),
        ("Jeffrey Epstein", "Display format (First Last)"),
        ("JEFFREY EPSTEIN", "Uppercase test"),
        ("epstein, jeffrey", "Lowercase canonical"),
    ]

    results = []

    for entity_param, description in test_cases:
        print(f"\n📋 Test: {description}")
        print(f"   Parameter: {entity_param}")

        try:
            result = test_entity_search(entity_param)
            results.append((entity_param, result))

            print(f"   ✅ Total articles: {result['total']}")
            print(f"   ✅ Returned: {result['returned']}")
            print(f"   ✅ First article: {result['first_title'][:60]}...")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    # Verify all formats return same count
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    totals = [r[1]["total"] for r in results]
    first_ids = [r[1]["article_ids"] for r in results]

    if len(set(totals)) == 1:
        print(f"✅ All formats return same total: {totals[0]} articles")
    else:
        print(f"❌ FAIL: Different totals returned: {totals}")
        return False

    # Verify same articles returned (first 5)
    if all(ids == first_ids[0] for ids in first_ids):
        print(f"✅ All formats return same articles (same order)")
    else:
        print(f"❌ FAIL: Different articles returned for different formats")
        return False

    print("\n" + "=" * 80)
    print("SUCCESS: Entity name resolution working correctly!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   - Total articles for 'Jeffrey Epstein': {totals[0]}")
    print(f"   - All name formats supported: ✅")
    print(f"   - Case-insensitive matching: ✅")
    print(f"   - Consistent results: ✅")

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
