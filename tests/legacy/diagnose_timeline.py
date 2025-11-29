#!/usr/bin/env python3
"""
Timeline Visibility Diagnostic Script
Uses Playwright to capture real browser state and identify timeline visibility issues
"""

import asyncio
import json

from playwright.async_api import async_playwright


async def diagnose_timeline():
    async with async_playwright() as p:
        # Launch browser in headed mode so we can see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        # Collect console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": str(msg.location)
        }))

        # Collect errors
        errors = []
        page.on("pageerror", lambda error: errors.append({
            "message": str(error),
        }))

        try:
            print("🌐 Navigating to http://localhost:8081/...")
            await page.goto("http://localhost:8081/", wait_until="load", timeout=10000)

            # Wait for page to load
            await asyncio.sleep(2)

            print("📸 Taking initial screenshot...")
            await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_initial.png", full_page=True)

            # Try to find and click Timeline tab
            print("🔍 Looking for Timeline tab...")
            timeline_selectors = [
                'button:has-text("Timeline")',
                'a:has-text("Timeline")',
                '[data-view="timeline"]',
                '.view-tab:has-text("Timeline")',
                "#timeline-tab",
                "text=Timeline"
            ]

            clicked = False
            for selector in timeline_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        print(f"✅ Found Timeline tab with selector: {selector}")
                        await element.click()
                        clicked = True
                        break
                except Exception:
                    # Try next selector
                    continue

            if not clicked:
                print("⚠️  Could not find Timeline tab button. Available buttons:")
                buttons = await page.locator("button").all()
                for btn in buttons:
                    text = await btn.text_content()
                    print(f'  - Button: "{text}"')

            # Wait for any animations/transitions
            await asyncio.sleep(1)

            print("📸 Taking timeline screenshot...")
            await page.screenshot(path="/Users/masa/Projects/epstein/screenshot_timeline.png", full_page=True)

            # Extract comprehensive diagnostics
            print("🔬 Extracting diagnostics...")
            diagnostics = await page.evaluate("""
                () => {
                    const getElementInfo = (selector) => {
                        const el = document.querySelector(selector);
                        if (!el) return { exists: false, selector };

                        const rect = el.getBoundingClientRect();
                        const styles = window.getComputedStyle(el);

                        return {
                            exists: true,
                            selector,
                            visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none' && styles.visibility !== 'hidden',
                            rect: {
                                top: rect.top,
                                left: rect.left,
                                width: rect.width,
                                height: rect.height,
                                bottom: rect.bottom,
                                right: rect.right
                            },
                            styles: {
                                display: styles.display,
                                visibility: styles.visibility,
                                opacity: styles.opacity,
                                position: styles.position,
                                zIndex: styles.zIndex,
                                overflow: styles.overflow,
                                overflowY: styles.overflowY,
                                height: styles.height,
                                maxHeight: styles.maxHeight,
                                minHeight: styles.minHeight,
                                paddingTop: styles.paddingTop,
                                paddingBottom: styles.paddingBottom,
                                marginTop: styles.marginTop,
                                marginBottom: styles.marginBottom
                            },
                            innerHTML_length: el.innerHTML.length,
                            childCount: el.children.length,
                            classList: Array.from(el.classList),
                            scrollHeight: el.scrollHeight,
                            clientHeight: el.clientHeight
                        };
                    };

                    return {
                        timelineView: getElementInfo('#timeline-view'),
                        timelineEvents: getElementInfo('#timeline-events'),
                        timelineContainer: getElementInfo('.timeline-container'),
                        pageContent: getElementInfo('.page-content'),
                        mainContent: getElementInfo('#main-content'),
                        currentView: document.querySelector('.view.active')?.id || 'none',
                        allViews: Array.from(document.querySelectorAll('.view')).map(v => ({
                            id: v.id,
                            active: v.classList.contains('active'),
                            display: window.getComputedStyle(v).display,
                            height: window.getComputedStyle(v).height
                        })),
                        timelineEventCount: document.querySelectorAll('.timeline-event').length,
                        timelineItemCount: document.querySelectorAll('.timeline-item').length,
                        monthSliders: document.querySelectorAll('.month-slider').length,
                        bodyHeight: document.body.scrollHeight,
                        viewportHeight: window.innerHeight,
                        scrollY: window.scrollY
                    };
                }
            """)

            print("\n" + "="*80)
            print("DIAGNOSTICS RESULTS")
            print("="*80)
            print(json.dumps(diagnostics, indent=2))

            print("\n" + "="*80)
            print("CONSOLE MESSAGES")
            print("="*80)
            for msg in console_messages:
                print(f"[{msg['type']}] {msg['text']}")

            print("\n" + "="*80)
            print("JAVASCRIPT ERRORS")
            print("="*80)
            if errors:
                for err in errors:
                    print(f"❌ {err['message']}")
            else:
                print("✅ No JavaScript errors detected")

            # Get HTML structure of timeline area
            timeline_html = await page.evaluate("""
                () => {
                    const view = document.getElementById('timeline-view');
                    if (!view) return 'Timeline view not found';

                    const getStructure = (el, depth = 0) => {
                        if (depth > 5) return '';
                        const indent = '  '.repeat(depth);
                        const rect = el.getBoundingClientRect();
                        const styles = window.getComputedStyle(el);

                        let result = `${indent}<${el.tagName.toLowerCase()}`;
                        if (el.id) result += ` id="${el.id}"`;
                        if (el.className) result += ` class="${el.className}"`;
                        result += ` [${Math.round(rect.width)}x${Math.round(rect.height)}]`;

                        // Add key flex properties
                        if (styles.display.includes('flex')) {
                            result += ` flex-dir:${styles.flexDirection}`;
                        }
                        if (styles.flex !== '0 1 auto') {
                            result += ` flex:${styles.flex}`;
                        }

                        result += '>\\n';

                        for (let child of el.children) {
                            result += getStructure(child, depth + 1);
                        }

                        return result;
                    };

                    return getStructure(view);
                }
            """)

            print("\n" + "="*80)
            print("TIMELINE HTML STRUCTURE")
            print("="*80)
            print(timeline_html)

            # Check if page-content exists in the DOM at all
            page_content_exists = await page.evaluate("""
                () => {
                    const timelineView = document.getElementById('timeline-view');
                    const pageContent = timelineView?.querySelector('.page-content');
                    const allPageContents = document.querySelectorAll('.page-content');

                    return {
                        inTimelineView: !!pageContent,
                        totalPageContents: allPageContents.length,
                        timelineViewHTML: timelineView?.innerHTML.substring(0, 500),
                        pageContentParent: pageContent?.parentElement?.id || 'none',
                        pageContentDisplay: pageContent ? window.getComputedStyle(pageContent).display : 'not found'
                    };
                }
            """)

            print("\n" + "="*80)
            print("PAGE-CONTENT DEBUG")
            print("="*80)
            print(json.dumps(page_content_exists, indent=2))

            # Save diagnostics to file
            output = {
                "diagnostics": diagnostics,
                "console_messages": console_messages,
                "errors": errors,
                "timeline_html": timeline_html
            }

            with open("/Users/masa/Projects/epstein/timeline_diagnostics.json", "w") as f:
                json.dump(output, f, indent=2)

            print("\n" + "="*80)
            print("✅ Diagnostics complete!")
            print("📸 Screenshots saved:")
            print("   - screenshot_initial.png")
            print("   - screenshot_timeline.png")
            print("📄 Full diagnostics saved: timeline_diagnostics.json")
            print("="*80)

            # Analyze the issue
            print("\n" + "="*80)
            print("ISSUE ANALYSIS")
            print("="*80)

            timeline_view = diagnostics["timelineView"]
            timeline_events = diagnostics["timelineEvents"]

            if not timeline_view["exists"]:
                print("❌ CRITICAL: #timeline-view element does not exist!")
            elif not timeline_view["visible"]:
                print("❌ CRITICAL: #timeline-view exists but is not visible!")
                print(f"   Display: {timeline_view['styles']['display']}")
                print(f"   Visibility: {timeline_view['styles']['visibility']}")
                print(f"   Size: {timeline_view['rect']['width']}x{timeline_view['rect']['height']}")
                print(f"   Height CSS: {timeline_view['styles']['height']}")
            else:
                print(f"✅ #timeline-view is visible ({timeline_view['rect']['width']}x{timeline_view['rect']['height']})")

            if not timeline_events["exists"]:
                print("❌ CRITICAL: #timeline-events element does not exist!")
            elif not timeline_events["visible"]:
                print("❌ CRITICAL: #timeline-events exists but is not visible!")
                print(f"   Display: {timeline_events['styles']['display']}")
                print(f"   Visibility: {timeline_events['styles']['visibility']}")
                print(f"   Size: {timeline_events['rect']['width']}x{timeline_events['rect']['height']}")
                print(f"   Height CSS: {timeline_events['styles']['height']}")
            else:
                print(f"✅ #timeline-events is visible ({timeline_events['rect']['width']}x{timeline_events['rect']['height']})")

            print(f"\n📊 Timeline events found: {diagnostics['timelineEventCount']}")
            print(f"📊 Timeline items found: {diagnostics['timelineItemCount']}")

            if diagnostics["currentView"] != "timeline-view":
                print(f"⚠️  Current active view: {diagnostics['currentView']} (expected: timeline-view)")

            # Keep browser open for manual inspection
            print("\n🔍 Browser will remain open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)

        except Exception as error:
            print(f"❌ Error during diagnosis: {error}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(diagnose_timeline())
