#!/usr/bin/env python3
"""
Test biography API endpoint with newly imported Grok biographies.

This script verifies that the database migration was successful and that
the API can retrieve the newly imported biographies.

Usage:
    python3 tests/verification/test_biography_api_grok.py
"""

import requests
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

API_BASE = "http://localhost:8081/api"

# Sample entities from Grok import
TEST_ENTITIES = [
    ("christopher_tucker", "Christopher Tucker", 214),
    ("casey", "Casey", 257),
    ("david_slang", "Slang, David", 250),
    ("karina_matson", "Karina Matson", 293),
    ("gary_roxbury", "Gary Roxbury", 273)
]

def test_biography_endpoint(entity_id: str, expected_name: str, expected_words: int):
    """Test biography endpoint for a specific entity."""
    url = f"{API_BASE}/entities/{entity_id}/biography"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            print(f"❌ {entity_id}: HTTP {response.status_code}")
            return False

        data = response.json()

        # Verify structure
        if "biography" not in data:
            print(f"❌ {entity_id}: No biography in response")
            return False

        bio = data["biography"]

        # Verify fields
        checks = {
            "summary": bio.get("summary", ""),
            "quality_score": bio.get("quality_score", 0),
            "word_count": bio.get("word_count", 0),
            "model_used": bio.get("model_used", ""),
        }

        # Validate content
        if not checks["summary"]:
            print(f"❌ {entity_id}: Empty summary")
            return False

        if checks["quality_score"] < 0.9:
            print(f"⚠️  {entity_id}: Low quality score ({checks['quality_score']})")

        if abs(checks["word_count"] - expected_words) > 10:
            print(f"⚠️  {entity_id}: Word count mismatch (expected ~{expected_words}, got {checks['word_count']})")

        if checks["model_used"] != "grok-4.1-fast":
            print(f"⚠️  {entity_id}: Unexpected model ({checks['model_used']})")

        print(f"✅ {entity_id}: {expected_name}")
        print(f"   Quality: {checks['quality_score']:.2f}, Words: {checks['word_count']}, Model: {checks['model_used']}")
        print(f"   Preview: {checks['summary'][:100]}...")
        print()

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ {entity_id}: Request failed - {e}")
        return False
    except Exception as e:
        print(f"❌ {entity_id}: Unexpected error - {e}")
        return False

def main():
    """Run all tests."""
    print("="*70)
    print("BIOGRAPHY API TEST - GROK IMPORT VERIFICATION")
    print("="*70)
    print()

    # Test if backend is running
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        print(f"✓ Backend is running (HTTP {response.status_code})")
        print()
    except requests.exceptions.RequestException:
        print("❌ Backend is not running. Please start the backend first:")
        print("   cd /Users/masa/Projects/epstein")
        print("   source .venv/bin/activate")
        print("   python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload")
        print()
        sys.exit(1)

    # Run tests
    passed = 0
    failed = 0

    for entity_id, expected_name, expected_words in TEST_ENTITIES:
        if test_biography_endpoint(entity_id, expected_name, expected_words):
            passed += 1
        else:
            failed += 1

    # Summary
    print("="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)

    if failed > 0:
        print()
        print("⚠️  Some tests failed. The backend may need a restart:")
        print("   pkill -f 'uvicorn.*app:app' && sleep 2")
        print("   python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload")
        sys.exit(1)
    else:
        print()
        print("✅ All tests passed! The migration was successful.")
        sys.exit(0)

if __name__ == "__main__":
    main()
