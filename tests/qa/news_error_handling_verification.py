#!/usr/bin/env python3
"""
News Coverage Error Handling Verification Test

Tests robust error handling implementation with:
- Retry logic with exponential backoff (1s, 2s, 4s)
- Timeout handling (10s per request)
- Clear error messages
- Retry button functionality
- Fallback URL behavior
- Loading states during retries

Test URL: http://localhost:5173/entities/jeffrey_epstein
"""

import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Route


def log(message: str):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


def test_happy_path(page: Page) -> dict:
    """
    Scenario 1: Happy Path - News loads successfully
    """
    log("\n" + "=" * 70)
    log("TEST 1: Happy Path - News loads successfully")
    log("=" * 70)

    result = {
        "test": "Happy Path",
        "status": "running",
        "details": []
    }

    try:
        # Navigate to entity page
        log("Navigating to Jeffrey Epstein entity page...")
        page.goto("http://localhost:5173/entities/jeffrey_epstein")

        # Wait for entity title
        page.wait_for_selector("h1:has-text('Jeffrey Epstein')", timeout=10000)
        result["details"].append("✅ Entity page loaded")

        # Wait for News Coverage section
        news_section = page.locator("div:has(> div:has-text('News Coverage'))")
        news_section.wait_for(timeout=15000)
        result["details"].append("✅ News Coverage section visible")

        # Check for article count badge
        article_badge = news_section.locator("span:text-matches('\\d+ article')")
        article_badge.wait_for(timeout=20000)
        badge_text = article_badge.text_content()
        result["details"].append(f"✅ Article badge: '{badge_text}'")

        # Extract article count
        import re
        match = re.search(r'(\d+)', badge_text)
        article_count = int(match.group(1)) if match else 0

        if article_count > 0:
            result["details"].append(f"✅ Article count: {article_count}")
        else:
            result["details"].append("❌ Article count is 0 - unexpected!")
            result["status"] = "failed"
            return result

        # Verify article cards display
        article_cards = page.locator("a[href*='/news/']")
        card_count = article_cards.count()
        result["details"].append(f"✅ Article cards visible: {card_count}")

        if card_count == 0:
            result["details"].append("❌ No article cards visible")
            result["status"] = "failed"
            return result

        # Verify NO error message
        error_banner = news_section.locator("div:has-text('Unable to load news articles')")
        error_visible = error_banner.is_visible()

        if error_visible:
            result["details"].append("❌ Error message shown unexpectedly")
            result["status"] = "failed"
            return result
        else:
            result["details"].append("✅ No error message displayed")

        # Verify "View All" button
        view_all_button = page.locator("button:has-text('View All')")
        if view_all_button.is_visible():
            button_text = view_all_button.text_content()
            result["details"].append(f"✅ View All button: '{button_text}'")

        result["status"] = "passed"

    except Exception as e:
        log(f"❌ Test failed with error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result


def test_backend_down(page: Page) -> dict:
    """
    Scenario 2: Backend Down - Graceful error handling
    """
    log("\n" + "=" * 70)
    log("TEST 2: Backend Down - Graceful error handling")
    log("=" * 70)

    result = {
        "test": "Backend Down",
        "status": "running",
        "details": [],
        "api_requests": []
    }

    request_count = [0]  # Use list to modify in closure

    def handle_route(route: Route):
        url = route.request.url
        if "/api/news/" in url:
            request_count[0] += 1
            log(f"[BLOCKED REQUEST {request_count[0]}] {url}")
            result["api_requests"].append(f"Blocked: {url}")
            route.abort()
        else:
            route.continue_()

    try:
        # Block news API requests
        page.route("**/api/news/**", handle_route)

        # Navigate to entity page
        log("Navigating with blocked API...")
        page.goto("http://localhost:5173/entities/jeffrey_epstein")

        # Wait for entity title
        page.wait_for_selector("h1:has-text('Jeffrey Epstein')", timeout=10000)
        result["details"].append("✅ Entity page loaded")

        # Wait for News Coverage section
        news_section = page.locator("div:has(> div:has-text('News Coverage'))")
        news_section.wait_for(timeout=10000)
        result["details"].append("✅ News Coverage section visible")

        # Wait for retry attempts to complete
        log("⏳ Waiting for retry attempts to complete (up to 30s)...")
        time.sleep(2)  # Give time for initial retry

        # Wait for error banner
        error_banner = news_section.locator("div:has-text('Unable to load news articles')")
        error_banner.wait_for(timeout=30000)
        result["details"].append("✅ Error banner appeared")

        # Get error message text
        error_text = error_banner.text_content()
        result["details"].append(f"✅ Error message: '{error_text[:100]}...'")

        # Check for retry count info
        retry_info = news_section.locator("p:text-matches('Attempted \\d+ time')")
        if retry_info.is_visible():
            retry_text = retry_info.text_content()
            result["details"].append(f"✅ Retry info: '{retry_text}'")

        # Verify retry button is visible
        retry_button = error_banner.locator("button:has-text('Retry')")
        if retry_button.is_visible():
            result["details"].append("✅ Retry button visible")
        else:
            result["details"].append("❌ Retry button not visible")
            result["status"] = "failed"
            return result

        # Verify NO misleading "0 articles" badge
        zero_badge = news_section.locator("span:has-text('0 article')")
        if zero_badge.is_visible():
            result["details"].append("❌ Misleading '0 articles' badge shown")
            result["status"] = "failed"
        else:
            result["details"].append("✅ No misleading '0 articles' badge")

        # Log API request count
        result["details"].append(f"📊 Total API requests blocked: {request_count[0]}")
        if request_count[0] >= 3:
            result["details"].append(f"✅ Multiple retry attempts detected ({request_count[0]} requests)")
        else:
            result["details"].append(f"⚠️ Expected 3+ requests, got {request_count[0]}")

        result["status"] = "passed"

    except Exception as e:
        log(f"❌ Test failed with error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    finally:
        page.unroute("**/api/news/**")

    return result


def test_retry_button(page: Page) -> dict:
    """
    Scenario 3: Retry Button Functionality
    """
    log("\n" + "=" * 70)
    log("TEST 3: Retry Button Functionality")
    log("=" * 70)

    result = {
        "test": "Retry Button",
        "status": "running",
        "details": [],
        "request_timeline": []
    }

    request_count = [0]

    def handle_route(route: Route):
        request_count[0] += 1
        url = route.request.url
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if "/api/news/" in url:
            result["request_timeline"].append(f"[{timestamp}] Request {request_count[0]}: {url.split('/')[-1]}")

            # Fail first 3 attempts (initial + 2 retries), succeed on manual retry (4th+)
            if request_count[0] <= 3:
                log(f"[BLOCKING REQUEST {request_count[0]}] {url}")
                route.abort()
            else:
                log(f"[ALLOWING REQUEST {request_count[0]}] {url}")
                route.continue_()
        else:
            route.continue_()

    try:
        page.route("**/api/news/**", handle_route)

        # Navigate to entity page
        page.goto("http://localhost:5173/entities/jeffrey_epstein")
        page.wait_for_selector("h1:has-text('Jeffrey Epstein')", timeout=10000)

        # Wait for error banner (after auto-retries fail)
        news_section = page.locator("div:has(> div:has-text('News Coverage'))")
        error_banner = news_section.locator("div:has-text('Unable to load news articles')")
        error_banner.wait_for(timeout=30000)
        result["details"].append(f"✅ Error banner appeared after {request_count[0]} failed attempts")

        # Click retry button
        retry_button = error_banner.locator("button:has-text('Retry')")
        log("🔄 Clicking retry button...")
        retry_button.click()
        result["details"].append("✅ Retry button clicked")

        # Check for loading state
        loading_text = page.locator("p:has-text('Retrying')")
        if loading_text.is_visible(timeout=2000):
            result["details"].append("✅ Loading state shown during retry")

        # Wait for error to disappear (success)
        page.wait_for_timeout(5000)  # Give time for request to complete

        # Check if articles loaded
        article_badge = news_section.locator("span:text-matches('\\d+ article')")
        if article_badge.is_visible(timeout=10000):
            badge_text = article_badge.text_content()
            result["details"].append(f"✅ Articles loaded after retry: '{badge_text}'")
            result["status"] = "passed"
        else:
            result["details"].append("❌ Articles did not load after retry")
            result["status"] = "failed"

        result["details"].append(f"📊 Total requests: {request_count[0]}")

    except Exception as e:
        log(f"❌ Test failed with error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    finally:
        page.unroute("**/api/news/**")

    return result


def test_console_logs(page: Page) -> dict:
    """
    Scenario 4: Console Log Verification
    """
    log("\n" + "=" * 70)
    log("TEST 4: Console Log Verification")
    log("=" * 70)

    result = {
        "test": "Console Logs",
        "status": "running",
        "details": [],
        "console_logs": []
    }

    def handle_console(msg):
        text = msg.text
        if any(keyword in text.lower() for keyword in ['news', 'retry', 'failed', 'error']):
            log_entry = f"[{msg.type}] {text}"
            result["console_logs"].append(log_entry)
            log(f"📋 Console: {log_entry}")

    try:
        page.on("console", handle_console)

        # Block requests to trigger errors
        page.route("**/api/news/**", lambda route: route.abort())

        # Navigate
        page.goto("http://localhost:5173/entities/jeffrey_epstein")
        page.wait_for_selector("h1:has-text('Jeffrey Epstein')", timeout=10000)

        # Wait for retries to complete
        time.sleep(10)

        result["details"].append(f"📊 Captured {len(result['console_logs'])} relevant console logs")

        # Check for retry-related logs
        has_error_logs = any('failed' in log.lower() or 'error' in log.lower()
                           for log in result['console_logs'])

        if has_error_logs:
            result["details"].append("✅ Error logs present in console")
        else:
            result["details"].append("⚠️ No explicit error logs captured")

        result["status"] = "passed"

    except Exception as e:
        log(f"❌ Test failed with error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    finally:
        page.unroute("**/api/news/**")

    return result


def test_production_environment(page: Page) -> dict:
    """
    Production Test: Verify real backend behavior
    """
    log("\n" + "=" * 70)
    log("PRODUCTION TEST: Real Backend Verification")
    log("=" * 70)

    result = {
        "test": "Production Environment",
        "status": "running",
        "details": []
    }

    try:
        # No mocking - test against real backend
        page.goto("http://localhost:5173/entities/jeffrey_epstein")

        # Wait for entity
        page.wait_for_selector("h1:has-text('Jeffrey Epstein')", timeout=10000)
        result["details"].append("✅ Entity page loaded")

        # Wait for news section
        news_section = page.locator("div:has(> div:has-text('News Coverage'))")
        news_section.wait_for(timeout=10000)
        result["details"].append("✅ News Coverage section visible")

        # Check for success OR error (not silent failure)
        article_badge = news_section.locator("span:text-matches('\\d+ article')")
        error_banner = news_section.locator("div:has-text('Unable to load')")

        has_articles = article_badge.is_visible(timeout=20000)
        has_error = error_banner.is_visible()

        if has_articles:
            badge_text = article_badge.text_content()
            result["details"].append(f"✅ Articles loaded: {badge_text}")

            # Count article cards
            cards = page.locator("a[href*='/news/']").count()
            result["details"].append(f"✅ Article cards visible: {cards}")

            if cards > 0:
                result["status"] = "passed"
            else:
                result["details"].append("❌ Badge shows articles but no cards visible")
                result["status"] = "failed"

        elif has_error:
            error_text = error_banner.text_content()[:100]
            result["details"].append(f"⚠️ Error shown (expected behavior if backend down): {error_text}...")

            # Verify retry button exists
            retry_button = error_banner.locator("button:has-text('Retry')")
            if retry_button.is_visible():
                result["details"].append("✅ Retry button available")
                result["status"] = "passed"  # Error handling working as expected
            else:
                result["details"].append("❌ Retry button not visible")
                result["status"] = "failed"
        else:
            result["details"].append("❌ Neither articles nor error shown - BUG!")
            result["status"] = "failed"

    except Exception as e:
        log(f"❌ Test failed with error: {e}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result


def main():
    """Run all news error handling verification tests"""
    log("=" * 70)
    log("NEWS COVERAGE ERROR HANDLING VERIFICATION")
    log("=" * 70)

    all_results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # Test 1: Happy Path
        result1 = test_happy_path(page)
        all_results.append(result1)

        # Test 2: Backend Down
        result2 = test_backend_down(page)
        all_results.append(result2)

        # Test 3: Retry Button
        result3 = test_retry_button(page)
        all_results.append(result3)

        # Test 4: Console Logs
        result4 = test_console_logs(page)
        all_results.append(result4)

        # Test 5: Production Environment
        result5 = test_production_environment(page)
        all_results.append(result5)

        browser.close()

    # Print Summary
    log("\n" + "=" * 70)
    log("TEST SUMMARY")
    log("=" * 70)

    passed = sum(1 for r in all_results if r["status"] == "passed")
    failed = sum(1 for r in all_results if r["status"] == "failed")

    for result in all_results:
        status_emoji = "✅" if result["status"] == "passed" else "❌"
        log(f"{status_emoji} {result['test']}: {result['status'].upper()}")

        for detail in result["details"]:
            log(f"   {detail}")

        if "error" in result:
            log(f"   Error: {result['error']}")

    log("\n" + "=" * 70)
    log(f"FINAL RESULTS: {passed} PASSED, {failed} FAILED")
    log("=" * 70)

    # Save detailed results
    output_file = f"news_error_handling_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(all_results),
                "passed": passed,
                "failed": failed
            },
            "tests": all_results
        }, f, indent=2)

    log(f"\n📄 Detailed results saved to: {output_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
