#!/usr/bin/env python3
"""
Test script to verify News API limit validation fix
Tests that the /api/news/articles endpoint properly validates limit parameter
"""

import sys

import requests


API_BASE = "http://localhost:8000"

def test_limit_validation():
    """Test that limit > 100 returns 422 error"""
    print("Testing News API limit validation...\n")

    # Test 1: Valid limit (should succeed)
    print("Test 1: Valid limit=100")
    response = requests.get(f"{API_BASE}/api/news/articles?limit=100")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Received {len(data.get('articles', []))} articles")
        print(f"   Total available: {data.get('total', 0)}")
    else:
        print(f"❌ Failed: Status {response.status_code}")
        return False

    # Test 2: Invalid limit (should return 422)
    print("\nTest 2: Invalid limit=1000 (exceeds max)")
    response = requests.get(f"{API_BASE}/api/news/articles?limit=1000")
    if response.status_code == 422:
        print(f"✅ Correctly rejected: Status {response.status_code}")
        error_detail = response.json().get("detail", [])
        if error_detail:
            print(f"   Error: {error_detail[0].get('msg', 'Unknown error')}")
    else:
        print(f"❌ Unexpected status: {response.status_code}")
        return False

    # Test 3: Pagination (limit=100, offset=0)
    print("\nTest 3: Pagination with limit=100, offset=0")
    response = requests.get(f"{API_BASE}/api/news/articles?limit=100&offset=0")
    if response.status_code == 200:
        data = response.json()
        articles_count = len(data.get("articles", []))
        total = data.get("total", 0)
        print(f"✅ Success: Received {articles_count} articles")
        print(f"   Total available: {total}")
        print(f"   Can fetch remaining: {total - articles_count} articles with offset=100")
    else:
        print(f"❌ Failed: Status {response.status_code}")
        return False

    print("\n" + "="*60)
    print("✅ All tests passed! The 422 error fix is working correctly.")
    print("="*60)
    return True

def main():
    try:
        if not test_limit_validation():
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server at http://localhost:8000")
        print("   Make sure the backend server is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
