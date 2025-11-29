#!/usr/bin/env python3
"""
Comprehensive Search API Testing Suite
Tests performance, functionality, fuzzy matching, boolean logic, and error handling
"""
import asyncio
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime

import httpx


BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class SearchAPITester:
    def __init__(self):
        self.results = {
            "performance": {},
            "functionality": {},
            "fuzzy_matching": {},
            "boolean_logic": {},
            "error_handling": {},
            "concurrent_load": {}
        }
        self.response_times = defaultdict(list)

    async def test_performance(self, client: httpx.AsyncClient):
        """Test 10 different query types and measure performance"""
        print("\n" + "="*80)
        print("PERFORMANCE TESTING - 10 Query Types")
        print("="*80)

        test_queries = [
            ("Simple entity", {"query": "Epstein"}),
            ("Multi-word", {"query": "Ghislaine Maxwell"}),
            ("Boolean AND", {"query": "Epstein AND Maxwell"}),
            ("Boolean OR", {"query": "Epstein OR Clinton"}),
            ("Boolean NOT", {"query": "Epstein NOT Maxwell"}),
            ("Fuzzy typo", {"query": "Ghisline"}),
            ("Date filtered", {"query": "Epstein", "date_start": "2019-01-01", "date_end": "2019-12-31"}),
            ("Field filtered", {"query": "Maxwell", "fields": "entities"}),
            ("Empty results", {"query": "xyznonexistentquery123"}),
            ("Large result set", {"query": "flight", "limit": 50})
        ]

        for query_name, params in test_queries:
            try:
                start = time.perf_counter()
                response = await client.get(f"{BASE_URL}/api/search/unified", params=params, timeout=TIMEOUT)
                end = time.perf_counter()

                latency_ms = (end - start) * 1000
                self.response_times[query_name].append(latency_ms)

                status = "✅" if response.status_code == 200 else "❌"
                data = response.json() if response.status_code == 200 else {}
                total_results = data.get("total_results", 0) if isinstance(data, dict) else 0

                print(f"{status} {query_name:20s} | {latency_ms:6.1f}ms | Status: {response.status_code} | Results: {total_results}")

                self.results["performance"][query_name] = {
                    "latency_ms": round(latency_ms, 2),
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "result_count": total_results
                }

            except Exception as e:
                print(f"❌ {query_name:20s} | ERROR: {str(e)[:50]}")
                self.results["performance"][query_name] = {
                    "error": str(e),
                    "success": False
                }

    async def test_endpoints(self, client: httpx.AsyncClient):
        """Test all search endpoints functionality"""
        print("\n" + "="*80)
        print("ENDPOINT FUNCTIONALITY TESTING")
        print("="*80)

        # Test Unified Search
        print("\n🔍 Testing Unified Search (/api/search/unified)")
        try:
            response = await client.get(f"{BASE_URL}/api/search/unified", params={"query": "Epstein", "limit": 10}, timeout=TIMEOUT)
            data = response.json()

            if response.status_code == 200:
                print(f"✅ Status: {response.status_code}")
                print(f"   Total results: {data.get('total_results', 0)}")
                print(f"   Fields present: {list(data.keys())}")

                # Check for results array
                results = data.get("results", [])
                result_types = {}
                for r in results:
                    rtype = r.get("type", "unknown")
                    result_types[rtype] = result_types.get(rtype, 0) + 1

                print(f"   Results by type: {result_types}")

                self.results["functionality"]["unified_search"] = {
                    "success": True,
                    "status": response.status_code,
                    "total": data.get("total_results", 0),
                    "result_types": result_types
                }
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.results["functionality"]["unified_search"] = {
                    "success": False,
                    "status": response.status_code,
                    "error": response.text[:200]
                }
        except Exception as e:
            print(f"❌ Error: {e!s}")
            self.results["functionality"]["unified_search"] = {"success": False, "error": str(e)}

        # Test Autocomplete
        print("\n💡 Testing Autocomplete (/api/search/suggestions)")
        test_prefixes = ["Eps", "Max", "Cli", "Gh"]
        autocomplete_times = []

        for prefix in test_prefixes:
            try:
                start = time.perf_counter()
                response = await client.get(f"{BASE_URL}/api/search/suggestions", params={"query": prefix}, timeout=TIMEOUT)
                end = time.perf_counter()

                latency_ms = (end - start) * 1000
                autocomplete_times.append(latency_ms)

                data = response.json() if response.status_code == 200 else []
                # Suggestions endpoint returns a list directly
                suggestions = data if isinstance(data, list) else []

                status = "✅" if response.status_code == 200 else "❌"
                print(f"{status} Prefix '{prefix}': {latency_ms:.1f}ms | Suggestions: {len(suggestions)}")

            except Exception as e:
                print(f"❌ Prefix '{prefix}': ERROR - {str(e)[:50]}")

        avg_autocomplete_time = statistics.mean(autocomplete_times) if autocomplete_times else 0
        self.results["functionality"]["autocomplete"] = {
            "success": len(autocomplete_times) > 0,
            "avg_latency_ms": round(avg_autocomplete_time, 2),
            "target_met": avg_autocomplete_time < 100
        }
        print(f"   Average autocomplete latency: {avg_autocomplete_time:.1f}ms (target: <100ms)")

        # Test Analytics
        print("\n📊 Testing Analytics (/api/search/analytics)")
        try:
            response = await client.get(f"{BASE_URL}/api/search/analytics", timeout=TIMEOUT)
            data = response.json()

            if response.status_code == 200:
                print(f"✅ Status: {response.status_code}")
                print(f"   Total searches: {data.get('total_searches', 0)}")
                print(f"   Popular queries: {len(data.get('popular_queries', []))}")
                print(f"   Recent searches: {len(data.get('recent_searches', []))}")

                self.results["functionality"]["analytics"] = {
                    "success": True,
                    "status": response.status_code,
                    "total_searches": data.get("total_searches", 0)
                }
            else:
                print(f"❌ Status: {response.status_code}")
                self.results["functionality"]["analytics"] = {
                    "success": False,
                    "status": response.status_code
                }
        except Exception as e:
            print(f"❌ Error: {e!s}")
            self.results["functionality"]["analytics"] = {"success": False, "error": str(e)}

        # Test Clear History
        print("\n🗑️  Testing Clear History (/api/search/analytics/history)")
        try:
            response = await client.delete(f"{BASE_URL}/api/search/analytics/history", timeout=TIMEOUT)
            data = response.json()

            if response.status_code == 200:
                print(f"✅ Status: {response.status_code}")
                print(f"   Message: {data.get('message', 'N/A')}")

                self.results["functionality"]["clear_history"] = {
                    "success": True,
                    "status": response.status_code
                }
            else:
                print(f"❌ Status: {response.status_code}")
                self.results["functionality"]["clear_history"] = {
                    "success": False,
                    "status": response.status_code
                }
        except Exception as e:
            print(f"❌ Error: {e!s}")
            self.results["functionality"]["clear_history"] = {"success": False, "error": str(e)}

    async def test_fuzzy_matching(self, client: httpx.AsyncClient):
        """Test fuzzy matching with common typos"""
        print("\n" + "="*80)
        print("FUZZY MATCHING ACCURACY TESTING")
        print("="*80)

        typo_tests = [
            ("Ghisline", "Ghislaine"),
            ("Maxwel", "Maxwell"),
            ("Jeffry", "Jeffrey"),
            ("Epstien", "Epstein")
        ]

        matches = 0
        total = len(typo_tests)

        for typo, correct in typo_tests:
            try:
                response = await client.get(f"{BASE_URL}/api/search/unified", params={"query": typo}, timeout=TIMEOUT)
                data = response.json()

                # Check if results contain the correct spelling
                found = False
                results = data.get("results", []) if isinstance(data, dict) else []

                for result in results:
                    result_title = result.get("title", "").lower()
                    if correct.lower() in result_title:
                        found = True
                        matches += 1
                        break

                status = "✅" if found else "❌"
                print(f"{status} '{typo}' → '{correct}' | Found: {found}")

                self.results["fuzzy_matching"][typo] = {
                    "target": correct,
                    "found": found,
                    "result_count": len(results)
                }

            except Exception as e:
                print(f"❌ '{typo}' → ERROR: {str(e)[:50]}")
                self.results["fuzzy_matching"][typo] = {"error": str(e)}

        accuracy = (matches / total * 100) if total > 0 else 0
        print(f"\nFuzzy Matching Accuracy: {accuracy:.1f}% ({matches}/{total})")
        self.results["fuzzy_matching"]["overall_accuracy"] = round(accuracy, 2)

    async def test_boolean_logic(self, client: httpx.AsyncClient):
        """Test boolean operators with sample data"""
        print("\n" + "="*80)
        print("BOOLEAN LOGIC VERIFICATION")
        print("="*80)

        boolean_tests = [
            ("Epstein AND Maxwell", "AND"),
            ("Epstein OR Clinton", "OR"),
            ("Epstein NOT Maxwell", "NOT"),
            ("(Epstein OR Clinton) AND NOT Maxwell", "COMPLEX")
        ]

        for query, test_type in boolean_tests:
            try:
                response = await client.get(f"{BASE_URL}/api/search/unified", params={"query": query}, timeout=TIMEOUT)
                data = response.json()

                status = "✅" if response.status_code == 200 else "❌"
                total = data.get("total_results", 0) if isinstance(data, dict) else 0

                print(f"{status} {test_type:10s} | Query: '{query[:40]}' | Results: {total}")

                self.results["boolean_logic"][test_type] = {
                    "query": query,
                    "success": response.status_code == 200,
                    "result_count": total
                }

            except Exception as e:
                print(f"❌ {test_type:10s} | ERROR: {str(e)[:50]}")
                self.results["boolean_logic"][test_type] = {"error": str(e)}

    async def test_error_handling(self, client: httpx.AsyncClient):
        """Test edge cases and error handling"""
        print("\n" + "="*80)
        print("ERROR HANDLING VERIFICATION")
        print("="*80)

        error_tests = [
            ("Empty query", {"query": ""}),
            ("Special chars", {"query": "!@#$%^&*()"}),
            ("Very long query", {"query": "x" * 1000}),
            ("Invalid params", {"query": "test", "limit": "invalid"}),
            ("Malformed boolean", {"query": "AND OR NOT"})
        ]

        for test_name, params in error_tests:
            try:
                response = await client.get(f"{BASE_URL}/api/search/unified", params=params, timeout=TIMEOUT)

                # Error handling should return graceful responses (200 with empty results or 4xx)
                graceful = response.status_code in [200, 400, 422]
                status = "✅" if graceful else "❌"

                print(f"{status} {test_name:20s} | Status: {response.status_code}")

                self.results["error_handling"][test_name] = {
                    "status_code": response.status_code,
                    "graceful": graceful
                }

            except Exception as e:
                print(f"❌ {test_name:20s} | ERROR: {str(e)[:50]}")
                self.results["error_handling"][test_name] = {"error": str(e)}

    async def test_concurrent_load(self, client: httpx.AsyncClient):
        """Test concurrent load with 10 simultaneous requests"""
        print("\n" + "="*80)
        print("CONCURRENT LOAD TESTING - 10 Simultaneous Requests")
        print("="*80)

        async def single_request(query_id: int):
            start = time.perf_counter()
            try:
                response = await client.get(
                    f"{BASE_URL}/api/search/unified",
                    params={"query": f"test_query_{query_id}"},
                    timeout=TIMEOUT
                )
                end = time.perf_counter()
                return {
                    "id": query_id,
                    "success": response.status_code == 200,
                    "latency_ms": (end - start) * 1000,
                    "status": response.status_code
                }
            except Exception as e:
                end = time.perf_counter()
                return {
                    "id": query_id,
                    "success": False,
                    "latency_ms": (end - start) * 1000,
                    "error": str(e)
                }

        # Send 10 concurrent requests
        tasks = [single_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        successes = sum(1 for r in results if r["success"])
        latencies = [r["latency_ms"] for r in results]
        avg_latency = statistics.mean(latencies) if latencies else 0

        print(f"✅ Successful requests: {successes}/10")
        print(f"   Average latency: {avg_latency:.1f}ms")
        print(f"   Min latency: {min(latencies):.1f}ms")
        print(f"   Max latency: {max(latencies):.1f}ms")

        self.results["concurrent_load"] = {
            "total_requests": 10,
            "successful": successes,
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "all_succeeded": successes == 10
        }

    def calculate_percentiles(self):
        """Calculate performance percentiles"""
        print("\n" + "="*80)
        print("PERFORMANCE PERCENTILES")
        print("="*80)

        all_latencies = []
        for times in self.response_times.values():
            all_latencies.extend(times)

        if all_latencies:
            p50 = statistics.median(all_latencies)
            p95 = statistics.quantiles(all_latencies, n=20)[18]  # 95th percentile
            p99 = statistics.quantiles(all_latencies, n=100)[98]  # 99th percentile

            print(f"p50 (median): {p50:.1f}ms (target: <300ms) {'✅' if p50 < 300 else '❌'}")
            print(f"p95:          {p95:.1f}ms (target: <500ms) {'✅' if p95 < 500 else '❌'}")
            print(f"p99:          {p99:.1f}ms (target: <1000ms) {'✅' if p99 < 1000 else '❌'}")

            self.results["percentiles"] = {
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "p50_target_met": p50 < 300,
                "p95_target_met": p95 < 500,
                "p99_target_met": p99 < 1000
            }
        else:
            print("❌ No latency data collected")
            self.results["percentiles"] = {"error": "No data"}

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)

        # Success criteria
        print("\n📋 SUCCESS CRITERIA VERIFICATION:")

        criteria = {
            "All endpoints return 200 OK": all(
                r.get("success", False) for r in self.results.get("functionality", {}).values()
            ),
            "No 500 errors": all(
                r.get("status_code", 500) != 500
                for r in self.results.get("performance", {}).values()
            ),
            "p50 latency <300ms": self.results.get("percentiles", {}).get("p50_target_met", False),
            "p95 latency <500ms": self.results.get("percentiles", {}).get("p95_target_met", False),
            "Fuzzy matching accuracy >90%": self.results.get("fuzzy_matching", {}).get("overall_accuracy", 0) > 90,
            "Boolean operators work": all(
                r.get("success", False) for r in self.results.get("boolean_logic", {}).values()
            ),
            "Error handling is graceful": all(
                r.get("graceful", False) for r in self.results.get("error_handling", {}).values()
            ),
            "Concurrent requests succeed": self.results.get("concurrent_load", {}).get("all_succeeded", False)
        }

        for criterion, met in criteria.items():
            status = "✅" if met else "❌"
            print(f"{status} {criterion}")

        # Overall assessment
        success_count = sum(1 for met in criteria.values() if met)
        total_count = len(criteria)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"/Users/masa/Projects/epstein/search_api_test_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "success_criteria": criteria,
                "success_rate": success_rate,
                "detailed_results": self.results
            }, f, indent=2)

        print(f"\n📄 Detailed report saved: {report_file}")

        return success_rate >= 75  # 75% success rate threshold

async def main():
    """Run all tests"""
    tester = SearchAPITester()

    print("🚀 Starting Comprehensive Search API Testing")
    print(f"Target: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s")

    async with httpx.AsyncClient() as client:
        # Run all test suites
        await tester.test_performance(client)
        await tester.test_endpoints(client)
        await tester.test_fuzzy_matching(client)
        await tester.test_boolean_logic(client)
        await tester.test_error_handling(client)
        await tester.test_concurrent_load(client)

        # Calculate percentiles
        tester.calculate_percentiles()

        # Generate final report
        success = tester.generate_report()

        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
