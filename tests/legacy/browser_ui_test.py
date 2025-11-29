#!/usr/bin/env python3
"""
Browser UI Test - Visual verification of all tabs
Tests actual UI interaction and takes screenshots
"""

import os
import time

from playwright.sync_api import sync_playwright


BASE_URL = "http://localhost:8081"
SCREENSHOTS_DIR = "/Users/masa/Projects/epstein/qa_screenshots"

def test_ui():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    print("="*80)
    print("BROWSER UI TEST - VISUAL VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("="*80)

    with sync_playwright() as p:
        print("\n[1] Launching browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        # Capture console messages
        console_messages = []
        def handle_console(msg):
            console_messages.append({"type": msg.type, "text": msg.text})
            if msg.type in ["error", "warning"]:
                print(f"  [CONSOLE {msg.type.upper()}] {msg.text}")

        page.on("console", handle_console)

        try:
            # Test 1: Load homepage
            print("\n[2] Loading homepage...")
            start = time.time()
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            load_time = time.time() - start
            print(f"  ✅ Page loaded in {load_time:.2f}s")

            # Wait a bit for initial rendering
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/01_homepage.png", full_page=True)
            print("  📸 Screenshot saved: 01_homepage.png")

            # Test 2: Timeline Tab
            print("\n[3] Testing Timeline tab...")
            page.click('.tab:has-text("Timeline")')
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/02_timeline.png", full_page=True)
            print("  ✅ Timeline tab loaded")
            print("  📸 Screenshot saved: 02_timeline.png")

            # Test 3: Network Tab
            print("\n[4] Testing Network tab...")
            page.click('.tab:has-text("Network")')
            page.wait_for_timeout(3000)  # Network graph takes time to render
            page.screenshot(path=f"{SCREENSHOTS_DIR}/03_network.png", full_page=True)
            print("  ✅ Network tab loaded")
            print("  📸 Screenshot saved: 03_network.png")

            # Test 4: Flights Tab
            print("\n[5] Testing Flights tab...")
            page.click('.tab:has-text("Flights")')
            page.wait_for_timeout(3000)  # Map takes time to render
            page.screenshot(path=f"{SCREENSHOTS_DIR}/04_flights.png", full_page=True)
            print("  ✅ Flights tab loaded")
            print("  📸 Screenshot saved: 04_flights.png")

            # Test 5: Entities Tab
            print("\n[6] Testing Entities tab...")
            page.click('.tab:has-text("Entities")')
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/05_entities.png", full_page=True)
            print("  ✅ Entities tab loaded")
            print("  📸 Screenshot saved: 05_entities.png")

            # Test entity card click
            print("\n[7] Testing entity card interaction...")
            entity_cards = page.query_selector_all('.entity-card, [class*="entity"]')
            if len(entity_cards) > 0:
                print(f"  Found {len(entity_cards)} entity cards")
                # Click first visible entity
                entity_cards[0].scroll_into_view_if_needed()
                entity_cards[0].click()
                page.wait_for_timeout(1000)
                page.screenshot(path=f"{SCREENSHOTS_DIR}/06_entity_detail.png", full_page=True)
                print("  ✅ Entity card clicked")
                print("  📸 Screenshot saved: 06_entity_detail.png")
            else:
                print("  ⚠️  No entity cards found")

            # Test 6: Documents Tab
            print("\n[8] Testing Documents tab...")
            page.click('.tab:has-text("Documents")')
            page.wait_for_timeout(2000)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/07_documents.png", full_page=True)
            print("  ✅ Documents tab loaded")
            print("  📸 Screenshot saved: 07_documents.png")

            # Console summary
            print("\n" + "="*80)
            print("CONSOLE MESSAGES SUMMARY")
            print("="*80)
            errors = [m for m in console_messages if m["type"] == "error"]
            warnings = [m for m in console_messages if m["type"] == "warning"]

            print(f"Total console messages: {len(console_messages)}")
            print(f"Errors: {len(errors)}")
            print(f"Warnings: {len(warnings)}")

            if errors:
                print("\n❌ Console Errors Found:")
                for err in errors[:5]:  # Show first 5
                    print(f"  - {err['text']}")

            if warnings:
                print("\n⚠️  Console Warnings:")
                for warn in warnings[:5]:  # Show first 5
                    print(f"  - {warn['text']}")

            # Final summary
            print("\n" + "="*80)
            print("TEST COMPLETE")
            print("="*80)
            print(f"✅ All screenshots saved to: {SCREENSHOTS_DIR}/")
            print("✅ Browser test completed successfully")

            # Keep browser open for 5 seconds for manual inspection
            print("\nBrowser will remain open for 5 seconds for inspection...")
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            page.screenshot(path=f"{SCREENSHOTS_DIR}/ERROR.png")
            raise

        finally:
            browser.close()

if __name__ == "__main__":
    test_ui()
