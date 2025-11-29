#!/usr/bin/env python3
"""
Timeline Tab Browser Test with Console Monitoring
Tests the Timeline tab to identify why it's showing blank
"""

import asyncio
import json

from playwright.async_api import async_playwright


async def test_timeline_tab():
    print("🚀 Starting Timeline Tab Browser Test\n")

    async with async_playwright() as p:
        # Launch browser with console logging
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Console message handler
        console_messages = []

        def handle_console(msg):
            message_data = {
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            }
            console_messages.append(message_data)
            print(f"  [{msg.type.upper()}] {msg.text}")

        # Error handler
        errors = []

        def handle_error(error):
            error_data = {
                "message": str(error),
                "name": getattr(error, "name", "Error")
            }
            errors.append(error_data)
            print(f"  ❌ ERROR: {error}")

        page.on("console", handle_console)
        page.on("pageerror", handle_error)

        try:
            # Navigate to the main page
            print("📍 Step 1: Navigating to http://localhost:8000/")
            await page.goto("http://localhost:8000/", wait_until="networkidle", timeout=30000)
            print("✅ Page loaded\n")

            # Wait a moment for initial load
            await asyncio.sleep(2)

            # Take screenshot of initial state
            await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_01_initial.png")
            print("📸 Screenshot saved: screenshot_01_initial.png\n")

            # Find and click the Timeline tab
            print("📍 Step 2: Looking for Timeline tab...")

            # Try multiple selectors
            timeline_tab = None
            selectors = [
                'button[data-tab="timeline"]',
                '.tab-button[data-tab="timeline"]',
                "text=Timeline",
                '[data-tab="timeline"]'
            ]

            for selector in selectors:
                try:
                    timeline_tab = await page.query_selector(selector)
                    if timeline_tab:
                        print(f"✅ Found Timeline tab using selector: {selector}")
                        break
                except:
                    continue

            if not timeline_tab:
                print("❌ Timeline tab not found with any selector!")
                print("\nAvailable tabs:")
                tabs = await page.query_selector_all("button[data-tab]")
                for tab in tabs:
                    tab_name = await tab.get_attribute("data-tab")
                    print(f"  - {tab_name}")
                return

            # Click the Timeline tab
            print("🖱️  Clicking Timeline tab...")
            await timeline_tab.click()
            print("✅ Timeline tab clicked\n")

            # Wait for timeline to load
            print("⏳ Waiting 3 seconds for Timeline to render...")
            await asyncio.sleep(3)

            # Take screenshot after clicking
            await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_02_timeline.png")
            print("📸 Screenshot saved: screenshot_02_timeline.png\n")

            # Check for timeline container
            print("📍 Step 3: Checking Timeline DOM elements...")

            timeline_container = await page.query_selector("#timeline-events")
            if timeline_container:
                print("✅ #timeline-events container found")

                # Get inner HTML
                inner_html = await timeline_container.inner_html()
                print(f"📄 Container HTML length: {len(inner_html)} characters")

                if len(inner_html) > 100:
                    print(f"📄 First 500 chars:\n{inner_html[:500]}\n")
                else:
                    print(f"📄 Full HTML:\n{inner_html}\n")
            else:
                print("❌ #timeline-events container NOT found!\n")

            # Check if timeline data is loaded
            print("📍 Step 4: Checking JavaScript timeline data...")

            timeline_data_check = await page.evaluate("""() => {
                return {
                    timelineDataExists: typeof timelineData !== 'undefined',
                    timelineDataLength: typeof timelineData !== 'undefined' ? timelineData.length : 0,
                    filteredTimelineDataLength: typeof filteredTimelineData !== 'undefined' ? filteredTimelineData.length : 0,
                    loadTimelineFunctionExists: typeof loadTimeline === 'function',
                    renderTimelineFunctionExists: typeof renderTimeline === 'function'
                };
            }""")

            print("JavaScript State:")
            for key, value in timeline_data_check.items():
                print(f"  {key}: {value}")
            print()

            # Check network requests
            print("📍 Step 5: Checking network requests for timeline API...")
            await asyncio.sleep(1)

            # Try to trigger timeline load manually
            print("📍 Step 6: Manually calling loadTimeline()...")
            try:
                load_result = await page.evaluate("loadTimeline()")
                print(f"✅ loadTimeline() called: {load_result}")
                await asyncio.sleep(2)

                # Take screenshot after manual load
                await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_03_after_load.png")
                print("📸 Screenshot saved: screenshot_03_after_load.png\n")

                # Re-check timeline data
                timeline_data_check2 = await page.evaluate("""() => {
                    return {
                        timelineDataLength: typeof timelineData !== 'undefined' ? timelineData.length : 0,
                        filteredTimelineDataLength: typeof filteredTimelineData !== 'undefined' ? filteredTimelineData.length : 0
                    };
                }""")
                print("Timeline data after manual load:")
                for key, value in timeline_data_check2.items():
                    print(f"  {key}: {value}")
                print()

            except Exception as e:
                print(f"❌ Error calling loadTimeline(): {e}\n")

            # Final wait
            print("⏳ Waiting 5 seconds for final state...")
            await asyncio.sleep(5)

            # Final screenshot
            await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_04_final.png")
            print("📸 Screenshot saved: screenshot_04_final.png\n")

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Print summary
            print("\n" + "="*60)
            print("SUMMARY")
            print("="*60)

            print(f"\nConsole Messages: {len(console_messages)}")
            if console_messages:
                print("\nRecent console messages:")
                for msg in console_messages[-20:]:  # Last 20 messages
                    print(f"  [{msg['type']}] {msg['text'][:100]}")

            print(f"\nErrors: {len(errors)}")
            if errors:
                print("\nAll errors:")
                for err in errors:
                    print(f"  ❌ {err['message']}")

            # Save detailed logs
            with open("/Users/masa/Projects/epstein/timeline_test_console.json", "w") as f:
                json.dump({
                    "console_messages": console_messages,
                    "errors": errors
                }, f, indent=2)
            print("\n💾 Detailed logs saved to: timeline_test_console.json")

            await browser.close()
            print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_timeline_tab())
