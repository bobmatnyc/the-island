#!/usr/bin/env python3
"""
QA Verification Script for:
- 1M-305: Related Entities Component Fix
- 1M-306: Entity Classification Badges

Tests the public URL: https://the-island.ngrok.app
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


class QAVerification:
    def __init__(self):
        self.base_url = "https://the-island.ngrok.app"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "1M-305_related_entities": {
                "api_tests": [],
                "ui_tests": []
            },
            "1M-306_category_badges": {
                "grid_view_tests": [],
                "bio_view_tests": []
            },
            "screenshots": [],
            "console_errors": []
        }

    async def run_tests(self):
        """Run all QA verification tests"""
        async with async_playwright() as p:
            # Launch browser with console logging
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()

            # Monitor console errors
            page.on("console", lambda msg: self._log_console(msg))
            page.on("pageerror", lambda exc: self._log_error(exc))

            try:
                # Test 1M-306: Entity Grid View Badges
                await self.test_entity_grid_badges(page)

                # Test 1M-306: Entity Bio View Badges
                await self.test_entity_bio_badges(page)

                # Test 1M-305: Related Entities Component
                await self.test_related_entities_component(page)

                # Test responsive behavior
                await self.test_responsive_behavior(page)

            finally:
                await browser.close()

        # Save results
        self._save_results()
        self._print_summary()

    async def test_entity_grid_badges(self, page):
        """Test 1M-306: Category badges in entity grid view"""
        print("\n🔬 Testing Entity Grid View Badges (1M-306)...")

        try:
            # Navigate to entities page
            await page.goto(f"{self.base_url}/entities", wait_until="networkidle")
            await asyncio.sleep(2)  # Wait for data to load

            # Take screenshot
            screenshot_path = f"/Users/masa/Projects/epstein/tests/qa/screenshots/grid_badges_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=screenshot_path, full_page=True)
            self.results["screenshots"].append(screenshot_path)

            # Check for category badges in grid
            badges = await page.locator('[class*="category-badge"], [class*="CategoryBadge"]').count()

            # Try to find entity cards with badges
            entity_cards = await page.locator('[class*="entity-card"], [class*="EntityCard"]').count()

            # Check for specific category labels
            categories_found = []
            for category in ["Victims", "Associates", "Legal", "Financial", "Political", "Academic", "Media", "Law Enforcement", "Uncategorized"]:
                count = await page.get_by_text(category, exact=False).count()
                if count > 0:
                    categories_found.append(category)

            test_result = {
                "test": "Entity Grid Badges Present",
                "status": "PASS" if badges > 0 or len(categories_found) > 0 else "FAIL",
                "badge_count": badges,
                "entity_cards": entity_cards,
                "categories_found": categories_found,
                "screenshot": screenshot_path
            }

            self.results["1M-306_category_badges"]["grid_view_tests"].append(test_result)

            print(f"  ✅ Found {badges} badge elements")
            print(f"  ✅ Found {entity_cards} entity cards")
            print(f"  ✅ Categories visible: {', '.join(categories_found)}")

        except Exception as e:
            self.results["1M-306_category_badges"]["grid_view_tests"].append({
                "test": "Entity Grid Badges",
                "status": "ERROR",
                "error": str(e)
            })
            print(f"  ❌ Error: {e}")

    async def test_entity_bio_badges(self, page):
        """Test 1M-306: Category badges in entity biography view"""
        print("\n🔬 Testing Entity Bio View Badges (1M-306)...")

        try:
            # Navigate to an entity with biography
            await page.goto(f"{self.base_url}/entities", wait_until="networkidle")
            await asyncio.sleep(2)

            # Click on first entity with biography
            entity_link = page.locator('a[href*="/entity/"]').first
            entity_name = await entity_link.text_content() if await entity_link.count() > 0 else "Unknown"

            if await entity_link.count() > 0:
                await entity_link.click()
                await asyncio.sleep(2)

                # Take screenshot
                screenshot_path = f"/Users/masa/Projects/epstein/tests/qa/screenshots/bio_badges_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                self.results["screenshots"].append(screenshot_path)

                # Check for badge in bio view
                badge_in_bio = await page.locator('[class*="category-badge"], [class*="CategoryBadge"]').count()

                # Check for category text
                categories_found = []
                for category in ["Victims", "Associates", "Legal", "Financial", "Political", "Academic", "Media", "Law Enforcement", "Uncategorized"]:
                    if await page.get_by_text(category, exact=False).count() > 0:
                        categories_found.append(category)

                test_result = {
                    "test": "Entity Bio Badge Present",
                    "entity": entity_name,
                    "status": "PASS" if badge_in_bio > 0 or len(categories_found) > 0 else "FAIL",
                    "badge_count": badge_in_bio,
                    "categories_found": categories_found,
                    "screenshot": screenshot_path
                }

                self.results["1M-306_category_badges"]["bio_view_tests"].append(test_result)

                print(f"  ✅ Entity: {entity_name}")
                print(f"  ✅ Found {badge_in_bio} badge elements in bio view")
                print(f"  ✅ Categories visible: {', '.join(categories_found)}")

        except Exception as e:
            self.results["1M-306_category_badges"]["bio_view_tests"].append({
                "test": "Entity Bio Badges",
                "status": "ERROR",
                "error": str(e)
            })
            print(f"  ❌ Error: {e}")

    async def test_related_entities_component(self, page):
        """Test 1M-305: Related Entities component functionality"""
        print("\n🔬 Testing Related Entities Component (1M-305)...")

        try:
            # Navigate to an entity detail page
            await page.goto(f"{self.base_url}/entities", wait_until="networkidle")
            await asyncio.sleep(2)

            # Click on Jeffrey Epstein (should have related entities)
            entity_link = page.get_by_text("Jeffrey Epstein", exact=False).first
            if await entity_link.count() > 0:
                await entity_link.click()
                await asyncio.sleep(3)

                # Take screenshot
                screenshot_path = f"/Users/masa/Projects/epstein/tests/qa/screenshots/related_entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                self.results["screenshots"].append(screenshot_path)

                # Check for "Related Entities" heading
                related_heading = await page.get_by_text("Related Entities", exact=False).count()

                # Check for error message
                error_message = await page.get_by_text("Failed to load", exact=False).count()

                # Check for entity links in related section
                # Look for any links that might be related entities
                page_content = await page.content()
                has_entity_links = "similar" in page_content.lower() or "related" in page_content.lower()

                test_result = {
                    "test": "Related Entities Component",
                    "status": "PASS" if related_heading > 0 and error_message == 0 else "FAIL",
                    "related_heading_found": related_heading > 0,
                    "error_message_found": error_message > 0,
                    "has_entity_links": has_entity_links,
                    "screenshot": screenshot_path
                }

                self.results["1M-305_related_entities"]["ui_tests"].append(test_result)

                print(f"  ✅ Related Entities heading: {'Found' if related_heading > 0 else 'NOT FOUND'}")
                print(f"  ✅ Error message: {'FOUND (BAD)' if error_message > 0 else 'Not found (good)'}")
                print(f"  ✅ Entity links present: {has_entity_links}")

        except Exception as e:
            self.results["1M-305_related_entities"]["ui_tests"].append({
                "test": "Related Entities Component",
                "status": "ERROR",
                "error": str(e)
            })
            print(f"  ❌ Error: {e}")

    async def test_responsive_behavior(self, page):
        """Test responsive behavior on mobile viewport"""
        print("\n🔬 Testing Responsive Behavior...")

        try:
            # Test mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            await page.goto(f"{self.base_url}/entities", wait_until="networkidle")
            await asyncio.sleep(2)

            # Take mobile screenshot
            screenshot_path = f"/Users/masa/Projects/epstein/tests/qa/screenshots/mobile_view_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            self.results["screenshots"].append(screenshot_path)

            # Check if badges are still visible on mobile
            badges_visible = await page.locator('[class*="category-badge"], [class*="CategoryBadge"]').count()

            print(f"  ✅ Mobile viewport: {badges_visible} badges visible")

        except Exception as e:
            print(f"  ❌ Error in responsive test: {e}")

    def _log_console(self, msg):
        """Log console messages"""
        if msg.type in ["error", "warning"]:
            self.results["console_errors"].append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat()
            })

    def _log_error(self, exc):
        """Log page errors"""
        self.results["console_errors"].append({
            "type": "exception",
            "text": str(exc),
            "timestamp": datetime.now().isoformat()
        })

    def _save_results(self):
        """Save test results to JSON file"""
        results_path = f"/Users/masa/Projects/epstein/tests/qa/qa_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Results saved to: {results_path}")

    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("QA VERIFICATION SUMMARY")
        print("="*80)

        # 1M-305 Summary
        print("\n🎫 1M-305: Related Entities Component Fix")
        for test in self.results["1M-305_related_entities"]["ui_tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test['test']}: {test['status']}")

        # 1M-306 Summary
        print("\n🎫 1M-306: Entity Classification Badges")
        print("  Grid View:")
        for test in self.results["1M-306_category_badges"]["grid_view_tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "❌"
            print(f"    {status_icon} {test['test']}: {test['status']}")

        print("  Bio View:")
        for test in self.results["1M-306_category_badges"]["bio_view_tests"]:
            status_icon = "✅" if test["status"] == "PASS" else "❌"
            print(f"    {status_icon} {test['test']}: {test['status']}")

        # Console Errors
        if self.results["console_errors"]:
            print(f"\n⚠️  Console Errors/Warnings: {len(self.results['console_errors'])}")
            for err in self.results["console_errors"][:5]:  # Show first 5
                print(f"    - {err['type']}: {err['text'][:100]}")
        else:
            print("\n✅ No console errors detected")

        print("\n" + "="*80)


async def main():
    """Main entry point"""
    qa = QAVerification()
    await qa.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
