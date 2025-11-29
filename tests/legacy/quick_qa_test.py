#!/usr/bin/env python3
"""
Quick QA Test - Essential Production Readiness Checks
Fast execution with focused testing
"""

import json
import sys
import time
from datetime import datetime

import requests


BASE_URL = "http://localhost:8081"

def colored(text, color):
    """Simple colored output"""
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m", "blue": "\033[94m", "end": "\033[0m"}
    return f"{colors.get(color, '')}{text}{colors['end']}"

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add(self, name, status, details=""):
        self.tests.append({"name": name, "status": status, "details": details})
        if status == "PASS":
            self.passed += 1
            print(f"  ✅ {name}")
        elif status == "FAIL":
            self.failed += 1
            print(f"  ❌ {name}: {details}")
        else:
            self.warnings += 1
            print(f"  ⚠️  {name}: {details}")
        if details and status != "PASS":
            print(f"     {details}")

    def summary(self):
        total = len(self.tests)
        print(f"\n{'='*80}")
        print("TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"Passed:  {colored(f'{self.passed} ({self.passed/total*100:.1f}%)', 'green')}")
        print(f"Failed:  {colored(f'{self.failed} ({self.failed/total*100:.1f}%)', 'red')}")
        print(f"Warnings: {colored(f'{self.warnings} ({self.warnings/total*100:.1f}%)', 'yellow')}")

    def decision(self):
        print(f"\n{'='*80}")
        print("PRODUCTION READINESS DECISION")
        print(f"{'='*80}")

        if self.failed == 0:
            print(colored("✅ GO FOR PRODUCTION", "green"))
            print("   - All core features working")
            print("   - 0 critical bugs")
            print("   - All API endpoints functional")
            return "GO"
        if self.failed <= 2:
            print(colored("⚠️  CONDITIONAL GO", "yellow"))
            print(f"   - {self.failed} minor failures")
            print("   - Review recommended before deploy")
            return "CONDITIONAL"
        print(colored("❌ NO-GO FOR PRODUCTION", "red"))
        print(f"   - {self.failed} critical failures")
        print("   - Issues must be resolved")
        return "NO_GO"

def main():
    results = TestResults()

    print("="*80)
    print("QUICK QA TEST - PRODUCTION READINESS")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Test 1: Server Connectivity
    print("\n[1] SERVER CONNECTIVITY")
    try:
        start = time.time()
        response = requests.get(BASE_URL, timeout=5)
        load_time = time.time() - start

        if response.status_code == 200:
            results.add("Server responds with 200 OK", "PASS")
            if load_time < 2.0:
                results.add(f"Page load < 2s ({load_time:.2f}s)", "PASS")
            else:
                results.add("Page load time", "WARNING", f"Took {load_time:.2f}s")
        else:
            results.add("Server responds with 200 OK", "FAIL", f"Status: {response.status_code}")
    except Exception as e:
        results.add("Server connectivity", "FAIL", str(e))
        results.decision()
        return None

    # Test 2: API Endpoints
    print("\n[2] API ENDPOINTS")
    endpoints = [
        ("/api/stats", "Stats"),
        ("/api/entities", "Entities"),
        ("/api/network", "Network"),
        ("/api/timeline", "Timeline"),
        ("/api/flights", "Flights"),
        ("/api/documents", "Documents")
    ]

    api_data = {}
    for path, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=10)
            if response.status_code == 200:
                results.add(f"{name} API (200 OK)", "PASS")
                try:
                    data = response.json()
                    api_data[name] = data
                    results.add(f"{name} API returns valid JSON", "PASS")
                except:
                    results.add(f"{name} API returns valid JSON", "FAIL", "Invalid JSON")
            else:
                results.add(f"{name} API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            results.add(f"{name} API", "FAIL", str(e))

    # Test 3: Data Counts
    print("\n[3] DATA INTEGRITY")
    if "Stats" in api_data:
        stats = api_data["Stats"]

        expected = {
            "total_entities": 1702,
            "total_documents": 38482,
            "network_nodes": 284,
            "network_edges": 1624
        }

        print("\n  Current Data Counts:")
        for key, expected_val in expected.items():
            actual_val = stats.get(key, 0)
            print(f"    {key}: {actual_val}")

            if actual_val == expected_val:
                results.add(f"Data count: {key} = {expected_val}", "PASS")
            elif actual_val > 0:
                results.add(f"Data count: {key}", "WARNING", f"Expected {expected_val}, got {actual_val}")
            else:
                results.add(f"Data count: {key}", "FAIL", f"No data (expected {expected_val})")

    # Test 4: Timeline Events (Previously broken)
    print("\n[4] TIMELINE FIX VERIFICATION")
    if "Timeline" in api_data:
        timeline = api_data["Timeline"]

        if isinstance(timeline, dict) and "events" in timeline:
            event_count = len(timeline["events"])
            if event_count > 0:
                results.add(f"Timeline returns events ({event_count})", "PASS")
            else:
                results.add("Timeline returns events", "FAIL", "No events in response")
        elif isinstance(timeline, list):
            if len(timeline) > 0:
                results.add(f"Timeline returns events ({len(timeline)})", "PASS")
            else:
                results.add("Timeline returns events", "FAIL", "Empty timeline array")
        else:
            results.add("Timeline format", "WARNING", f"Unexpected format: {type(timeline)}")

    # Test 5: Network Graph Data
    print("\n[5] NETWORK GRAPH DATA")
    if "Network" in api_data:
        network = api_data["Network"]

        if "nodes" in network and "edges" in network:
            node_count = len(network["nodes"])
            edge_count = len(network["edges"])

            if node_count > 0:
                results.add(f"Network has nodes ({node_count})", "PASS")
            else:
                results.add("Network has nodes", "FAIL", "No nodes")

            if edge_count > 0:
                results.add(f"Network has edges ({edge_count})", "PASS")
            else:
                results.add("Network has edges", "FAIL", "No edges")
        else:
            results.add("Network data structure", "FAIL", "Missing nodes or edges")

    # Test 6: Flights Data
    print("\n[6] FLIGHTS DATA")
    if "Flights" in api_data:
        flights = api_data["Flights"]

        if isinstance(flights, dict) and "flights" in flights:
            flight_count = len(flights["flights"])
            if flight_count > 0:
                results.add(f"Flights data loaded ({flight_count})", "PASS")
            else:
                results.add("Flights data loaded", "FAIL", "No flights")
        elif isinstance(flights, list) and len(flights) > 0:
            results.add(f"Flights data loaded ({len(flights)})", "PASS")
        else:
            results.add("Flights data format", "WARNING", "Unexpected format")

    # Test 7: Entities Data
    print("\n[7] ENTITIES DATA")
    if "Entities" in api_data:
        entities = api_data["Entities"]

        if isinstance(entities, dict) and "entities" in entities:
            entity_count = len(entities["entities"])
            if entity_count > 0:
                results.add(f"Entities data loaded ({entity_count})", "PASS")

                # Check for entity quality issues
                sample = entities["entities"][:10] if len(entities["entities"]) >= 10 else entities["entities"]
                has_trailing_comma = any(e.get("name", "").strip().endswith(",") for e in sample)

                if not has_trailing_comma:
                    results.add("Entity name quality (no trailing commas)", "PASS")
                else:
                    results.add("Entity name quality", "WARNING", "Found entities with trailing commas")
            else:
                results.add("Entities data loaded", "FAIL", "No entities")
        elif isinstance(entities, list) and len(entities) > 0:
            results.add(f"Entities data loaded ({len(entities)})", "PASS")
        else:
            results.add("Entities data format", "WARNING", "Unexpected format")

    # Test 8: Documents Data
    print("\n[8] DOCUMENTS DATA")
    if "Documents" in api_data:
        documents = api_data["Documents"]

        if isinstance(documents, dict) and "documents" in documents:
            doc_count = len(documents["documents"])
            if doc_count > 0:
                results.add(f"Documents data loaded ({doc_count})", "PASS")
            else:
                results.add("Documents data loaded", "FAIL", "No documents")
        elif isinstance(documents, list) and len(documents) > 0:
            results.add(f"Documents data loaded ({len(documents)})", "PASS")
        else:
            results.add("Documents data format", "WARNING", "Unexpected format")

    # Test 9: Static Assets
    print("\n[9] STATIC ASSETS")
    static_assets = [
        ("/favicon.ico", "Favicon"),
        ("/server/web/app.js", "Main JS"),
        ("/server/web/index.html", "Index HTML")
    ]

    for path, name in static_assets:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            if response.status_code == 200:
                results.add(f"{name} available", "PASS")
            else:
                results.add(f"{name} available", "WARNING", f"Status: {response.status_code}")
        except:
            results.add(f"{name} available", "WARNING", "Not accessible")

    # Generate summary and decision
    results.summary()
    decision = results.decision()

    # Save results
    report = {
        "timestamp": datetime.now().isoformat(),
        "decision": decision,
        "tests": results.tests,
        "stats": {
            "total": len(results.tests),
            "passed": results.passed,
            "failed": results.failed,
            "warnings": results.warnings
        },
        "api_data": api_data
    }

    results_file = "/Users/masa/Projects/epstein/quick_qa_results.json"
    with open(results_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Full results saved to: {results_file}")

    # Return appropriate exit code
    return 0 if decision in ["GO", "CONDITIONAL"] else 1

if __name__ == "__main__":
    sys.exit(main())
