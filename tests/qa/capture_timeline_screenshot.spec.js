/**
 * Capture Timeline Screenshots for QA Report
 */

const { test } = require('@playwright/test');

const BASE_URL = 'http://localhost:5173';

test('Capture Timeline with 17 News Events', async ({ page }) => {
  await page.goto(`${BASE_URL}/timeline`);

  // Wait for initial load
  await page.waitForSelector('text=/Showing \\d+ of \\d+ events/', { timeout: 10000 });

  // Apply News filter
  await page.click('button:has-text("News Articles")');

  // Wait for filtered view
  await page.waitForTimeout(2000);

  // Capture screenshot
  await page.screenshot({
    path: 'test-results/timeline-news-filter-17-events.png',
    fullPage: true
  });

  console.log('✓ Screenshot saved: test-results/timeline-news-filter-17-events.png');
});
