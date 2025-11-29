#!/usr/bin/env python3
"""
Advanced Search QA Testing Script
Tests all advanced search functionality with performance metrics
"""

import json
import time
from datetime import datetime
from typing import Any, Optional

import requests


API_BASE_URL = "http://localhost:8000"
RESULTS_FILE = "/Users/masa/Projects/epstein/qa_search_results.json"

# Performance tracking
test_results = {
    "timestamp": datetime.utcnow().isoformat(),
    "performance_tests": [],
    "functional_tests": [],
    "errors": [],
    "summary": {}
}

def measure_request(name: str, url: str, params: Optional[dict] = None) -> dict[str, Any]:
    """Make a timed API request and return results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    if params:
        print(f"Params: {json.dumps(params, indent=2)}")

    start_time = time.time()

    try:
        response = requests.get(url, params=params, timeout=5)
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed_ms:.2f}ms")

        if response.ok:
            data = response.json()
            print(f"Results: {data.get('total_results', len(data)) if isinstance(data, dict) else len(data)} items")

            return {
                "name": name,
                "status": "success",
                "status_code": response.status_code,
                "time_ms": elapsed_ms,
                "data": data
            }
        print(f"Error: {response.text}")
        return {
            "name": name,
            "status": "failed",
            "status_code": response.status_code,
            "time_ms": elapsed_ms,
            "error": response.text
        }

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"Exception: {e!s}")
        return {
            "name": name,
            "status": "error",
            "time_ms": elapsed_ms,
            "error": str(e)
        }


def test_1_simple_entity_search():
    """Test 1: Simple entity name search."""
    result = measure_request(
        "Simple Entity Search - Epstein",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Epstein", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_2_multi_word_search():
    """Test 2: Multi-word entity search."""
    result = measure_request(
        "Multi-word Search - Ghislaine Maxwell",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Ghislaine Maxwell", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_3_boolean_and():
    """Test 3: Boolean AND operator."""
    result = measure_request(
        "Boolean AND - Epstein AND Maxwell",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Epstein AND Maxwell", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_4_fuzzy_typo():
    """Test 4: Fuzzy matching with typo."""
    result = measure_request(
        "Fuzzy Match - Ghisline (typo)",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Ghisline", "limit": 20, "fuzzy": "true"}
    )
    test_results["performance_tests"].append(result)
    return result


def test_5_date_filter():
    """Test 5: Search with date filter."""
    result = measure_request(
        "Date Filter - 2000-2010",
        f"{API_BASE_URL}/api/search/unified",
        params={
            "query": "flight",
            "date_start": "2000-01-01",
            "date_end": "2010-12-31",
            "limit": 20
        }
    )
    test_results["performance_tests"].append(result)
    return result


def test_6_entity_only_search():
    """Test 6: Entity-only field search."""
    result = measure_request(
        "Entity-only Search - Prince",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Prince", "fields": "entities", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_7_document_search():
    """Test 7: Document-only search."""
    result = measure_request(
        "Document Search - deposition",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "deposition", "fields": "documents", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_8_news_search():
    """Test 8: News article search."""
    result = measure_request(
        "News Search - investigation",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "investigation", "fields": "news", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_9_boolean_or():
    """Test 9: Boolean OR operator."""
    result = measure_request(
        "Boolean OR - Clinton OR Trump",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Clinton OR Trump", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_10_boolean_not():
    """Test 10: Boolean NOT operator."""
    result = measure_request(
        "Boolean NOT - Epstein NOT Maxwell",
        f"{API_BASE_URL}/api/search/unified",
        params={"query": "Epstein NOT Maxwell", "limit": 20}
    )
    test_results["performance_tests"].append(result)
    return result


def test_autocomplete_suggestions():
    """Test autocomplete suggestions endpoint."""
    print(f"\n{'='*60}")
    print("Testing: Autocomplete Suggestions")

    test_queries = ["Eps", "Ghis", "Max", "Prin", "Clint"]

    for query in test_queries:
        result = measure_request(
            f"Autocomplete - '{query}'",
            f"{API_BASE_URL}/api/search/suggestions",
            params={"query": query, "limit": 10}
        )
        test_results["functional_tests"].append(result)


def test_fuzzy_matching_accuracy():
    """Test fuzzy matching with various typos."""
    print(f"\n{'='*60}")
    print("Testing: Fuzzy Matching Accuracy")

    typo_tests = [
        ("Ghisline", "Ghislaine"),
        ("Maxwel", "Maxwell"),
        ("Jeffry", "Jeffrey"),
        ("Clynton", "Clinton"),
        ("Andru", "Andrew")
    ]

    for typo, expected in typo_tests:
        result = measure_request(
            f"Fuzzy Match - '{typo}' → '{expected}'",
            f"{API_BASE_URL}/api/search/unified",
            params={"query": typo, "fuzzy": "true", "limit": 5}
        )

        # Check if expected term appears in results
        if result["status"] == "success":
            data = result["data"]
            results = data.get("results", [])
            found = any(expected.lower() in r.get("title", "").lower() for r in results)
            result["fuzzy_match_success"] = found
            result["expected_term"] = expected

        test_results["functional_tests"].append(result)


def test_analytics_endpoint():
    """Test search analytics endpoint."""
    result = measure_request(
        "Analytics Endpoint",
        f"{API_BASE_URL}/api/search/analytics"
    )
    test_results["functional_tests"].append(result)


def calculate_statistics():
    """Calculate performance statistics."""
    print(f"\n{'='*60}")
    print("PERFORMANCE STATISTICS")
    print("="*60)

    performance_times = [
        r["time_ms"] for r in test_results["performance_tests"]
        if r["status"] == "success"
    ]

    if performance_times:
        performance_times.sort()

        p50_idx = len(performance_times) // 2
        p95_idx = int(len(performance_times) * 0.95)

        stats = {
            "total_tests": len(test_results["performance_tests"]),
            "successful_tests": len(performance_times),
            "min_ms": min(performance_times),
            "max_ms": max(performance_times),
            "avg_ms": sum(performance_times) / len(performance_times),
            "p50_ms": performance_times[p50_idx],
            "p95_ms": performance_times[p95_idx],
            "under_300ms": sum(1 for t in performance_times if t < 300),
            "under_500ms": sum(1 for t in performance_times if t < 500),
            "under_1000ms": sum(1 for t in performance_times if t < 1000),
        }

        test_results["summary"] = stats

        print(f"Total Tests: {stats['total_tests']}")
        print(f"Successful: {stats['successful_tests']}")
        print("\nLatency Statistics:")
        print(f"  Min: {stats['min_ms']:.2f}ms")
        print(f"  P50: {stats['p50_ms']:.2f}ms")
        print(f"  P95: {stats['p95_ms']:.2f}ms")
        print(f"  Max: {stats['max_ms']:.2f}ms")
        print(f"  Avg: {stats['avg_ms']:.2f}ms")
        print("\nPerformance Goals:")
        print(f"  < 300ms (p50 goal): {stats['under_300ms']}/{stats['total_tests']} ✓" if stats["p50_ms"] < 300 else f"  < 300ms (p50 goal): {stats['p50_ms']:.2f}ms ✗")
        print(f"  < 500ms (p95 goal): {stats['under_500ms']}/{stats['total_tests']} ✓" if stats["p95_ms"] < 500 else f"  < 500ms (p95 goal): {stats['p95_ms']:.2f}ms ✗")
        print(f"  < 1000ms (all): {stats['under_1000ms']}/{stats['total_tests']} ✓" if stats["under_1000ms"] == stats["total_tests"] else f"  < 1000ms (all): {stats['under_1000ms']}/{stats['total_tests']} ✗")

        return stats

    return None


def main():
    """Run all tests."""
    print("="*60)
    print("ADVANCED SEARCH QA TEST SUITE")
    print("="*60)
    print(f"Target: {API_BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check API health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if not response.ok:
            print("\n❌ API is not responding. Please ensure the server is running.")
            return
    except Exception as e:
        print(f"\n❌ Cannot connect to API: {e}")
        print("Please ensure the server is running at http://localhost:8000")
        return

    print("\n✓ API is responding")

    # Run performance tests (10 different queries)
    print("\n" + "="*60)
    print("PART 1: PERFORMANCE TESTS (10 QUERIES)")
    print("="*60)

    test_1_simple_entity_search()
    test_2_multi_word_search()
    test_3_boolean_and()
    test_4_fuzzy_typo()
    test_5_date_filter()
    test_6_entity_only_search()
    test_7_document_search()
    test_8_news_search()
    test_9_boolean_or()
    test_10_boolean_not()

    # Run functional tests
    print("\n" + "="*60)
    print("PART 2: FUNCTIONAL TESTS")
    print("="*60)

    test_autocomplete_suggestions()
    test_fuzzy_matching_accuracy()
    test_analytics_endpoint()

    # Calculate statistics
    calculate_statistics()

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(test_results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results saved to: {RESULTS_FILE}")
    print("="*60)


if __name__ == "__main__":
    main()
