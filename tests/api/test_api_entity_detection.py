#!/usr/bin/env python3
"""Test Entity Detection via API

Tests the /api/documents/{doc_id}/summary endpoint to verify entity detection.

Usage:
    # Start server first: python3 server/app.py 8081
    python3 test_api_entity_detection.py
"""

import json
import time
import requests
from pathlib import Path


def test_summary_endpoint():
    """Test document summary endpoint with entity detection."""
    API_BASE_URL = "http://localhost:8081"

    # Load document index to find a test document
    doc_index_path = Path("data/metadata/all_documents_index.json")
    if not doc_index_path.exists():
        print("❌ Document index not found")
        return False

    with open(doc_index_path) as f:
        doc_data = json.load(f)

    documents = doc_data.get("documents", [])
    if not documents:
        print("❌ No documents found in index")
        return False

    # Find a document with OCR text
    test_doc = None
    for doc in documents[:100]:  # Check first 100 documents
        filename = doc.get("filename", "")
        if filename:
            base_name = filename.rsplit(".", 1)[0]
            ocr_path = Path(f"data/sources/house_oversight_nov2025/ocr_text/{base_name}.txt")
            if ocr_path.exists():
                # Check if it has decent length
                with open(ocr_path) as f:
                    text = f.read()
                    if len(text) > 1000:
                        test_doc = doc
                        break

    if not test_doc:
        print("❌ No suitable test document found with OCR text")
        return False

    doc_id = test_doc["id"]
    print(f"Testing with document: {test_doc.get('filename', doc_id)}")
    print(f"Document ID: {doc_id}")
    print()

    # Make API request
    url = f"{API_BASE_URL}/api/documents/{doc_id}/summary"

    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"API Response time: {elapsed_ms:.0f}ms")
        print(f"Status code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ API request failed: {response.text}")
            return False

        data = response.json()

        # Check response structure
        print("\nResponse structure:")
        print(f"  ✓ document_id: {data.get('document_id')}")
        print(f"  ✓ filename: {data.get('filename')}")
        print(f"  ✓ file_size: {data.get('file_size'):,} bytes")
        print(f"  ✓ has_ocr_text: {data.get('has_ocr_text')}")
        print(f"  ✓ full_text_length: {data.get('full_text_length'):,} chars")

        # Check detected entities
        detected_entities = data.get('detected_entities', [])
        print(f"\nDetected entities: {len(detected_entities)}")

        if detected_entities:
            print("\nTop detected entities:")
            for i, entity in enumerate(detected_entities[:10], 1):
                guid = entity.get('guid', 'N/A')
                name = entity.get('name', 'N/A')
                mentions = entity.get('mentions', 0)
                entity_type = entity.get('entity_type', 'N/A')
                print(f"{i:2d}. {name:<40} ({mentions:3d} mentions)")
                print(f"    GUID: {guid}")

            # Verify structure
            first_entity = detected_entities[0]
            required_fields = ['guid', 'name', 'mentions', 'entity_type']
            missing_fields = [field for field in required_fields if field not in first_entity]

            if missing_fields:
                print(f"\n❌ Missing required fields: {missing_fields}")
                return False

            print("\n✓ All entity fields present")

        else:
            print("  ℹ No entities detected in this document")

        # Check legacy entities_mentioned
        entities_mentioned = data.get('entities_mentioned', [])
        print(f"\nLegacy entities_mentioned: {len(entities_mentioned)}")

        # Performance check
        print(f"\nPerformance:")
        if elapsed_ms < 500:
            print(f"  ✓ PASS: {elapsed_ms:.0f}ms < 500ms target")
        else:
            print(f"  ⚠ SLOW: {elapsed_ms:.0f}ms >= 500ms target")

        return True

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Start server with: python3 server/app.py 8081")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("Document Summary API - Entity Detection Test")
    print("=" * 80)
    print()

    success = test_summary_endpoint()

    print()
    print("=" * 80)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 80)

    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
