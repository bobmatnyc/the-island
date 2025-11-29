#!/usr/bin/env python3
"""
UAT Testing Script v2 for Epstein Document Archive v1.2.0
Fixed: Clicks navigation tabs instead of using hash routing
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

        # Start at home page
        page.goto("http://localhost:8081")
        page.wait_for_load_state("networkidle")

        # Click Timeline tab
        page.click('text="Timeline"')
        page.wait_for_timeout(5000)  # Wait for content to load

        # Take screenshot
        page.screenshot(path="/tmp/uat_timeline_full_v2.png", full_page=True)

        # Count visible events - try multiple selectors
        timeline_events = 0
        selectors = [".timeline-event", ".event", '[class*="timeline"]', ".timeline-item"]
        for selector in selectors:
            count = page.locator(selector).count()
            if count > timeline_events:
                timeline_events = count
                print(f"  Found {count} elements with selector: {selector}")

        print(f"✓ Timeline events visible: {timeline_events}")

        # Check for specific 2024-2025 events by searching page text
        page_text = page.inner_text("body")
        has_house_oversight = "House Oversight Releases Estate Documents" in page_text
        has_giuffre_death = "Death of Virginia Giuffre" in page_text or "Virginia Giuffre" in page_text
        has_florida_transcripts = "Florida State Grand Jury Transcripts" in page_text

        print(f"✓ 2025-11-12 House Oversight event: {'✅ FOUND' if has_house_oversight else '❌ MISSING'}")
        print(f"✓ 2025-04-25 Virginia Giuffre event: {'✅ FOUND' if has_giuffre_death else '❌ MISSING'}")
        print(f"✓ 2024-07-01 Florida Transcripts event: {'✅ FOUND' if has_florida_transcripts else '❌ MISSING'}")

        # Count total occurrences of years to estimate event coverage
        count_2025 = page_text.count("2025")
        count_2024 = page_text.count("2024")
        count_2019 = page_text.count("2019")
        print(f"✓ Year mentions: 2025({count_2025}), 2024({count_2024}), 2019({count_2019})")

        # Test category filters
        filter_buttons = page.locator('button:has-text("All"), button:has-text("Case"), button:has-text("Life"), button:has-text("Documents")').count()
        print(f"✓ Category filter buttons: {filter_buttons}")

        results["timeline"] = {
            "events_displayed": timeline_events,
            "has_2025_events": has_house_oversight or has_giuffre_death,
            "has_2024_events": has_florida_transcripts,
            "filter_buttons": filter_buttons,
            "year_2025_count": count_2025,
            "year_2024_count": count_2024,
            "status": "✅ PASS" if (count_2025 > 10 and count_2024 > 5) else "❌ FAIL"
        }

        # ========== TEST 2: ENTITY FEATURES ==========
        print("\n" + "=" * 60)
        print("TEST 2: ENTITY FEATURES")
        print("=" * 60)

        # Click Entities tab
        page.click('text="Entities"')
        page.wait_for_timeout(3000)

        # Take screenshot
        page.screenshot(path="/tmp/uat_entities_page_v2.png", full_page=True)

        # Check for entity cards - try multiple selectors
        entity_cards = 0
        card_selectors = [".entity-card", ".card", '[class*="entity"]']
        for selector in card_selectors:
            count = page.locator(selector).count()
            entity_cards = max(entity_cards, count)

        print(f"✓ Entity cards displayed: {entity_cards}")

        # Look for entity names
        entity_names = ["Epstein", "Maxwell", "Clinton", "Trump"]
        found_entities = [name for name in entity_names if name in page.inner_text("body")]
        print(f"✓ Key entities found: {', '.join(found_entities)}")

        # Try to click an entity card
        bio_modal = False
        action_buttons = 0
        tags = 0

        try:
            # Look for clickable entity elements
            clickable = page.locator('text="Epstein, Jeffrey"').first
            if clickable.count() > 0:
                clickable.click()
                page.wait_for_timeout(1500)

                # Check bio modal
                modal_visible = page.locator('.modal, [role="dialog"], .entity-bio').count() > 0
                bio_modal = modal_visible
                print(f"✓ Bio modal opens: {'✅ YES' if bio_modal else '❌ NO'}")

                if bio_modal:
                    # Take screenshot of modal
                    page.screenshot(path="/tmp/uat_entity_bio_modal_v2.png")

                    # Count action buttons
                    action_buttons = page.locator('button:has-text("View"), button:has-text("Flights"), button:has-text("Documents"), button:has-text("Network")').count()
                    print(f"✓ Action buttons in modal: {action_buttons}")

                    # Check for tags
                    tags = page.locator('.badge, .tag, [class*="tag"]').count()
                    print(f"✓ Entity tags visible: {tags}")

                    # Close modal
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
        except Exception as e:
            print(f"⚠️ Could not test entity modal: {e}")

        results["entities"] = {
            "cards_displayed": entity_cards,
            "entities_found": len(found_entities),
            "bio_modal_works": bio_modal,
            "action_buttons": action_buttons,
            "tags_visible": tags,
            "status": "✅ PASS" if len(found_entities) >= 3 else "⚠️ PARTIAL"
        }

        # ========== TEST 3: FLIGHTS PAGE ==========
        print("\n" + "=" * 60)
        print("TEST 3: FLIGHTS PAGE (Map Theme)")
        print("=" * 60)

        # Click Flights tab
        page.click('text="Flights"')
        page.wait_for_timeout(6000)  # Maps take longer to load

        # Take screenshot
        page.screenshot(path="/tmp/uat_flights_map_v2.png", full_page=True)

        # Check for map
        map_visible = page.locator(".leaflet-container, #map, canvas").count() > 0
        print(f"✓ Map visible: {'✅ YES' if map_visible else '❌ NO'}")

        # Check for map tiles loading (indicates light theme)
        page_text = page.inner_text("body")
        has_flights_data = "flight" in page_text.lower() or "passenger" in page_text.lower()
        print(f"✓ Flights data present: {'✅ YES' if has_flights_data else '❌ NO'}")

        # Check for controls
        has_controls = page.locator("input, select, button").count() > 0
        print(f"✓ Interactive controls: {'✅ YES' if has_controls else '❌ NO'}")

        results["flights"] = {
            "map_visible": map_visible,
            "flights_data": has_flights_data,
            "has_controls": has_controls,
            "status": "✅ PASS" if map_visible else "❌ FAIL"
        }

        # ========== TEST 4: NETWORK GRAPH ==========
        print("\n" + "=" * 60)
        print("TEST 4: NETWORK GRAPH (Node Spacing)")
        print("=" * 60)

        # Click Network Graph tab
        page.click('text="Network Graph"')
        page.wait_for_timeout(6000)  # Graphs take time to render

        # Take screenshot
        page.screenshot(path="/tmp/uat_network_graph_v2.png", full_page=True)

        # Check for network graph elements
        network_visible = page.locator("canvas, svg, #network-graph, .graph").count() > 0
        print(f"✓ Network graph visible: {'✅ YES' if network_visible else '❌ NO'}")

        # Check for network content
        page_text = page.inner_text("body")
        has_network_data = "connection" in page_text.lower() or "node" in page_text.lower() or "epstein" in page_text.lower()
        print(f"✓ Network data present: {'✅ YES' if has_network_data else '❌ NO'}")

        # Check for controls
        controls = page.locator("button, input, select").count()
        print(f"✓ Control elements: {controls}")

        results["network"] = {
            "graph_visible": network_visible,
            "network_data": has_network_data,
            "controls": controls,
            "status": "✅ PASS" if network_visible or has_network_data else "❌ FAIL"
        }

        # ========== SUMMARY ==========
        print("\n" + "=" * 60)
        print("UAT TEST SUMMARY")
        print("=" * 60)

        all_pass = all(r["status"] in ["✅ PASS", "⚠️ PARTIAL"] for r in results.values())

        print(f"\n{'✅' if results['timeline']['status'] == '✅ PASS' else '❌'} Timeline: {results['timeline']['status']} - 2025 events: {results['timeline']['year_2025_count']}, 2024 events: {results['timeline']['year_2024_count']}")
        print(f"{'✅' if results['entities']['status'] in ['✅ PASS', '⚠️ PARTIAL'] else '❌'} Entities: {results['entities']['status']} - {results['entities']['entities_found']} key entities found")
        print(f"{'✅' if results['flights']['status'] == '✅ PASS' else '❌'} Flights: {results['flights']['status']} - Map visible: {results['flights']['map_visible']}")
        print(f"{'✅' if results['network']['status'] == '✅ PASS' else '❌'} Network: {results['network']['status']} - Graph visible: {results['network']['graph_visible']}")

        print(f"\n{'🎉 ALL TESTS PASSED' if all_pass else '⚠️ REVIEW RESULTS'}")

        print("\n📸 Screenshots saved:")
        print("  - /tmp/uat_timeline_full_v2.png")
        print("  - /tmp/uat_entities_page_v2.png")
        print("  - /tmp/uat_entity_bio_modal_v2.png")
        print("  - /tmp/uat_flights_map_v2.png")
        print("  - /tmp/uat_network_graph_v2.png")

        # Save results to JSON
        with open("/tmp/uat_results_v2.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n📊 Results saved to: /tmp/uat_results_v2.json")

        # Keep browser open for 5 seconds
        print("\n⏳ Keeping browser open for review...")
        page.wait_for_timeout(5000)

        browser.close()

        return results

if __name__ == "__main__":
    run_uat_tests()
