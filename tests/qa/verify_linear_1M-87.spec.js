/**
 * Linear Ticket 1M-87 Verification Test
 *
 * Testing Timeline & News Unification Implementation
 *
 * Critical Requirements:
 * 1. Single "Timeline & News" navigation entry (not two separate items)
 * 2. /news route redirects to /timeline
 * 3. Timeline page shows source filters
 * 4. No console errors
 */

const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

// Screenshot directory
const screenshotDir = path.join(__dirname, '../artifacts/linear-1M-87');

test.beforeAll(async () => {
  // Create screenshot directory
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir, { recursive: true });
  }
});

test.describe('Linear 1M-87: Timeline & News Unification', () => {

  test('CRITICAL: Navigation menu shows single "Timeline & News" entry', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Take screenshot of initial page
    await page.screenshot({
      path: path.join(screenshotDir, '01-homepage.png'),
      fullPage: true
    });

    // Find all navigation links containing "Timeline" or "News"
    const navLinks = await page.locator('nav a, nav button').all();
    const timelineNewsLinks = [];

    for (const link of navLinks) {
      const text = await link.textContent();
      if (text && (text.includes('Timeline') || text.includes('News'))) {
        timelineNewsLinks.push(text.trim());
      }
    }

    console.log('\n=== Navigation Links Found ===');
    console.log('Timeline/News related links:', timelineNewsLinks);
    console.log('Count:', timelineNewsLinks.length);

    // Take screenshot of navigation
    const nav = page.locator('nav').first();
    if (await nav.isVisible()) {
      await nav.screenshot({
        path: path.join(screenshotDir, '02-navigation-menu.png')
      });
    }

    // CRITICAL: Should be exactly 1 Timeline/News entry
    expect(timelineNewsLinks.length,
      `Expected 1 Timeline/News navigation entry, found ${timelineNewsLinks.length}: ${JSON.stringify(timelineNewsLinks)}`
    ).toBe(1);

    // Should contain "Timeline" or "Timeline & News"
    const linkText = timelineNewsLinks[0];
    expect(
      linkText.includes('Timeline'),
      `Navigation entry should contain "Timeline", found: "${linkText}"`
    ).toBeTruthy();

    // Should NOT be just "News"
    expect(
      linkText,
      'Navigation entry should not be just "News"'
    ).not.toBe('News');

    console.log('✅ PASS: Single navigation entry verified:', linkText);
    console.log('Console errors:', consoleErrors.length > 0 ? consoleErrors : 'None');
  });

  test('CRITICAL: /news route redirects to /timeline', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    console.log('\n=== Testing /news Redirect ===');

    // Navigate directly to /news
    await page.goto('http://localhost:5173/news');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000); // Wait for any redirects

    // Take screenshot after navigation
    await page.screenshot({
      path: path.join(screenshotDir, '03-news-redirect.png'),
      fullPage: true
    });

    // Check final URL
    const finalUrl = page.url();
    console.log('Initial navigation: /news');
    console.log('Final URL:', finalUrl);

    // CRITICAL: Should redirect to /timeline
    expect(
      finalUrl.includes('/timeline'),
      `Expected redirect to /timeline, but got: ${finalUrl}`
    ).toBeTruthy();

    expect(
      finalUrl.includes('/news'),
      `URL should not contain /news after redirect, got: ${finalUrl}`
    ).toBeFalsy();

    console.log('✅ PASS: /news redirects to /timeline');
    console.log('Console errors:', consoleErrors.length > 0 ? consoleErrors : 'None');
  });

  test('CRITICAL: Timeline page loads with source filters', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    console.log('\n=== Testing Timeline Page Functionality ===');

    await page.goto('http://localhost:5173/timeline');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Take screenshot of timeline page
    await page.screenshot({
      path: path.join(screenshotDir, '04-timeline-page.png'),
      fullPage: true
    });

    // Check page header
    const pageContent = await page.textContent('body');
    console.log('Checking page header...');

    const hasTimelineHeader = pageContent.includes('Timeline') &&
                              (pageContent.includes('Timeline & News') ||
                               pageContent.includes('Timeline and News'));

    console.log('Page header contains Timeline:', hasTimelineHeader);

    // Check for source filter
    console.log('Checking for source filters...');

    // Try multiple selectors for source filter
    const possibleFilterSelectors = [
      'select[name="source"]',
      'select:has-text("All Sources")',
      'button:has-text("All Sources")',
      'div:has-text("Source")',
      '[role="combobox"]',
      '.source-filter',
      'label:has-text("Source")'
    ];

    let sourceFilterFound = false;
    let filterText = '';

    for (const selector of possibleFilterSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          sourceFilterFound = true;
          filterText = await element.textContent();
          console.log(`✓ Found source filter with selector: ${selector}`);
          console.log(`  Filter text: ${filterText?.substring(0, 100)}`);

          // Take screenshot of filter
          await element.screenshot({
            path: path.join(screenshotDir, '05-source-filter.png')
          });
          break;
        }
      } catch (e) {
        // Continue to next selector
      }
    }

    // Also check page text for filter-related content
    const hasFilterText = pageContent.includes('All Sources') ||
                          pageContent.includes('Timeline Events') ||
                          pageContent.includes('News Articles');

    console.log('Source filter found via selectors:', sourceFilterFound);
    console.log('Source filter text found in page:', hasFilterText);

    // Check for expected filter options in page content
    const hasAllSources = pageContent.includes('All Sources');
    const hasTimelineEvents = pageContent.includes('Timeline Events');
    const hasNewsArticles = pageContent.includes('News Articles');

    console.log('Filter options in page:');
    console.log('  - All Sources:', hasAllSources);
    console.log('  - Timeline Events:', hasTimelineEvents);
    console.log('  - News Articles:', hasNewsArticles);

    // CRITICAL: Timeline page should be functional
    expect(
      hasTimelineHeader,
      'Timeline page should have Timeline header'
    ).toBeTruthy();

    // Source filter should exist (either as element or in text)
    expect(
      sourceFilterFound || hasFilterText,
      'Timeline page should have source filter functionality'
    ).toBeTruthy();

    console.log('✅ PASS: Timeline page loads with expected functionality');
    console.log('Console errors:', consoleErrors.length > 0 ? consoleErrors : 'None');
  });

  test('Check for article detail routes preservation', async ({ page }) => {
    console.log('\n=== Testing Article Detail Routes ===');

    // This is a bonus check - we don't know if article routes exist
    // Just verify that direct article access doesn't break

    await page.goto('http://localhost:5173/timeline');
    await page.waitForLoadState('networkidle');

    // Look for any article links
    const articleLinks = await page.locator('a[href*="/news/"]').count();
    console.log('Article detail links found:', articleLinks);

    if (articleLinks > 0) {
      console.log('✓ Article detail routes appear to be present');
    } else {
      console.log('ℹ No article detail links found (may not exist in current view)');
    }

    // Check if route handling exists in app
    const pageContent = await page.textContent('body');
    const hasRouting = !pageContent.includes('404') && !pageContent.includes('Not Found');

    console.log('Page routing functional:', hasRouting);
  });

  test('SUMMARY: Generate verification report', async ({ page }) => {
    console.log('\n==========================================================');
    console.log('LINEAR TICKET 1M-87 VERIFICATION SUMMARY');
    console.log('==========================================================\n');

    const report = {
      ticket: '1M-87',
      feature: 'Timeline & News Unification',
      timestamp: new Date().toISOString(),
      testUrl: 'http://localhost:5173',
      screenshots: screenshotDir,
      results: {
        singleNavigationEntry: 'See test results above',
        newsRedirect: 'See test results above',
        timelineFunctionality: 'See test results above',
        articleDetailRoutes: 'See test results above'
      }
    };

    console.log('Test Report:', JSON.stringify(report, null, 2));
    console.log('\nScreenshots saved to:', screenshotDir);
    console.log('\n==========================================================\n');

    // Save report to file
    fs.writeFileSync(
      path.join(screenshotDir, 'verification-report.json'),
      JSON.stringify(report, null, 2)
    );
  });

});
