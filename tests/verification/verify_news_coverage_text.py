#!/usr/bin/env python3
"""
Text-based verification of News Coverage display
No screenshots - only text extraction and API verification
"""

import json
from playwright.sync_api import sync_playwright


def verify_news_coverage():
    print("\n" + "=" * 60)
    print("NEWS COVERAGE TEXT VERIFICATION")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # Track network requests
        api_requests = []
        api_responses = []
        console_errors = []

        def handle_request(request):
            if '/api/news' in request.url:
                api_requests.append({
                    'url': request.url,
                    'method': request.method
                })
                print(f"[REQUEST] {request.method} {request.url}")

        def handle_response(response):
            if '/api/news' in response.url:
                print(f"[RESPONSE] {response.status} {response.url}")
                try:
                    data = response.json()
                    api_responses.append(data)
                    articles_count = len(data.get('articles', []))
                    total = data.get('total', 0)
                    has_more = data.get('has_more', False)
                    print(f"[RESPONSE DATA] Articles count: {articles_count}")
                    print(f"[RESPONSE DATA] Total: {total}")
                    print(f"[RESPONSE DATA] Has more: {has_more}")
                except Exception as e:
                    print(f"[RESPONSE DATA] Failed to parse JSON: {e}")

        def handle_console(msg):
            if msg.type == 'error':
                console_errors.append(msg.text)
                print(f"[CONSOLE ERROR] {msg.text}")

        page.on('request', handle_request)
        page.on('response', handle_response)
        page.on('console', handle_console)

        # Navigate to entity page
        print("\n1. NAVIGATING TO PAGE...")
        page.goto("http://localhost:3000/entities/jeffrey_epstein")

        # Wait for network idle
        print("\n2. WAITING FOR NETWORK IDLE...")
        page.wait_for_load_state('networkidle')

        # Wait a bit more for any delayed requests
        page.wait_for_timeout(3000)

        # Extract page title
        print("\n3. EXTRACTING PAGE CONTENT...")
        page_title = page.title()
        print(f"Page Title: {page_title}")

        # Look for News Coverage section
        news_coverage_visible = False
        try:
            news_section = page.locator('text=News Coverage').first
            news_coverage_visible = news_section.is_visible()
            print(f"\nNews Coverage Section Visible: {news_coverage_visible}")
        except:
            print(f"\nNews Coverage Section Visible: False")

        if news_coverage_visible:
            # Try to find badges with article count
            print("\n4. LOOKING FOR ARTICLE COUNT BADGES...")
            badges = page.locator('[class*="badge"], [class*="Badge"]')
            badge_count = badges.count()
            print(f"Found {badge_count} badge elements")

            for i in range(min(badge_count, 10)):
                try:
                    badge_text = badges.nth(i).text_content()
                    if badge_text and 'article' in badge_text.lower():
                        print(f"  Badge {i}: \"{badge_text}\"")
                except:
                    pass

            # Look for article titles
            print("\n5. SEARCHING FOR ARTICLE TITLES...")
            selectors_to_try = [
                'h3',
                'h4',
                '[class*="article"]',
                '[class*="news"]'
            ]

            for selector in selectors_to_try:
                try:
                    elements = page.locator(selector)
                    count = elements.count()
                    if count > 0:
                        print(f"\nFound {count} elements with selector: {selector}")
                        # Get first 5 text contents
                        for i in range(min(count, 5)):
                            try:
                                text = elements.nth(i).text_content()
                                if text and len(text) > 10 and len(text) < 200:
                                    print(f"  {i + 1}. {text.strip()[:100]}")
                            except:
                                pass
                except:
                    pass

        # Get all text content and search for known article titles
        print("\n6. SEARCHING FOR KNOWN ARTICLE TITLES IN PAGE TEXT...")
        body_text = page.locator('body').text_content()

        known_titles = [
            'Last Batch of Unsealed Jeffrey Epstein Documents',
            'Unsealed Court Documents Reveal Names',
            'Jeffrey Epstein List'
        ]

        for title in known_titles:
            found = title in body_text if body_text else False
            print(f"  Looking for \"{title}\": {'FOUND' if found else 'NOT FOUND'}")

        # Check for article count text
        print("\n7. SEARCHING FOR ARTICLE COUNT INDICATORS...")
        if body_text:
            import re
            article_count_matches = re.findall(r'(\d+)\s*articles?', body_text, re.IGNORECASE)
            if article_count_matches:
                print(f"  Article count indicators found: {', '.join(article_count_matches)}")
            else:
                print("  No article count indicators found")

        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"API Requests Made: {len(api_requests)}")
        print(f"API Responses Received: {len(api_responses)}")
        print(f"Console Errors: {len(console_errors)}")
        if console_errors:
            print("\nConsole Errors:")
            for i, err in enumerate(console_errors[:5], 1):
                print(f"  {i}. {err[:200]}")
        print(f"\nNews Coverage Section Present: {news_coverage_visible}")

        if api_responses:
            print("\nAPI Response Summary:")
            for i, resp in enumerate(api_responses, 1):
                articles = len(resp.get('articles', []))
                total = resp.get('total', 0)
                print(f"  Response {i}: {articles} articles returned, {total} total")

        # Verification results
        print("\n" + "=" * 60)
        print("VERIFICATION RESULTS")
        print("=" * 60)

        success = True
        if len(api_requests) == 0:
            print("❌ FAIL: No API requests made to /api/news")
            success = False
        else:
            print("✅ PASS: API requests made to /api/news")

        if len(api_responses) == 0:
            print("❌ FAIL: No API responses received")
            success = False
        else:
            print(f"✅ PASS: API responses received ({len(api_responses)})")

        if not news_coverage_visible:
            print("❌ FAIL: News Coverage section not visible")
            success = False
        else:
            print("✅ PASS: News Coverage section visible")

        if console_errors:
            print(f"⚠️  WARNING: {len(console_errors)} console errors detected")
        else:
            print("✅ PASS: No console errors")

        print("\n" + "=" * 60)
        if success:
            print("✅ OVERALL: NEWS COVERAGE VERIFICATION PASSED")
        else:
            print("❌ OVERALL: NEWS COVERAGE VERIFICATION FAILED")
        print("=" * 60 + "\n")

        browser.close()


if __name__ == '__main__':
    verify_news_coverage()
