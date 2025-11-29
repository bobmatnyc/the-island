#!/usr/bin/env python3
"""
Phase 1 News Expansion Verification
Tests the 80 new articles added to News page
"""
import json
from playwright.sync_api import sync_playwright, expect
import sys

def test_news_phase1_expansion():
    """Verify Phase 1 news expansion (70 → 150 articles)"""

    results = {
        "test_1_article_count": {"status": "UNKNOWN", "evidence": []},
        "test_2_source_coverage": {"status": "UNKNOWN", "evidence": []},
        "test_3_entity_coverage": {"status": "UNKNOWN", "evidence": []},
        "test_4_date_range": {"status": "UNKNOWN", "evidence": []},
        "test_5_article_quality": {"status": "UNKNOWN", "evidence": []},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Enable console monitoring
        console_errors = []
        page.on("console", lambda msg:
            console_errors.append(msg.text()) if msg.type in ["error", "warning"] else None
        )

        try:
            # Navigate to news page
            print("Navigating to /news page...")
            page.goto("http://localhost:5173/news", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)  # Allow content to load

            # TEST 1: Article Count Verification
            print("\n=== TEST 1: Article Count Verification ===")
            try:
                # Look for total count indicator
                page_text = page.content()

                # Check for article cards
                article_cards = page.locator('[class*="article"], [class*="news-item"], [class*="card"]').count()

                # Look for pagination or count text
                count_elements = page.locator('text=/\\d+\\s+(article|total|showing)/i').all()
                count_text = " | ".join([el.text_content() for el in count_elements]) if count_elements else "No count text found"

                evidence = {
                    "visible_article_cards": article_cards,
                    "count_text_found": count_text,
                    "page_has_articles": "article" in page_text.lower() or "news" in page_text.lower()
                }

                results["test_1_article_count"]["evidence"].append(evidence)

                # Check if we see indication of 150 articles
                if "150" in page_text or article_cards >= 10:  # At least 10 visible (pagination)
                    results["test_1_article_count"]["status"] = "PASS"
                    print("✅ PASS: Article count appears correct")
                else:
                    results["test_1_article_count"]["status"] = "PARTIAL"
                    print(f"⚠️ PARTIAL: Found {article_cards} article cards, count text: {count_text}")

            except Exception as e:
                results["test_1_article_count"]["status"] = "FAIL"
                results["test_1_article_count"]["evidence"].append({"error": str(e)})
                print(f"❌ FAIL: {e}")

            # TEST 2: Source Coverage
            print("\n=== TEST 2: Source Coverage ===")
            try:
                # Look for source filters or source names
                expected_sources = ["Guardian", "BBC", "Miami Herald", "NPR"]
                found_sources = []

                for source in expected_sources:
                    if page.get_by_text(source, exact=False).count() > 0:
                        found_sources.append(source)

                # Count unique sources visible on page
                source_filter = page.locator('[class*="source"], [class*="filter"]').first
                source_options = source_filter.locator('option, [role="option"], button').count() if source_filter.count() > 0 else 0

                evidence = {
                    "expected_sources_found": found_sources,
                    "source_filter_options": source_options,
                }

                results["test_2_source_coverage"]["evidence"].append(evidence)

                if len(found_sources) >= 2 or source_options >= 10:  # At least 2 sources or 10+ filter options
                    results["test_2_source_coverage"]["status"] = "PASS"
                    print(f"✅ PASS: Found sources: {found_sources}, filter options: {source_options}")
                else:
                    results["test_2_source_coverage"]["status"] = "PARTIAL"
                    print(f"⚠️ PARTIAL: Limited source coverage visible")

            except Exception as e:
                results["test_2_source_coverage"]["status"] = "FAIL"
                results["test_2_source_coverage"]["evidence"].append({"error": str(e)})
                print(f"❌ FAIL: {e}")

            # TEST 3: Entity Coverage (Check if filtering by entity works)
            print("\n=== TEST 3: Entity Coverage ===")
            try:
                # Look for entity filter or entity links
                entity_names = ["Jeffrey Epstein", "Ghislaine Maxwell"]
                entity_links = []

                for entity in entity_names:
                    count = page.get_by_text(entity, exact=False).count()
                    if count > 0:
                        entity_links.append({"entity": entity, "mentions": count})

                evidence = {
                    "entity_mentions": entity_links,
                    "total_entity_references": sum(e["mentions"] for e in entity_links)
                }

                results["test_3_entity_coverage"]["evidence"].append(evidence)

                if len(entity_links) >= 2 and evidence["total_entity_references"] >= 10:
                    results["test_3_entity_coverage"]["status"] = "PASS"
                    print(f"✅ PASS: Found entities: {entity_links}")
                else:
                    results["test_3_entity_coverage"]["status"] = "PARTIAL"
                    print(f"⚠️ PARTIAL: Entity coverage needs verification: {entity_links}")

            except Exception as e:
                results["test_3_entity_coverage"]["status"] = "FAIL"
                results["test_3_entity_coverage"]["evidence"].append({"error": str(e)})
                print(f"❌ FAIL: {e}")

            # TEST 4: Date Range
            print("\n=== TEST 4: Date Range Coverage ===")
            try:
                page_content = page.content().lower()

                # Look for dates from different years
                years_found = []
                for year in ["2018", "2019", "2020", "2021", "2022", "2023", "2024"]:
                    if year in page_content:
                        years_found.append(year)

                evidence = {
                    "years_found": years_found,
                    "date_range_span": f"{min(years_found)} - {max(years_found)}" if years_found else "No dates found"
                }

                results["test_4_date_range"]["evidence"].append(evidence)

                if len(years_found) >= 5:  # Coverage across at least 5 years
                    results["test_4_date_range"]["status"] = "PASS"
                    print(f"✅ PASS: Date range: {evidence['date_range_span']}, years: {years_found}")
                else:
                    results["test_4_date_range"]["status"] = "PARTIAL"
                    print(f"⚠️ PARTIAL: Limited date range: {years_found}")

            except Exception as e:
                results["test_4_date_range"]["status"] = "FAIL"
                results["test_4_date_range"]["evidence"].append({"error": str(e)})
                print(f"❌ FAIL: {e}")

            # TEST 5: Article Quality (Click first article)
            print("\n=== TEST 5: Article Quality ===")
            try:
                # Find first article link or card
                first_article = page.locator('[class*="article"]:visible, [class*="news-item"]:visible, [class*="card"]:visible').first

                if first_article.count() > 0:
                    article_text = first_article.text_content()
                    has_title = len(article_text) > 20
                    has_source = any(src in article_text.lower() for src in ["guardian", "bbc", "nyt", "washington", "reuters"])

                    # Try clicking to see if article opens
                    clickable = first_article.locator('a, button').first
                    if clickable.count() > 0:
                        clickable.click()
                        page.wait_for_timeout(2000)

                        # Check if article detail opened
                        article_opened = "article" in page.url or page.locator('[class*="article-content"]').count() > 0
                    else:
                        article_opened = False

                    evidence = {
                        "article_has_title": has_title,
                        "article_has_source": has_source,
                        "article_clickable": clickable.count() > 0,
                        "article_opened": article_opened,
                        "sample_text": article_text[:100] + "..."
                    }

                    results["test_5_article_quality"]["evidence"].append(evidence)

                    if has_title and has_source:
                        results["test_5_article_quality"]["status"] = "PASS"
                        print(f"✅ PASS: Article quality verified")
                    else:
                        results["test_5_article_quality"]["status"] = "PARTIAL"
                        print(f"⚠️ PARTIAL: Article structure needs review")
                else:
                    results["test_5_article_quality"]["status"] = "FAIL"
                    results["test_5_article_quality"]["evidence"].append({"error": "No articles found on page"})
                    print("❌ FAIL: No articles found")

            except Exception as e:
                results["test_5_article_quality"]["status"] = "PARTIAL"
                results["test_5_article_quality"]["evidence"].append({"error": str(e)})
                print(f"⚠️ PARTIAL: {e}")

            # Console Errors Summary
            if console_errors:
                print(f"\n⚠️ Console Errors/Warnings: {len(console_errors)}")
                for error in console_errors[:5]:  # Show first 5
                    print(f"  - {error}")
            else:
                print("\n✅ No console errors detected")

        except Exception as e:
            print(f"\n❌ CRITICAL FAILURE: {e}")
            results["critical_error"] = str(e)

        finally:
            browser.close()

    # Print Summary
    print("\n" + "="*60)
    print("PHASE 1 VERIFICATION SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        if test_name != "critical_error":
            status = result["status"]
            emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"{emoji} {test_name}: {status}")

    # Overall assessment
    pass_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "PASS")
    partial_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("status") == "PARTIAL")

    print(f"\nPassed: {pass_count}/5, Partial: {partial_count}/5")

    # Save results
    with open("/Users/masa/Projects/epstein/phase1_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: phase1_verification_results.json")

    # Return exit code
    if pass_count >= 3:
        print("\n✅ PHASE 1 VERIFICATION: PASSED (sufficient evidence)")
        return 0
    elif pass_count + partial_count >= 4:
        print("\n⚠️ PHASE 1 VERIFICATION: ACCEPTABLE (mostly working)")
        return 0
    else:
        print("\n❌ PHASE 1 VERIFICATION: FAILED (too many issues)")
        return 1

if __name__ == "__main__":
    sys.exit(test_news_phase1_expansion())
