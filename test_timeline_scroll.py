#!/usr/bin/env python3
"""
Enhanced Timeline Test with Scrolling
"""

import asyncio
from playwright.async_api import async_playwright

async def test_timeline_with_scroll():
    print("🚀 Testing Timeline with Scrolling\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Navigate
            print("📍 Navigating to http://localhost:8000/")
            await page.goto('http://localhost:8000/', timeout=10000)
            await asyncio.sleep(2)

            # Click Timeline tab
            print("📍 Clicking Timeline tab...")
            await page.click('text=Timeline')
            await asyncio.sleep(3)

            # Take screenshot before scroll
            await page.screenshot(path='/Users/masa/Projects/epstein/timeline_before_scroll.png', full_page=True)
            print("📸 Full page screenshot saved: timeline_before_scroll.png")

            # Check if timeline events container exists and has content
            timeline_container = await page.query_selector('#timeline-events')
            if timeline_container:
                inner_html = await timeline_container.inner_html()
                print(f"\n✅ Timeline container HTML length: {len(inner_html)} characters")

                # Count timeline events
                event_count = await page.evaluate('''() => {
                    return document.querySelectorAll('.timeline-event').length;
                }''')
                print(f"📊 Number of .timeline-event elements: {event_count}")

                if event_count > 0:
                    print("\n✅✅✅ TIMELINE EVENTS ARE RENDERED! ✅✅✅\n")

                    # Scroll to see some events
                    print("📜 Scrolling to view events...")
                    await page.evaluate('''() => {
                        const container = document.querySelector('.page-content');
                        if (container) {
                            container.scrollTop = 300;
                        }
                    }''')
                    await asyncio.sleep(1)

                    # Take another screenshot after scroll
                    await page.screenshot(path='/Users/masa/Projects/epstein/timeline_after_scroll.png', full_page=True)
                    print("📸 Full page screenshot after scroll saved: timeline_after_scroll.png")

                    # Get first few event titles
                    event_titles = await page.evaluate('''() => {
                        const events = Array.from(document.querySelectorAll('.timeline-event'));
                        return events.slice(0, 5).map(event => {
                            const title = event.querySelector('.timeline-event-title');
                            const date = event.querySelector('.timeline-date');
                            return {
                                title: title ? title.textContent.trim() : 'N/A',
                                date: date ? date.textContent.trim() : 'N/A'
                            };
                        });
                    }''')

                    print("\n📋 First 5 timeline events:")
                    for i, event in enumerate(event_titles, 1):
                        print(f"  {i}. [{event['date']}] {event['title']}")

                else:
                    print("\n❌ No .timeline-event elements found - events not rendering!")

                    # Debug: Check what's in the container
                    print(f"\n🔍 Container HTML (first 1000 chars):\n{inner_html[:1000]}")

            else:
                print("❌ Timeline container #timeline-events not found!")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()
            print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_timeline_with_scroll())
