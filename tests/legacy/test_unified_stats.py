#!/usr/bin/env python3
"""
Test script for unified statistics endpoint
Verifies functionality, performance, and error handling
"""

import time

import requests


BASE_URL = "http://localhost:8000"
STATS_ENDPOINT = f"{BASE_URL}/api/v2/stats"


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_basic_request():
    """Test 1: Basic request with cache enabled."""
    print_section("TEST 1: Basic Request (with cache)")

    start = time.time()
    response = requests.get(STATS_ENDPOINT)
    elapsed = (time.time() - start) * 1000

    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"Overall Status: {data['status']}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Cache Hit: {data['cache']['hit']}")
        print("\nAvailable Sections:")
        for section, values in data["data"].items():
            status = "✓" if values else "✗"
            print(f"  {status} {section}: {type(values).__name__}")

        # Check for errors
        if data.get("errors"):
            print("\nPartial Failures:")
            for error in data["errors"]:
                print(f"  - {error['source']}: {error['message']}")

        return True
    print(f"ERROR: {response.text}")
    return False


def test_cache_functionality():
    """Test 2: Verify cache works correctly."""
    print_section("TEST 2: Cache Functionality")

    # First request (cache miss)
    print("Request 1 (cache miss expected):")
    start = time.time()
    response1 = requests.get(STATS_ENDPOINT)
    elapsed1 = (time.time() - start) * 1000
    data1 = response1.json()
    print(f"  Response Time: {elapsed1:.2f}ms")
    print(f"  Cache Hit: {data1['cache']['hit']}")

    # Second request (cache hit)
    print("\nRequest 2 (cache hit expected):")
    start = time.time()
    response2 = requests.get(STATS_ENDPOINT)
    elapsed2 = (time.time() - start) * 1000
    data2 = response2.json()
    print(f"  Response Time: {elapsed2:.2f}ms")
    print(f"  Cache Hit: {data2['cache']['hit']}")

    # Performance check
    speedup = elapsed1 / elapsed2 if elapsed2 > 0 else 0
    print(f"\nSpeedup: {speedup:.1f}x faster (cached vs uncached)")

    if data2["cache"]["hit"] and elapsed2 < elapsed1:
        print("✓ Cache working correctly")
        return True
    print("✗ Cache not working as expected")
    return False


def test_fresh_data():
    """Test 3: Bypass cache to get fresh data."""
    print_section("TEST 3: Fresh Data (use_cache=false)")

    start = time.time()
    response = requests.get(STATS_ENDPOINT, params={"use_cache": False})
    elapsed = (time.time() - start) * 1000

    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {elapsed:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"Cache Hit: {data['cache']['hit']}")

        if not data["cache"]["hit"]:
            print("✓ Successfully bypassed cache")
            return True
        print("✗ Cache was used despite use_cache=false")
        return False
    print(f"ERROR: {response.text}")
    return False


def test_section_filtering():
    """Test 4: Request specific sections only."""
    print_section("TEST 4: Section Filtering")

    # Test multiple section combinations
    test_cases = [
        ["documents", "timeline"],
        ["entities", "flights"],
        ["news"],
        ["documents", "news", "timeline", "entities"]
    ]

    for sections in test_cases:
        sections_param = ",".join(sections)
        print(f"\nRequesting sections: {sections_param}")

        response = requests.get(STATS_ENDPOINT, params={"sections": sections_param})

        if response.status_code == 200:
            data = response.json()
            returned_sections = list(data["data"].keys())
            print(f"  Returned sections: {returned_sections}")

            if set(returned_sections) == set(sections):
                print("  ✓ Correct sections returned")
            else:
                print("  ✗ Section mismatch")
                return False
        else:
            print(f"  ERROR: {response.text}")
            return False

    print("\n✓ All section filtering tests passed")
    return True


def test_data_completeness():
    """Test 5: Verify data structure and completeness."""
    print_section("TEST 5: Data Completeness")

    response = requests.get(STATS_ENDPOINT, params={"use_cache": False})

    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return False

    data = response.json()

    # Check documents section
    if data["data"].get("documents"):
        docs = data["data"]["documents"]
        print("Documents:")
        print(f"  Total: {docs.get('total', 0)}")
        print(f"  Court Documents: {docs.get('court_documents', 0)}")
        print(f"  Sources: {docs.get('sources', 0)}")

    # Check timeline section
    if data["data"].get("timeline"):
        timeline = data["data"]["timeline"]
        print("\nTimeline:")
        print(f"  Total Events: {timeline.get('total_events', 0)}")
        print(f"  Date Range: {timeline.get('date_range', {})}")

    # Check entities section
    if data["data"].get("entities"):
        entities = data["data"]["entities"]
        print("\nEntities:")
        print(f"  Total: {entities.get('total', 0)}")
        print(f"  With Biographies: {entities.get('with_biographies', 0)}")
        print(f"  Types: {entities.get('types', {})}")

    # Check flights section
    if data["data"].get("flights"):
        flights = data["data"]["flights"]
        print("\nFlights:")
        print(f"  Total: {flights.get('total', 0)}")
        print(f"  Unique Passengers: {flights.get('unique_passengers', 0)}")
        print(f"  Date Range: {flights.get('date_range', {})}")

    # Check news section
    if data["data"].get("news"):
        news = data["data"]["news"]
        print("\nNews:")
        print(f"  Total Articles: {news.get('total_articles', 0)}")
        print(f"  Sources: {news.get('sources', 0)}")
        print(f"  Date Range: {news.get('date_range', {})}")

    # Check network section
    if data["data"].get("network"):
        network = data["data"]["network"]
        print("\nNetwork:")
        print(f"  Nodes: {network.get('nodes', 0)}")
        print(f"  Edges: {network.get('edges', 0)}")
        print(f"  Average Degree: {network.get('avg_degree', 0)}")

    # Check vector_store section
    if data["data"].get("vector_store"):
        vector = data["data"]["vector_store"]
        print("\nVector Store:")
        print(f"  Total Documents: {vector.get('total_documents', 0)}")
        print(f"  Court Documents: {vector.get('court_documents', 0)}")
        print(f"  News Articles: {vector.get('news_articles', 0)}")

    print("\n✓ Data structure looks good")
    return True


def test_performance():
    """Test 6: Performance benchmarks."""
    print_section("TEST 6: Performance Benchmarks")

    # Test cached performance (10 requests)
    print("Testing cached performance (10 requests)...")
    cached_times = []
    for _i in range(10):
        start = time.time()
        requests.get(STATS_ENDPOINT)
        elapsed = (time.time() - start) * 1000
        cached_times.append(elapsed)

    avg_cached = sum(cached_times) / len(cached_times)
    min_cached = min(cached_times)
    max_cached = max(cached_times)

    print(f"  Average: {avg_cached:.2f}ms")
    print(f"  Min: {min_cached:.2f}ms")
    print(f"  Max: {max_cached:.2f}ms")

    # Test fresh data performance (3 requests)
    print("\nTesting fresh data performance (3 requests)...")
    fresh_times = []
    for _i in range(3):
        start = time.time()
        requests.get(STATS_ENDPOINT, params={"use_cache": False})
        elapsed = (time.time() - start) * 1000
        fresh_times.append(elapsed)

    avg_fresh = sum(fresh_times) / len(fresh_times)
    min_fresh = min(fresh_times)
    max_fresh = max(fresh_times)

    print(f"  Average: {avg_fresh:.2f}ms")
    print(f"  Min: {min_fresh:.2f}ms")
    print(f"  Max: {max_fresh:.2f}ms")

    # Performance targets
    print("\nPerformance Targets:")
    cached_ok = avg_cached < 50
    fresh_ok = avg_fresh < 500

    print(f"  Cached < 50ms: {'✓' if cached_ok else '✗'} ({avg_cached:.2f}ms)")
    print(f"  Fresh < 500ms: {'✓' if fresh_ok else '✗'} ({avg_fresh:.2f}ms)")

    return cached_ok and fresh_ok


def test_cache_clear():
    """Test 7: Cache clearing endpoint."""
    print_section("TEST 7: Cache Clear Endpoint")

    # Clear cache
    response = requests.post(f"{BASE_URL}/api/v2/stats/cache/clear")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Message: {data['message']}")
        print("✓ Cache cleared successfully")
        return True
    print(f"ERROR: {response.text}")
    return False


def main():
    """Run all tests."""
    print_section("UNIFIED STATISTICS ENDPOINT TEST SUITE")
    print(f"Target: {STATS_ENDPOINT}")

    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/api/stats")
        print("✓ Server is running")
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running")
        print("\nPlease start the server first:")
        print("  cd server && python3 app.py")
        return

    # Run tests
    results = {
        "Basic Request": test_basic_request(),
        "Cache Functionality": test_cache_functionality(),
        "Fresh Data": test_fresh_data(),
        "Section Filtering": test_section_filtering(),
        "Data Completeness": test_data_completeness(),
        "Performance": test_performance(),
        "Cache Clear": test_cache_clear()
    }

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
