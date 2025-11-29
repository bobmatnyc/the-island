#!/usr/bin/env python3
"""
Test script for /api/documents/{document_id}/ai-summary endpoint

Tests:
1. Small PDF summary generation
2. Large PDF summary generation
3. Caching verification (second call uses cache)
4. Error handling (invalid document ID)
"""

import json
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8081"
MASTER_INDEX = Path("/Users/masa/Projects/epstein/data/metadata/master_document_index.json")

# Credentials (update these)
USERNAME = "admin"
PASSWORD = "password"  # Update with actual password


def test_ai_summary():
    """Test the AI summary endpoint"""

    # Load master index to get test document hashes
    with open(MASTER_INDEX) as f:
        index_data = json.load(f)

    documents = index_data["documents"]

    # Find test documents
    small_doc = next((d for d in documents if d.get("size", 0) < 1_000_000 and d.get("size", 0) > 10_000), None)
    large_doc = next((d for d in documents if d.get("size", 0) > 5_000_000), None)

    if not small_doc:
        print("❌ No small PDF found for testing")
        return

    if not large_doc:
        print("⚠️  No large PDF found, will only test small PDF")

    print("=" * 80)
    print("AI SUMMARY ENDPOINT TEST")
    print("=" * 80)

    # Test 1: Small PDF - First call (generation)
    print("\n📄 TEST 1: Small PDF Summary Generation")
    print(f"Document: {small_doc['canonical_path']}")
    print(f"Size: {small_doc['size'] / 1024:.1f} KB")
    print(f"Hash: {small_doc['hash'][:32]}...")

    start_time = time.time()
    response = requests.get(
        f"{BASE_URL}/api/documents/{small_doc['hash']}/ai-summary",
        auth=(USERNAME, PASSWORD)
    )
    elapsed = time.time() - start_time

    print(f"Status: {response.status_code}")
    print(f"Time: {elapsed:.2f}s")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Summary generated successfully")
        print(f"   From cache: {data['from_cache']}")
        print(f"   Word count: {data['word_count']}")
        print(f"   Model: {data['summary_model']}")
        print(f"\n   Summary preview:")
        print(f"   {data['summary'][:200]}...")
    else:
        print(f"❌ Failed: {response.text}")
        return

    # Test 2: Small PDF - Second call (cached)
    print("\n📄 TEST 2: Small PDF Summary (Cached)")

    start_time = time.time()
    response2 = requests.get(
        f"{BASE_URL}/api/documents/{small_doc['hash']}/ai-summary",
        auth=(USERNAME, PASSWORD)
    )
    elapsed2 = time.time() - start_time

    print(f"Status: {response2.status_code}")
    print(f"Time: {elapsed2:.2f}s")

    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Cached summary retrieved successfully")
        print(f"   From cache: {data2['from_cache']}")
        print(f"   Speed improvement: {elapsed / elapsed2:.1f}x faster")

        # Verify it's the same summary
        if data2['summary'] == data['summary']:
            print(f"   ✅ Summary matches original")
        else:
            print(f"   ❌ Summary doesn't match!")
    else:
        print(f"❌ Failed: {response2.text}")

    # Test 3: Large PDF (if available)
    if large_doc:
        print(f"\n📄 TEST 3: Large PDF Summary Generation")
        print(f"Document: {large_doc['canonical_path']}")
        print(f"Size: {large_doc['size'] / 1024 / 1024:.1f} MB")
        print(f"Hash: {large_doc['hash'][:32]}...")

        start_time = time.time()
        response3 = requests.get(
            f"{BASE_URL}/api/documents/{large_doc['hash']}/ai-summary",
            auth=(USERNAME, PASSWORD),
            timeout=30  # Longer timeout for large files
        )
        elapsed3 = time.time() - start_time

        print(f"Status: {response3.status_code}")
        print(f"Time: {elapsed3:.2f}s")

        if response3.status_code == 200:
            data3 = response3.json()
            print(f"✅ Large PDF summary generated successfully")
            print(f"   From cache: {data3['from_cache']}")
            print(f"   Word count: {data3['word_count']}")
            print(f"\n   Summary preview:")
            print(f"   {data3['summary'][:200]}...")
        else:
            print(f"⚠️  Failed (expected for very large files): {response3.text[:100]}")

    # Test 4: Invalid document ID
    print(f"\n📄 TEST 4: Invalid Document ID (Error Handling)")

    response4 = requests.get(
        f"{BASE_URL}/api/documents/invalid_hash_12345/ai-summary",
        auth=(USERNAME, PASSWORD)
    )

    print(f"Status: {response4.status_code}")

    if response4.status_code == 404:
        print(f"✅ Correctly returned 404 for invalid document")
    else:
        print(f"❌ Expected 404, got {response4.status_code}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_ai_summary()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running on http://localhost:8081?")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
