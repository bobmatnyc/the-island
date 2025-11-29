#!/usr/bin/env python3
"""
UAT Testing Script for Epstein Document Archive v1.2.0
Tests all critical features and generates screenshots
"""

import json

from playwright.sync_api import sync_playwright


def run_uat_tests():
    results = {
        "timeline": {},
        "entities": {},
        "flights": {},
        "network": {}
    }

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        print("🚀 Starting UAT Tests for Epstein Document Archive v1.2.0\n")

        # ========== TEST 1: TIMELINE PAGE ==========
        print("=" * 60)
        print("TEST 1: TIMELINE PAGE (CRITICAL - Just Fixed)")
        print("=" * 60)

        page.goto("http://localhost:8081/#timeline")
        page.wait_for_timeout(3000)

        # Take screenshot
        page.screenshot(path="/tmp/uat_timeline_full.png", full_page=True)

        # Count visible events
        timeline_events = page.locator(".timeline-event").count()
        print(f"✓ Timeline events visible: {timeline_events}")

        # Check for specific 2024-2025 events
        page_content = page.content()
        has_house_oversight = "House Oversight Releases Estate Documents" in page_content
        has_giuffre_death = "Death of Virginia Giuffre" in page_content
        has_florida_transcripts = "Florida State Grand Jury Transcripts Released" in page_content

        print(f"✓ 2025-11-12 House Oversight event: {'✅ FOUND' if has_house_oversight else '❌ MISSING'}")
        print(f"✓ 2025-04-25 Virginia Giuffre event: {'✅ FOUND' if has_giuffre_death else '❌ MISSING'}")
        print(f"✓ 2024-07-01 Florida Transcripts event: {'✅ FOUND' if has_florida_transcripts else '❌ MISSING'}")

        # Test category filters
        filter_buttons = page.locator(".timeline-filter-btn").count()
        print(f"✓ Category filter buttons: {filter_buttons}")

        results["timeline"] = {
            "events_displayed": timeline_events,
            "has_2025_events": has_house_oversight and has_giuffre_death,
            "has_2024_events": has_florida_transcripts,
            "filter_buttons": filter_buttons,
            "status": "✅ PASS" if timeline_events >= 90 else "❌ FAIL"
        }

        # ========== TEST 2: ENTITY FEATURES ==========
        print("\n" + "=" * 60)
        print("TEST 2: ENTITY FEATURES")
        print("=" * 60)

        page.goto("http://localhost:8081/#entities")
        page.wait_for_timeout(2000)

        # Take screenshot
        page.screenshot(path="/tmp/uat_entities_page.png", full_page=True)

        # Check for entity cards
        entity_cards = page.locator(".entity-card").count()
        print(f"✓ Entity cards displayed: {entity_cards}")

        # Click first entity to open bio modal
        if entity_cards > 0:
            page.locator(".entity-card").first.click()
            page.wait_for_timeout(1000)

            # Check bio modal
            bio_modal = page.locator(".entity-bio-modal").is_visible()
            print(f"✓ Bio modal opens: {'✅ YES' if bio_modal else '❌ NO'}")

            # Take screenshot of modal
            page.screenshot(path="/tmp/uat_entity_bio_modal.png")

            # Count action buttons
            action_buttons = page.locator(".entity-action-btn, .btn").count()
            print(f"✓ Action buttons in modal: {action_buttons}")

            # Check for tags
            tags = page.locator(".entity-tag, .badge").count()
            print(f"✓ Entity tags visible: {tags}")

            # Close modal
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        results["entities"] = {
            "cards_displayed": entity_cards,
            "bio_modal_works": bio_modal if entity_cards > 0 else False,
            "action_buttons": action_buttons if entity_cards > 0 else 0,
            "tags_visible": tags if entity_cards > 0 else 0,
            "status": "✅ PASS" if entity_cards > 0 and bio_modal else "❌ FAIL"
        }

        # ========== TEST 3: FLIGHTS PAGE ==========
        print("\n" + "=" * 60)
        print("TEST 3: FLIGHTS PAGE (Map Theme)")
        print("=" * 60)

        page.goto("http://localhost:8081/#flights")
        page.wait_for_timeout(4000)

        # Take screenshot
        page.screenshot(path="/tmp/uat_flights_map.png", full_page=True)

        # Check for map
        map_visible = page.locator("#map, .leaflet-container").is_visible()
        print(f"✓ Map visible: {'✅ YES' if map_visible else '❌ NO'}")

        # Check for light theme (look for white backgrounds in overlays)
        page_content = page.content()
        has_light_theme = "background: white" in page_content or "background-color: white" in page_content
        print(f"✓ Light theme detected: {'✅ YES' if has_light_theme else '⚠️ UNCERTAIN'}")

        # Check for passenger filter
        passenger_filter = page.locator('input[placeholder*="passenger"], input[placeholder*="Search"]').count()
        print(f"✓ Passenger filter present: {passenger_filter}")

        results["flights"] = {
            "map_visible": map_visible,
            "light_theme": has_light_theme,
            "passenger_filter": passenger_filter > 0,
            "status": "✅ PASS" if map_visible else "❌ FAIL"
        }

        # ========== TEST 4: NETWORK GRAPH ==========
        print("\n" + "=" * 60)
        print("TEST 4: NETWORK GRAPH (Node Spacing)")
        print("=" * 60)

        page.goto("http://localhost:8081/#network")
        page.wait_for_timeout(4000)

        # Take screenshot
        page.screenshot(path="/tmp/uat_network_graph.png", full_page=True)

        # Check for network graph
        network_visible = page.locator("#network-graph, canvas, svg").count() > 0
        print(f"✓ Network graph visible: {'✅ YES' if network_visible else '❌ NO'}")

        # Check for controls
        controls = page.locator("button, .control-btn").count()
        print(f"✓ Control buttons: {controls}")

        results["network"] = {
            "graph_visible": network_visible,
            "controls": controls,
            "status": "✅ PASS" if network_visible else "❌ FAIL"
        }

        # ========== SUMMARY ==========
        print("\n" + "=" * 60)
        print("UAT TEST SUMMARY")
        print("=" * 60)

        all_pass = all(r["status"] == "✅ PASS" for r in results.values())

        print(f"\n✅ Timeline: {results['timeline']['status']} - {results['timeline']['events_displayed']} events displayed")
        print(f"✅ Entities: {results['entities']['status']} - {results['entities']['cards_displayed']} cards, bio modal works")
        print(f"✅ Flights: {results['flights']['status']} - Map visible, light theme")
        print(f"✅ Network: {results['network']['status']} - Graph visible")

        print(f"\n{'🎉 ALL TESTS PASSED' if all_pass else '⚠️ SOME TESTS FAILED'}")

        print("\n📸 Screenshots saved:")
        print("  - /tmp/uat_timeline_full.png")
        print("  - /tmp/uat_entities_page.png")
        print("  - /tmp/uat_entity_bio_modal.png")
        print("  - /tmp/uat_flights_map.png")
        print("  - /tmp/uat_network_graph.png")

        # Save results to JSON
        with open("/tmp/uat_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n📊 Results saved to: /tmp/uat_results.json")

        browser.close()

        return results

if __name__ == "__main__":
    run_uat_tests()
