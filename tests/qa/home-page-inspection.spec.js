/**
 * Detailed Home Page Inspection
 * Identify what cards are being rendered
 */

const { test } = require('@playwright/test');

test('Inspect all cards on home page', async ({ page }) => {
  await page.goto('http://localhost:8081/');
  await page.waitForLoadState('networkidle');

  // Get all link elements
  const allLinks = await page.locator('a').all();
  console.log(`\nTotal links on page: ${allLinks.length}`);

  // Get all card-like elements
  const cardElements = await page.locator('[class*="card"], [class*="Card"], [role="button"]').all();
  console.log(`\nTotal card-like elements: ${cardElements.length}`);

  // Inspect each card-like element
  for (let i = 0; i < cardElements.length; i++) {
    const elem = cardElements[i];
    const text = await elem.textContent();
    const classes = await elem.getAttribute('class');
    const role = await elem.getAttribute('role');
    const href = await elem.evaluate(el => {
      const link = el.closest('a') || el.querySelector('a');
      return link ? link.getAttribute('href') : null;
    });

    console.log(`\n--- Card ${i + 1} ---`);
    console.log(`Text: ${text?.trim().substring(0, 100)}`);
    console.log(`Classes: ${classes}`);
    console.log(`Role: ${role}`);
    console.log(`Link: ${href}`);
  }

  // Get all dashboard cards specifically
  const dashboardSection = page.locator('[class*="grid"]').filter({ has: page.locator('a[href*="/"]') }).first();
  const dashboardCards = await dashboardSection.locator('a').all();

  console.log(`\n\n=== DASHBOARD CARDS ===`);
  console.log(`Total dashboard cards: ${dashboardCards.length}`);

  for (let i = 0; i < dashboardCards.length; i++) {
    const card = dashboardCards[i];
    const href = await card.getAttribute('href');
    const text = await card.textContent();
    const ariaLabel = await card.getAttribute('aria-label');

    console.log(`\nDashboard Card ${i + 1}:`);
    console.log(`  Link: ${href}`);
    console.log(`  ARIA Label: ${ariaLabel}`);
    console.log(`  Text: ${text?.trim().substring(0, 200)}`);
  }

  // Look for "News" text specifically
  const newsMatches = await page.locator('text=/\\bNews\\b/i').all();
  console.log(`\n\n=== "News" TEXT OCCURRENCES ===`);
  console.log(`Total "News" mentions: ${newsMatches.length}`);

  for (let i = 0; i < newsMatches.length; i++) {
    const elem = newsMatches[i];
    const text = await elem.textContent();
    const parent = await elem.evaluate(el => el.parentElement?.tagName);
    console.log(`\nNews ${i + 1}:`);
    console.log(`  Text: ${text?.trim()}`);
    console.log(`  Parent: ${parent}`);
  }

  // Take screenshot
  await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-inspection.png', fullPage: true });
});
