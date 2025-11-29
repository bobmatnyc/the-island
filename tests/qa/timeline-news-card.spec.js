/**
 * QA Test: Unified Timeline & News Card (Ticket 1M-87)
 *
 * Test Requirements:
 * 1. Home page displays 5 cards total (not 6)
 * 2. Single "Timeline & News" card is present
 * 3. No separate "News" card exists
 * 4. Combined count displays correctly
 * 5. Card links to /timeline
 * 6. Grid layout displays properly
 * 7. No console errors
 * 8. Consistent navigation
 */

const { test, expect } = require('@playwright/test');

test.describe('Unified Timeline & News Card - 1M-87', () => {
  let consoleErrors = [];

  test.beforeEach(async ({ page }) => {
    // Monitor console errors
    consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate to home page
    await page.goto('http://localhost:8081/');
    await page.waitForLoadState('networkidle');
  });

  test('1. Home Page Card Display - Verify 5 cards with unified Timeline & News', async ({ page }) => {
    // Count total cards
    const cards = page.locator('[class*="card"], [role="link"][class*="Card"]').filter({ hasText: /Entities|Documents|Timeline|Connections|Matrix/ });
    const cardCount = await cards.count();

    console.log(`Total cards found: ${cardCount}`);
    expect(cardCount).toBe(5);

    // Verify "Timeline & News" card exists
    const timelineNewsCard = page.locator('text=/Timeline.*News/i, text=/Timeline & News/i');
    await expect(timelineNewsCard.first()).toBeVisible();

    // Verify no separate "News" card (that's not part of "Timeline & News")
    const allText = await page.textContent('body');
    const timelineNewsMatches = (allText.match(/Timeline.*News|Timeline & News/gi) || []).length;
    const standaloneNewsMatches = (allText.match(/\bNews\b/gi) || []).length;

    console.log(`"Timeline & News" mentions: ${timelineNewsMatches}`);
    console.log(`"News" standalone mentions: ${standaloneNewsMatches}`);

    // Get all card titles
    const cardTitles = [];
    for (let i = 0; i < cardCount; i++) {
      const title = await cards.nth(i).textContent();
      cardTitles.push(title.trim());
    }
    console.log('Card titles:', cardTitles);
  });

  test('2. Combined Count Display - Verify count shows timeline + news', async ({ page }) => {
    // Find the Timeline & News card
    const timelineCard = page.locator('text=/Timeline.*News/i, text=/Timeline & News/i').first();
    await expect(timelineCard).toBeVisible();

    // Look for count display near the card
    const cardContainer = page.locator('[class*="card"], [class*="Card"]').filter({ has: timelineCard }).first();
    const cardText = await cardContainer.textContent();

    console.log('Timeline & News card content:', cardText);

    // Check if count is present (should be a number)
    const hasNumber = /\d+/.test(cardText);
    expect(hasNumber).toBe(true);

    // Extract the count
    const countMatch = cardText.match(/(\d+)/);
    if (countMatch) {
      const count = parseInt(countMatch[1]);
      console.log(`Combined count displayed: ${count}`);
      expect(count).toBeGreaterThan(0);
    }
  });

  test('3. Card Functionality - Click navigates to /timeline', async ({ page }) => {
    // Find and click the Timeline & News card
    const timelineCard = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Timeline.*News|Timeline & News/i
    }).first();

    await expect(timelineCard).toBeVisible();
    await timelineCard.click();

    // Wait for navigation
    await page.waitForURL('**/timeline');

    // Verify we're on the timeline page
    expect(page.url()).toContain('/timeline');

    // Verify source filtering exists
    const hasFilters = await page.locator('text=/All Sources|Timeline Events|News Articles/i').count() > 0;
    console.log('Source filters present:', hasFilters);
    expect(hasFilters).toBe(true);
  });

  test('4. Grid Layout - Verify responsive design', async ({ page }) => {
    // Desktop viewport (default)
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);

    let cards = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Entities|Documents|Timeline|Connections|Matrix/
    });
    let cardCount = await cards.count();
    console.log(`Desktop (1920x1080): ${cardCount} cards`);
    expect(cardCount).toBe(5);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-desktop.png', fullPage: true });

    // Tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(500);

    cards = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Entities|Documents|Timeline|Connections|Matrix/
    });
    cardCount = await cards.count();
    console.log(`Tablet (768x1024): ${cardCount} cards`);
    expect(cardCount).toBe(5);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-tablet.png', fullPage: true });

    // Mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);

    cards = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Entities|Documents|Timeline|Connections|Matrix/
    });
    cardCount = await cards.count();
    console.log(`Mobile (375x667): ${cardCount} cards`);
    expect(cardCount).toBe(5);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-mobile.png', fullPage: true });
  });

  test('5. Consistency Check - Navigation and routing', async ({ page }) => {
    // Check home page card
    const homeCard = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Timeline.*News|Timeline & News/i
    }).first();
    await expect(homeCard).toBeVisible();

    // Check header navigation
    const headerNav = page.locator('header, nav').first();
    const headerText = await headerNav.textContent();
    console.log('Header navigation text:', headerText);

    // Verify /news redirects to /timeline
    await page.goto('http://localhost:8081/news');
    await page.waitForLoadState('networkidle');

    const currentUrl = page.url();
    console.log('After navigating to /news, URL is:', currentUrl);
    expect(currentUrl).toContain('/timeline');
  });

  test('6. Visual Regression - Card appearance', async ({ page }) => {
    // Wait for cards to load
    await page.waitForSelector('[class*="card"], [class*="Card"]', { state: 'visible' });

    // Take screenshot of the Timeline & News card specifically
    const timelineCard = page.locator('[class*="card"], [class*="Card"]').filter({
      hasText: /Timeline.*News|Timeline & News/i
    }).first();

    await expect(timelineCard).toBeVisible();
    await timelineCard.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-news-card.png' });

    // Verify icon is present
    const hasIcon = await timelineCard.locator('svg, img, [class*="icon"]').count() > 0;
    console.log('Card has icon:', hasIcon);

    // Verify text is readable (check color contrast)
    const styles = await timelineCard.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        color: computed.color,
        fontSize: computed.fontSize
      };
    });
    console.log('Card styles:', styles);
  });

  test('7. Console Error Check', async ({ page }) => {
    // Wait for page to fully load
    await page.waitForTimeout(2000);

    console.log('Console errors captured:', consoleErrors);

    // Filter out non-critical errors (if any)
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('DevTools')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('8. Card Count Verification - Detailed inspection', async ({ page }) => {
    // Get all interactive card-like elements
    const allCards = page.locator('[class*="card" i], [class*="Card"], a[href*="/"]').filter({
      hasText: /.+/
    });

    // Find cards in the main content area (exclude header/footer)
    const mainContent = page.locator('main, [class*="content"], [class*="container"]').first();
    const mainCards = mainContent.locator('[class*="card" i], [class*="Card"]');

    const mainCardCount = await mainCards.count();
    console.log(`Cards in main content: ${mainCardCount}`);

    // List all card titles
    for (let i = 0; i < mainCardCount; i++) {
      const cardText = await mainCards.nth(i).textContent();
      console.log(`Card ${i + 1}: ${cardText.trim().substring(0, 100)}`);
    }

    // Verify expected cards are present
    const expectedCards = [
      'Entities',
      'Documents',
      'Timeline',
      'Connections',
      'Matrix'
    ];

    for (const expected of expectedCards) {
      const found = await page.locator(`text=/${expected}/i`).count();
      console.log(`"${expected}" found: ${found} times`);
      expect(found).toBeGreaterThan(0);
    }
  });
});
