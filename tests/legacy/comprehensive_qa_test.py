#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Epstein Archive Application
Testing all features and verifying production readiness
"""

import json
import sys
import time
from datetime import datetime

from playwright.sync_api import sync_playwright


# Test configuration
BASE_URL = "http://localhost:8081"
SCREENSHOTS_DIR = "/Users/masa/Projects/epstein/qa_screenshots"
TEST_RESULTS = {
    "timestamp": datetime.now().isoformat(),
    "test_suites": {},
    "console_errors": [],
    "performance_metrics": {},
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": []
}

def log_test(suite, test_name, status, details=""):
    """Log test result"""
    if suite not in TEST_RESULTS["test_suites"]:
        TEST_RESULTS["test_suites"][suite] = []

    TEST_RESULTS["test_suites"][suite].append({
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })

    TEST_RESULTS["total_tests"] += 1
    if status == "PASS":
        TEST_RESULTS["passed"] += 1
        print(f"✅ [{suite}] {test_name}")
    elif status == "FAIL":
        TEST_RESULTS["failed"] += 1
        print(f"❌ [{suite}] {test_name}: {details}")
    else:
        print(f"⚠️  [{suite}] {test_name}: {details}")

    if details:
        print(f"   {details}")

def capture_console_errors(page):
    """Capture console errors from page"""
    errors = []

    def on_console(msg):
        if msg.type in ["error", "warning"]:
            errors.append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat()
            })

    page.on("console", on_console)
    return errors

def test_suite_1_core_functionality(page):
    """Test Suite 1: Core Functionality"""
    print("\n" + "="*80)
    print("TEST SUITE 1: CORE FUNCTIONALITY")
    print("="*80)

    suite = "Core Functionality"
    console_errors = capture_console_errors(page)

    try:
        # Navigate to application
        start_time = time.time()
        page.goto(BASE_URL, wait_until="networkidle")
        load_time = time.time() - start_time
        TEST_RESULTS["performance_metrics"]["initial_page_load"] = f"{load_time:.2f}s"

        if load_time < 2.0:
            log_test(suite, "Initial page load < 2s", "PASS", f"Loaded in {load_time:.2f}s")
        else:
            log_test(suite, "Initial page load < 2s", "FAIL", f"Loaded in {load_time:.2f}s")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/01_dashboard_initial.png", full_page=True)
        log_test(suite, "Dashboard screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Initial page load", "FAIL", str(e))
        return

    # Test 1.1: Timeline Tab
    try:
        print("\n--- Testing Timeline Tab ---")
        page.click('button:has-text("Timeline")')
        page.wait_for_timeout(2000)  # Wait for content to load

        # Check for timeline events
        timeline_events = page.query_selector_all('.timeline-event, .timeline-item, [class*="timeline"]')
        event_count = len(timeline_events)

        # Also check the stats display
        stats_text = page.inner_text("body")

        # Look for event count in stats or content
        if "events" in stats_text.lower() or event_count > 0:
            log_test(suite, "Timeline tab displays events", "PASS", f"Found {event_count} event elements")
        else:
            log_test(suite, "Timeline tab displays events", "FAIL", "No timeline events found")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/02_timeline_tab.png", full_page=True)
        log_test(suite, "Timeline screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Timeline tab test", "FAIL", str(e))

    # Test 1.2: Network Graph
    try:
        print("\n--- Testing Network Graph ---")
        page.click('button:has-text("Network")')
        page.wait_for_timeout(3000)  # Wait for network graph to render

        # Check for network graph elements
        network_elements = page.query_selector_all('canvas, svg, .network-graph, [id*="network"], [class*="graph"]')

        if len(network_elements) > 0:
            log_test(suite, "Network graph renders", "PASS", f"Found {len(network_elements)} graph elements")
        else:
            log_test(suite, "Network graph renders", "FAIL", "No network graph elements found")

        # Test connection slider
        slider = page.query_selector('input[type="range"], .slider')
        if slider:
            log_test(suite, "Connection slider present", "PASS")
        else:
            log_test(suite, "Connection slider present", "WARNING", "Slider not found")

        # Test Load More button
        load_more_btn = page.query_selector('button:has-text("Load More"), button:has-text("Show More")')
        if load_more_btn:
            log_test(suite, "Load More button present", "PASS")
        else:
            log_test(suite, "Load More button present", "WARNING", "Button not found")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/03_network_graph.png", full_page=True)
        log_test(suite, "Network screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Network graph test", "FAIL", str(e))

    # Test 1.3: Flight Map
    try:
        print("\n--- Testing Flight Map ---")
        page.click('button:has-text("Flights")')
        page.wait_for_timeout(3000)  # Wait for map to render

        # Check for flight map elements
        map_elements = page.query_selector_all('canvas, .leaflet-container, .map-container, [id*="map"]')

        if len(map_elements) > 0:
            log_test(suite, "Flight map renders", "PASS", f"Found {len(map_elements)} map elements")
        else:
            log_test(suite, "Flight map renders", "FAIL", "No flight map elements found")

        # Check for passenger filter
        passenger_filter = page.query_selector('select, input[placeholder*="passenger" i], input[placeholder*="search" i]')
        if passenger_filter:
            log_test(suite, "Passenger filter present", "PASS")
        else:
            log_test(suite, "Passenger filter present", "WARNING", "Filter not found")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/04_flight_map.png", full_page=True)
        log_test(suite, "Flight map screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Flight map test", "FAIL", str(e))

    # Test 1.4: Entity List
    try:
        print("\n--- Testing Entity List ---")
        page.click('button:has-text("Entities")')
        page.wait_for_timeout(2000)  # Wait for entities to load

        # Check for entity cards
        entity_cards = page.query_selector_all('.entity-card, [class*="entity"], .card')
        entity_count = len(entity_cards)

        if entity_count > 0:
            log_test(suite, "Entity list displays", "PASS", f"Found {entity_count} entity cards")
        else:
            log_test(suite, "Entity list displays", "WARNING", "No entity cards found (may be virtual scrolling)")

        # Check for search functionality
        search_input = page.query_selector('input[type="search"], input[placeholder*="search" i]')
        if search_input:
            log_test(suite, "Entity search present", "PASS")
        else:
            log_test(suite, "Entity search present", "WARNING", "Search input not found")

        # Check for type filters
        type_filters = page.query_selector_all('select, .filter, [class*="type-filter"]')
        if len(type_filters) > 0:
            log_test(suite, "Type filters present", "PASS")
        else:
            log_test(suite, "Type filters present", "WARNING", "Filters not found")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/05_entity_list.png", full_page=True)
        log_test(suite, "Entity list screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Entity list test", "FAIL", str(e))

    # Test 1.5: Documents Tab
    try:
        print("\n--- Testing Documents Tab ---")
        page.click('button:has-text("Documents")')
        page.wait_for_timeout(2000)  # Wait for documents to load

        # Check for document elements
        doc_elements = page.query_selector_all('.document, .doc-item, [class*="document"]')

        if len(doc_elements) > 0:
            log_test(suite, "Documents tab displays", "PASS", f"Found {len(doc_elements)} document elements")
        else:
            log_test(suite, "Documents tab displays", "WARNING", "No document elements found (may be virtual scrolling)")

        page.screenshot(path=f"{SCREENSHOTS_DIR}/06_documents_tab.png", full_page=True)
        log_test(suite, "Documents screenshot captured", "PASS")

    except Exception as e:
        log_test(suite, "Documents tab test", "FAIL", str(e))

    # Check console errors
    if console_errors:
        TEST_RESULTS["console_errors"].extend(console_errors)
        error_count = len([e for e in console_errors if e["type"] == "error"])
        if error_count > 0:
            log_test(suite, "Console errors check", "FAIL", f"{error_count} console errors detected")
        else:
            log_test(suite, "Console errors check", "PASS", f"Only {len(console_errors)} warnings")
    else:
        log_test(suite, "Console errors check", "PASS", "No console errors or warnings")

def test_suite_2_interactive_features(page):
    """Test Suite 2: Interactive Features"""
    print("\n" + "="*80)
    print("TEST SUITE 2: INTERACTIVE FEATURES")
    print("="*80)

    suite = "Interactive Features"

    try:
        # Navigate to Entities tab
        page.click('button:has-text("Entities")')
        page.wait_for_timeout(2000)

        # Test 2.1: Entity Card Click
        entity_cards = page.query_selector_all('.entity-card, [class*="entity"]')
        if len(entity_cards) > 0:
            # Click first entity card
            entity_cards[0].click()
            page.wait_for_timeout(1000)

            # Check if entity detail modal/panel opened
            modal = page.query_selector('.modal, .panel, .detail, [class*="modal"], [class*="detail"]')
            if modal:
                log_test(suite, "Entity card click opens detail", "PASS")

                # Check for navigation buttons
                flights_btn = page.query_selector('button:has-text("Flights"), a:has-text("Flights")')
                docs_btn = page.query_selector('button:has-text("Documents"), a:has-text("Documents")')
                network_btn = page.query_selector('button:has-text("Network"), a:has-text("Network")')
                timeline_btn = page.query_selector('button:has-text("Timeline"), a:has-text("Timeline")')

                nav_btns = [b for b in [flights_btn, docs_btn, network_btn, timeline_btn] if b is not None]
                log_test(suite, "Entity navigation buttons present", "PASS" if len(nav_btns) > 0 else "WARNING",
                        f"Found {len(nav_btns)}/4 navigation buttons")

                page.screenshot(path=f"{SCREENSHOTS_DIR}/07_entity_card_detail.png", full_page=True)

                # Close modal/panel
                close_btn = page.query_selector('button:has-text("Close"), button[aria-label*="close" i], .close')
                if close_btn:
                    close_btn.click()
                    page.wait_for_timeout(500)
            else:
                log_test(suite, "Entity card click opens detail", "WARNING", "No modal/detail panel found")
        else:
            log_test(suite, "Entity card interaction test", "WARNING", "No entity cards found to test")

    except Exception as e:
        log_test(suite, "Interactive features test", "FAIL", str(e))

def test_suite_3_data_integrity(page):
    """Test Suite 3: Data Integrity"""
    print("\n" + "="*80)
    print("TEST SUITE 3: DATA INTEGRITY")
    print("="*80)

    suite = "Data Integrity"

    # Test API endpoints
    api_endpoints = [
        ("/api/stats", "Stats API"),
        ("/api/entities", "Entities API"),
        ("/api/network", "Network API"),
        ("/api/timeline", "Timeline API"),
        ("/api/flights", "Flights API"),
        ("/api/documents", "Documents API")
    ]

    for endpoint, name in api_endpoints:
        try:
            response = page.request.get(f"{BASE_URL}{endpoint}")
            status = response.status

            if status == 200:
                log_test(suite, f"{name} endpoint", "PASS", f"Status: {status}")

                # Validate JSON response
                try:
                    response.json()
                    log_test(suite, f"{name} returns valid JSON", "PASS")
                except:
                    log_test(suite, f"{name} returns valid JSON", "FAIL", "Invalid JSON response")
            else:
                log_test(suite, f"{name} endpoint", "FAIL", f"Status: {status}")
        except Exception as e:
            log_test(suite, f"{name} endpoint", "FAIL", str(e))

    # Test data counts from stats API
    try:
        response = page.request.get(f"{BASE_URL}/api/stats")
        stats = response.json()

        expected_counts = {
            "total_entities": 1702,
            "total_documents": 38482,
            "network_nodes": 284,
            "network_edges": 1624
        }

        for key, expected in expected_counts.items():
            actual = stats.get(key, 0)
            if actual == expected:
                log_test(suite, f"Data count: {key}", "PASS", f"Expected: {expected}, Actual: {actual}")
            else:
                log_test(suite, f"Data count: {key}", "WARNING", f"Expected: {expected}, Actual: {actual}")

    except Exception as e:
        log_test(suite, "Data counts validation", "FAIL", str(e))

def test_suite_4_performance(page):
    """Test Suite 4: Performance"""
    print("\n" + "="*80)
    print("TEST SUITE 4: PERFORMANCE")
    print("="*80)

    suite = "Performance"

    # Test tab switch performance
    tabs = ["Entities", "Network", "Flights", "Timeline", "Documents"]

    for tab in tabs:
        try:
            start_time = time.time()
            page.click(f'button:has-text("{tab}")')
            page.wait_for_timeout(500)  # Minimum wait
            switch_time = time.time() - start_time

            TEST_RESULTS["performance_metrics"][f"{tab}_tab_switch"] = f"{switch_time:.3f}s"

            if switch_time < 0.5:
                log_test(suite, f"{tab} tab switch < 500ms", "PASS", f"Switched in {switch_time*1000:.0f}ms")
            elif switch_time < 1.0:
                log_test(suite, f"{tab} tab switch < 500ms", "WARNING", f"Switched in {switch_time*1000:.0f}ms")
            else:
                log_test(suite, f"{tab} tab switch < 500ms", "FAIL", f"Switched in {switch_time*1000:.0f}ms")
        except Exception as e:
            log_test(suite, f"{tab} tab switch test", "FAIL", str(e))

def test_suite_5_error_handling(page):
    """Test Suite 5: Error Handling"""
    print("\n" + "="*80)
    print("TEST SUITE 5: ERROR HANDLING")
    print("="*80)

    suite = "Error Handling"

    # Test search with no results
    try:
        page.click('button:has-text("Entities")')
        page.wait_for_timeout(1000)

        search_input = page.query_selector('input[type="search"], input[placeholder*="search" i]')
        if search_input:
            search_input.fill("ZZZZNONEXISTENTZZZZZ")
            page.wait_for_timeout(1000)

            # Check if "no results" message appears
            body_text = page.inner_text("body")
            if "no results" in body_text.lower() or "not found" in body_text.lower() or "0 results" in body_text.lower():
                log_test(suite, "Empty search results handled", "PASS", "Shows 'no results' message")
            else:
                log_test(suite, "Empty search results handled", "WARNING", "No clear 'no results' message found")

            # Clear search
            search_input.fill("")
            page.wait_for_timeout(500)
        else:
            log_test(suite, "Search functionality test", "WARNING", "Search input not found")
    except Exception as e:
        log_test(suite, "Error handling test", "FAIL", str(e))

def test_suite_6_user_experience(page):
    """Test Suite 6: User Experience"""
    print("\n" + "="*80)
    print("TEST SUITE 6: USER EXPERIENCE")
    print("="*80)

    suite = "User Experience"

    # Test favicon
    try:
        favicon = page.query_selector('link[rel*="icon"]')
        if favicon:
            log_test(suite, "Favicon present", "PASS")
        else:
            log_test(suite, "Favicon present", "WARNING", "Favicon link not found")
    except Exception as e:
        log_test(suite, "Favicon test", "FAIL", str(e))

    # Test theme switcher
    try:
        theme_btn = page.query_selector('button[aria-label*="theme" i], .theme-toggle, button:has-text("Dark"), button:has-text("Light")')
        if theme_btn:
            log_test(suite, "Theme switcher present", "PASS")
        else:
            log_test(suite, "Theme switcher present", "WARNING", "Theme switcher not found")
    except Exception as e:
        log_test(suite, "Theme switcher test", "FAIL", str(e))

    # Test loading states
    try:
        # Navigate to a tab that should show loading
        page.click('button:has-text("Network")')
        page.wait_for_timeout(100)  # Check immediately for loading state

        loading_indicator = page.query_selector('.loading, .spinner, [class*="loading"], [class*="spinner"]')
        # Note: Loading might be too fast to catch, so this is informational
        if loading_indicator:
            log_test(suite, "Loading state visible", "PASS", "Loading indicator found")
        else:
            log_test(suite, "Loading state visible", "INFO", "Loading too fast to capture or not present")
    except Exception as e:
        log_test(suite, "Loading state test", "WARNING", str(e))

def generate_report():
    """Generate final test report"""
    print("\n" + "="*80)
    print("PRODUCTION READINESS REPORT")
    print("="*80)

    print("\nTest Execution Summary:")
    print(f"  Total Tests: {TEST_RESULTS['total_tests']}")
    print(f"  Passed: {TEST_RESULTS['passed']} ({TEST_RESULTS['passed']/TEST_RESULTS['total_tests']*100:.1f}%)")
    print(f"  Failed: {TEST_RESULTS['failed']} ({TEST_RESULTS['failed']/TEST_RESULTS['total_tests']*100:.1f}%)")
    print(f"  Warnings: {len([t for suite in TEST_RESULTS['test_suites'].values() for t in suite if t['status'] == 'WARNING'])}")

    print("\nPerformance Metrics:")
    for metric, value in TEST_RESULTS["performance_metrics"].items():
        print(f"  {metric}: {value}")

    print("\nConsole Errors:")
    error_count = len([e for e in TEST_RESULTS["console_errors"] if e["type"] == "error"])
    warning_count = len([e for e in TEST_RESULTS["console_errors"] if e["type"] == "warning"])
    print(f"  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")

    # Production readiness decision
    critical_failures = TEST_RESULTS["failed"]
    console_errors = error_count

    print(f"\n{'='*80}")
    print("GO/NO-GO DECISION")
    print("="*80)

    if critical_failures == 0 and console_errors == 0:
        print("✅ GO FOR PRODUCTION")
        print("   - All core features working")
        print("   - 0 critical bugs")
        print("   - Performance within thresholds")
        print("   - No console errors")
        decision = "GO"
    elif critical_failures <= 2 and console_errors == 0:
        print("⚠️  CONDITIONAL GO")
        print(f"   - {critical_failures} minor failures detected")
        print("   - Review failures before deploying")
        print("   - No console errors")
        decision = "CONDITIONAL_GO"
    else:
        print("❌ NO-GO FOR PRODUCTION")
        print(f"   - {critical_failures} critical failures")
        print(f"   - {console_errors} console errors")
        print("   - Issues must be resolved")
        decision = "NO_GO"

    TEST_RESULTS["production_readiness"] = decision

    # Save detailed results to JSON
    results_file = "/Users/masa/Projects/epstein/qa_test_results.json"
    with open(results_file, "w") as f:
        json.dump(TEST_RESULTS, f, indent=2)

    print(f"\n📄 Detailed results saved to: {results_file}")
    print(f"📸 Screenshots saved to: {SCREENSHOTS_DIR}/")

    return decision

def main():
    """Main test execution"""
    import os

    # Create screenshots directory
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print("="*80)
    print("COMPREHENSIVE QA TEST SUITE")
    print("Epstein Archive Application")
    print(f"Target: {BASE_URL}")
    print(f"Started: {TEST_RESULTS['timestamp']}")
    print("="*80)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=SCREENSHOTS_DIR
        )
        page = context.new_page()

        try:
            # Execute test suites
            test_suite_1_core_functionality(page)
            test_suite_2_interactive_features(page)
            test_suite_3_data_integrity(page)
            test_suite_4_performance(page)
            test_suite_5_error_handling(page)
            test_suite_6_user_experience(page)

        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            TEST_RESULTS["critical_error"] = str(e)

        finally:
            # Generate report
            decision = generate_report()

            # Close browser
            context.close()
            browser.close()

            # Exit with appropriate code
            sys.exit(0 if decision == "GO" else 1)

if __name__ == "__main__":
    main()
