#!/usr/bin/env python3
"""
Test API v2 Endpoints

Design Decision: Automated API Testing
Rationale: Verify all endpoints return correct data before frontend migration.
Tests all service layer integrations.

Usage:
    python3 test_api_v2.py

Requirements:
    - Server must be running on http://localhost:8000
    - Or specify URL: python3 test_api_v2.py --url http://localhost:8001
"""

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class Colors:
    """Terminal colors for output"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def test_endpoint(url: str, endpoint: str, description: str) -> bool:
    """Test single endpoint

    Args:
        url: Base URL
        endpoint: Endpoint path
        description: Test description

    Returns:
        True if test passed, False otherwise
    """
    full_url = url + endpoint
    print(f"\n{Colors.BLUE}Testing:{Colors.END} {description}")
    print(f"  URL: {full_url}")

    try:
        req = Request(full_url)
        req.add_header("Accept", "application/json")

        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            # Basic validation
            if not isinstance(data, dict):
                print(f"  {Colors.RED}✗ Failed:{Colors.END} Response is not a dictionary")
                return False

            print(f"  {Colors.GREEN}✓ Passed{Colors.END}")
            print(f"  Response keys: {', '.join(data.keys())}")

            return True

    except HTTPError as e:
        print(f"  {Colors.RED}✗ Failed:{Colors.END} HTTP {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"  {Colors.RED}✗ Failed:{Colors.END} URL Error - {e.reason}")
        return False
    except Exception as e:
        print(f"  {Colors.RED}✗ Failed:{Colors.END} {e!s}")
        return False


def run_tests(base_url: str):
    """Run all API v2 tests

    Args:
        base_url: Base URL (e.g., http://localhost:8000)
    """
    print("=" * 70)
    print("API v2 Endpoint Tests")
    print("=" * 70)
    print(f"Base URL: {base_url}")

    tests = [
        # Entity endpoints
        ("/api/v2/entities?limit=10", "Get entities (default)"),
        ("/api/v2/entities?search=Clinton&limit=10", "Get entities (search)"),
        ("/api/v2/entities?filter_billionaires=true&limit=10", "Get entities (billionaires only)"),
        ("/api/v2/entities?sort_by=connections&limit=10", "Get entities (sorted by connections)"),
        ("/api/v2/entities/stats/summary", "Get entity statistics"),

        # Flight endpoints
        ("/api/v2/flights?limit=10", "Get flights (default)"),
        ("/api/v2/flights/routes", "Get flight routes"),
        ("/api/v2/flights/stats", "Get flight statistics"),

        # Document endpoints
        ("/api/v2/documents/search?limit=10", "Get documents (default)"),
        ("/api/v2/documents/search?q=email&limit=10", "Get documents (search)"),
        ("/api/v2/documents/stats", "Get document statistics"),

        # Network endpoints
        ("/api/v2/network/graph?min_connections=5&max_nodes=100", "Get network graph"),
        ("/api/v2/network/stats", "Get network statistics"),

        # Unified search
        ("/api/v2/search?q=Clinton&limit=10", "Unified search"),
    ]

    results = {
        "passed": 0,
        "failed": 0,
        "total": len(tests)
    }

    for endpoint, description in tests:
        if test_endpoint(base_url, endpoint, description):
            results["passed"] += 1
        else:
            results["failed"] += 1

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total:  {results['total']}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")

    if results["failed"] == 0:
        print(f"\n{Colors.GREEN}✓ All tests passed!{Colors.END}")
        return 0
    print(f"\n{Colors.RED}✗ Some tests failed{Colors.END}")
    return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test API v2 endpoints")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    # Run tests
    exit_code = run_tests(args.url)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
