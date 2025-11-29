#!/usr/bin/env python3
"""
API Endpoint Test Script
Tests all API endpoints to verify data loading and functionality
"""

import json
import sys
from typing import Optional

import requests


# Server configuration
BASE_URL = "http://localhost:8081"
USERNAME = "epstein"
PASSWORD = "@rchiv*!2025"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def test_endpoint(
    name: str,
    endpoint: str,
    expected_keys: Optional[list[str]] = None,
    method: str = "GET",
    data: Optional[dict] = None
) -> bool:
    """Test a single API endpoint

    Args:
        name: Human-readable test name
        endpoint: API endpoint path
        expected_keys: Expected keys in response JSON
        method: HTTP method (GET, POST, etc.)
        data: Request body for POST/PUT

    Returns:
        True if test passed, False otherwise
    """
    url = f"{BASE_URL}{endpoint}"

    try:
        print(f"\n🔍 Testing: {name}")
        print(f"   URL: {url}")

        # Make request
        if method == "GET":
            response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)
        elif method == "POST":
            response = requests.post(
                url,
                auth=(USERNAME, PASSWORD),
                json=data,
                timeout=10
            )
        else:
            print(f"   {Colors.RED}✗ Unsupported method: {method}{Colors.RESET}")
            return False

        # Check status code
        if response.status_code in {200, 201}:
            print(f"   {Colors.GREEN}✓ Status: {response.status_code}{Colors.RESET}")
        else:
            print(f"   {Colors.RED}✗ Status: {response.status_code}{Colors.RESET}")
            print(f"   Response: {response.text[:200]}")
            return False

        # Parse JSON
        try:
            result = response.json()
        except json.JSONDecodeError:
            print(f"   {Colors.RED}✗ Invalid JSON response{Colors.RESET}")
            return False

        # Check expected keys
        if expected_keys:
            missing_keys = [k for k in expected_keys if k not in result]
            if missing_keys:
                print(f"   {Colors.RED}✗ Missing keys: {missing_keys}{Colors.RESET}")
                print(f"   Available keys: {list(result.keys())}")
                return False
            print(f"   {Colors.GREEN}✓ All expected keys present{Colors.RESET}")

        # Print summary statistics
        print(f"   {Colors.BLUE}📊 Response summary:{Colors.RESET}")
        for key, value in result.items():
            if isinstance(value, (list, dict)):
                print(f"      {key}: {len(value)} items")
            elif isinstance(value, (int, float)):
                print(f"      {key}: {value}")
            else:
                print(f"      {key}: {str(value)[:50]}")

        return True

    except requests.exceptions.Timeout:
        print(f"   {Colors.RED}✗ Request timeout{Colors.RESET}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   {Colors.RED}✗ Connection error - is server running?{Colors.RESET}")
        return False
    except Exception as e:
        print(f"   {Colors.RED}✗ Error: {e}{Colors.RESET}")
        return False


def main():
    """Run all endpoint tests"""
    print("=" * 70)
    print("EPSTEIN ARCHIVE API ENDPOINT TESTS")
    print("=" * 70)
    print(f"Server: {BASE_URL}")
    print(f"Auth: {USERNAME}")

    tests = [
        # Core statistics
        {
            "name": "Get overall statistics",
            "endpoint": "/api/stats",
            "expected_keys": ["total_entities", "total_documents", "network_nodes", "network_edges"]
        },

        # Ingestion status
        {
            "name": "Get ingestion status",
            "endpoint": "/api/ingestion/status",
            "expected_keys": ["ocr", "entities", "documents", "network"]
        },

        # Entity endpoints
        {
            "name": "List entities (default)",
            "endpoint": "/api/entities",
            "expected_keys": ["total", "offset", "limit", "entities"]
        },
        {
            "name": "List entities (top 10 by documents)",
            "endpoint": "/api/entities?limit=10&sort_by=documents",
            "expected_keys": ["total", "entities"]
        },
        {
            "name": "List billionaires",
            "endpoint": "/api/entities?filter_billionaires=true",
            "expected_keys": ["total", "entities"]
        },

        # Specific entity tests with disambiguation
        {
            "name": "Get entity: Jeffrey Epstein (canonical)",
            "endpoint": "/api/entities/Jeffrey Epstein",
            "expected_keys": ["name", "canonical_name"]
        },
        {
            "name": "Get entity: Je Je Epstein (variation)",
            "endpoint": "/api/entities/Je Je Epstein",
            "expected_keys": ["name", "canonical_name"]
        },
        {
            "name": "Get entity: Ghislaine Maxwell",
            "endpoint": "/api/entities/Ghislaine Maxwell",
            "expected_keys": ["name"]
        },

        # Network endpoints
        {
            "name": "Get network graph (deduplicated)",
            "endpoint": "/api/network?max_nodes=100&deduplicate=true",
            "expected_keys": ["nodes", "edges", "metadata"]
        },
        {
            "name": "Get network graph (no deduplication)",
            "endpoint": "/api/network?max_nodes=100&deduplicate=false",
            "expected_keys": ["nodes", "edges", "metadata"]
        },
        {
            "name": "Get highly connected entities (min 10 connections)",
            "endpoint": "/api/network?min_connections=10",
            "expected_keys": ["nodes", "edges"]
        },

        # Search endpoints
        {
            "name": "Search entities: Clinton",
            "endpoint": "/api/search?q=Clinton",
            "expected_keys": ["query", "total", "results"]
        },
        {
            "name": "Search entities: Trump",
            "endpoint": "/api/search?q=Trump",
            "expected_keys": ["query", "total", "results"]
        },

        # Timeline
        {
            "name": "Get timeline events",
            "endpoint": "/api/timeline",
            "expected_keys": ["total", "events"]
        },
    ]

    # Run tests
    results = []
    for test_config in tests:
        passed = test_endpoint(**test_config)
        results.append((test_config["name"], passed))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status} {test_name}")

    print("\n" + "=" * 70)
    print(f"Results: {passed_count}/{total_count} tests passed ({100*passed_count/total_count:.1f}%)")
    print("=" * 70)

    # Specific issue checks
    print("\n" + "=" * 70)
    print("ISSUE-SPECIFIC CHECKS")
    print("=" * 70)

    # Check 1: Entity loading
    print("\n1. Entity Loading Check:")
    try:
        response = requests.get(f"{BASE_URL}/api/stats", auth=(USERNAME, PASSWORD))
        data = response.json()
        if data.get("total_entities", 0) > 0:
            print(f"   {Colors.GREEN}✓ Entities loaded: {data['total_entities']}{Colors.RESET}")
        else:
            print(f"   {Colors.RED}✗ No entities loaded!{Colors.RESET}")
    except Exception as e:
        print(f"   {Colors.RED}✗ Failed to check: {e}{Colors.RESET}")

    # Check 2: OCR status loading
    print("\n2. OCR Status Check:")
    try:
        response = requests.get(f"{BASE_URL}/api/ingestion/status", auth=(USERNAME, PASSWORD))
        data = response.json()
        ocr_data = data.get("ocr", {})
        if "error" in ocr_data:
            print(f"   {Colors.YELLOW}⚠ OCR status error: {ocr_data['error']}{Colors.RESET}")
        else:
            print(f"   {Colors.GREEN}✓ OCR status loaded{Colors.RESET}")
            print(f"      Active: {ocr_data.get('active', False)}")
            print(f"      Progress: {ocr_data.get('progress', 0):.1f}%")
    except Exception as e:
        print(f"   {Colors.RED}✗ Failed to check: {e}{Colors.RESET}")

    # Check 3: Entity disambiguation
    print("\n3. Entity Disambiguation Check:")
    test_cases = [
        ("Je Je Epstein", "Jeffrey Epstein"),
        ("Ghislaine Ghislaine", "Ghislaine Maxwell"),
    ]

    for variation, expected_canonical in test_cases:
        try:
            response = requests.get(
                f"{BASE_URL}/api/entities/{variation}",
                auth=(USERNAME, PASSWORD)
            )
            if response.status_code == 200:
                data = response.json()
                canonical = data.get("canonical_name", "")
                if canonical == expected_canonical:
                    print(f"   {Colors.GREEN}✓ '{variation}' -> '{canonical}'{Colors.RESET}")
                else:
                    print(f"   {Colors.YELLOW}⚠ '{variation}' -> '{canonical}' (expected '{expected_canonical}'){Colors.RESET}")
            else:
                print(f"   {Colors.RED}✗ '{variation}' not found{Colors.RESET}")
        except Exception as e:
            print(f"   {Colors.RED}✗ Error testing '{variation}': {e}{Colors.RESET}")

    # Check 4: Network deduplication
    print("\n4. Network Deduplication Check:")
    try:
        # Without deduplication
        response1 = requests.get(
            f"{BASE_URL}/api/network?deduplicate=false&max_nodes=500",
            auth=(USERNAME, PASSWORD)
        )
        data1 = response1.json()
        original_count = len(data1.get("nodes", []))

        # With deduplication
        response2 = requests.get(
            f"{BASE_URL}/api/network?deduplicate=true&max_nodes=500",
            auth=(USERNAME, PASSWORD)
        )
        data2 = response2.json()
        deduplicated_count = len(data2.get("nodes", []))

        duplicates_removed = original_count - deduplicated_count

        if duplicates_removed > 0:
            print(f"   {Colors.GREEN}✓ Deduplication working: {duplicates_removed} duplicates removed{Colors.RESET}")
            print(f"      Original: {original_count} nodes")
            print(f"      Deduplicated: {deduplicated_count} nodes")
        else:
            print(f"   {Colors.YELLOW}⚠ No duplicates found (or deduplication not working){Colors.RESET}")
    except Exception as e:
        print(f"   {Colors.RED}✗ Failed to check: {e}{Colors.RESET}")

    print("\n" + "=" * 70)

    # Exit code based on test results
    if passed_count == total_count:
        print(f"{Colors.GREEN}All tests passed!{Colors.RESET}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}Some tests failed.{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
