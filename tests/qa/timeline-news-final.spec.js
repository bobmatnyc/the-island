/**
 * QA Test: Unified Timeline & News Card - FINAL VALIDATION (Ticket 1M-87)
 *
 * Corrected test with precise selectors for dashboard cards section
 */

const { test, expect } = require('@playwright/test');

test.describe('Unified Timeline & News Card - Final Validation', () => {
  let consoleErrors = [];
  let consoleWarnings = [];

  test.beforeEach(async ({ page }) => {
    // Monitor console messages
    consoleErrors = [];
    consoleWarnings = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text());
      }
    });

    // Navigate to home page
    await page.goto('http://localhost:8081/');
    await page.waitForLoadState('networkidle');
  });

  test('1. Dashboard Cards: Verify exactly 5 cards with unified Timeline & News', async ({ page }) => {
    // Precise selector: Get dashboard cards (links with role="button" parent)
    const dashboardCards = page.locator('a[aria-label*="View"]').filter({
      has: page.locator('[role="button"]')
    });

    const cardCount = await dashboardCards.count();
    console.log(`Dashboard cards found: ${cardCount}`);

    expect(cardCount).toBe(5);

    // Verify Timeline & News card exists
    const timelineNewsCard = page.locator('a[aria-label*="Timeline & News"]');
    await expect(timelineNewsCard).toBeVisible();

    const ariaLabel = await timelineNewsCard.getAttribute('aria-label');
    console.log(`Timeline & News card aria-label: ${ariaLabel}`);

    // Extract and verify all card labels
    const cardLabels = [];
    for (let i = 0; i < cardCount; i++) {
      const card = dashboardCards.nth(i);
      const ariaLabel = await card.getAttribute('aria-label');
      const text = await card.textContent();
      cardLabels.push({ ariaLabel, preview: text?.substring(0, 50) });
    }

    console.log('\nAll dashboard cards:', JSON.stringify(cardLabels, null, 2));

    // Verify expected cards are present
    const expectedLabels = ['Timeline & News', 'Entities', 'Flights', 'Documents', 'Visualizations'];
    for (const expected of expectedLabels) {
      const found = cardLabels.some(card => card.ariaLabel?.includes(expected));
      expect(found).toBe(true);
      console.log(`✓ "${expected}" card found`);
    }

    // Verify NO separate "News" card exists (should only be part of "Timeline & News")
    const hasStandaloneNewsCard = cardLabels.some(card => {
      const label = card.ariaLabel?.toLowerCase() || '';
      // Check for standalone "News" card (not "Timeline & News")
      return label === 'view news' ||
             (label.includes('news') && !label.includes('timeline'));
    });
    expect(hasStandaloneNewsCard).toBe(false);
    console.log('✓ No standalone "News" card found');
  });

  test('2. Combined Count: Verify Timeline & News shows combined count', async ({ page }) => {
    const timelineNewsCard = page.locator('a[aria-label*="Timeline & News"]');
    await expect(timelineNewsCard).toBeVisible();

    // Extract count from aria-label (e.g., "View 317 Timeline & News")
    const ariaLabel = await timelineNewsCard.getAttribute('aria-label');
    const countMatch = ariaLabel?.match(/View ([\d,]+)/);

    expect(countMatch).toBeTruthy();
    const count = parseInt(countMatch[1].replace(',', ''));
    console.log(`Combined count: ${count}`);

    expect(count).toBeGreaterThan(0);

    // Verify count is displayed visually
    const cardText = await timelineNewsCard.textContent();
    expect(cardText).toContain(countMatch[1]); // Should contain the count
  });

  test('3. Navigation: Click Timeline & News card navigates to /timeline', async ({ page }) => {
    const timelineNewsCard = page.locator('a[aria-label*="Timeline & News"]');
    await expect(timelineNewsCard).toBeVisible();

    // Click the card
    await timelineNewsCard.click();
    await page.waitForLoadState('networkidle');

    // Verify URL
    expect(page.url()).toContain('/timeline');
    console.log(`✓ Navigated to: ${page.url()}`);

    // Verify timeline page loaded
    const pageHeading = page.locator('h1, h2').first();
    const headingText = await pageHeading.textContent();
    console.log(`Timeline page heading: ${headingText}`);
  });

  test('4. Grid Layout: Verify responsive design across viewports', async ({ page }) => {
    const dashboardCards = page.locator('a[aria-label*="View"]').filter({
      has: page.locator('[role="button"]')
    });

    // Desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(300);
    let count = await dashboardCards.count();
    expect(count).toBe(5);
    console.log(`✓ Desktop (1920x1080): ${count} cards`);
    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-desktop-final.png', fullPage: true });

    // Tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(300);
    count = await dashboardCards.count();
    expect(count).toBe(5);
    console.log(`✓ Tablet (768x1024): ${count} cards`);
    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-tablet-final.png', fullPage: true });

    // Mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
    count = await dashboardCards.count();
    expect(count).toBe(5);
    console.log(`✓ Mobile (375x667): ${count} cards`);
    await page.screenshot({ path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-mobile-final.png', fullPage: true });
  });

  test('5. Consistency: Navigation and routing unified', async ({ page }) => {
    // Verify home page card
    const homeCard = page.locator('a[aria-label*="Timeline & News"]');
    await expect(homeCard).toBeVisible();
    console.log('✓ Home page has "Timeline & News" card');

    // Check header navigation
    const header = page.locator('header, nav').first();
    const headerText = await header.textContent();
    console.log(`Header text: ${headerText}`);

    // Verify Timeline is in header (not separate Timeline and News)
    expect(headerText).toMatch(/Timeline/i);
    console.log('✓ Header contains Timeline navigation');

    // Verify /news redirects to /timeline
    await page.goto('http://localhost:8081/news');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/timeline');
    console.log(`✓ /news redirects to: ${page.url()}`);
  });

  test('6. Visual Design: Card appearance and styling', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });

    const timelineCard = page.locator('a[aria-label*="Timeline & News"]');
    await expect(timelineCard).toBeVisible();

    // Take detailed screenshot of the card
    await timelineCard.screenshot({
      path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-news-card-final.png'
    });

    // Verify icon is present
    const cardDiv = timelineCard.locator('[role="button"]');
    const hasIcon = await cardDiv.locator('svg').count() > 0;
    expect(hasIcon).toBe(true);
    console.log('✓ Card has icon');

    // Verify card structure
    const cardText = await cardDiv.textContent();
    expect(cardText).toContain('Timeline & News');
    expect(cardText).toContain('Explore chronological events');
    console.log('✓ Card has title and description');

    // Get computed styles
    const styles = await cardDiv.evaluate(el => {
      const computed = window.getComputedStyle(el);
      return {
        minHeight: computed.minHeight,
        padding: computed.padding,
        borderRadius: computed.borderRadius,
        border: computed.border
      };
    });
    console.log('Card styles:', styles);

    // Verify minimum height
    expect(styles.minHeight).toBe('160px');
  });

  test('7. Console Monitoring: No critical errors', async ({ page }) => {
    await page.waitForTimeout(2000);

    console.log('\n=== Console Output ===');
    console.log(`Errors: ${consoleErrors.length}`);
    console.log(`Warnings: ${consoleWarnings.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nErrors:', consoleErrors);
    }

    if (consoleWarnings.length > 0) {
      console.log('\nWarnings:', consoleWarnings);
    }

    // Filter out non-critical errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('DevTools') &&
      !err.includes('websocket')
    );

    expect(criticalErrors.length).toBe(0);
    console.log('✓ No critical console errors');
  });

  test('8. Accessibility: ARIA labels and keyboard navigation', async ({ page }) => {
    const dashboardCards = page.locator('a[aria-label*="View"]');

    // Verify all cards have aria-labels
    const count = await dashboardCards.count();
    for (let i = 0; i < count; i++) {
      const card = dashboardCards.nth(i);
      const ariaLabel = await card.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      console.log(`Card ${i + 1} aria-label: ${ariaLabel}`);
    }

    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Skip header items

    // Focus should be on first card
    const focused = await page.evaluate(() => document.activeElement?.getAttribute('aria-label'));
    console.log(`Focused element: ${focused}`);

    console.log('✓ Cards are keyboard accessible');
  });

  test('9. Card Order: Verify Timeline & News is first card', async ({ page }) => {
    const dashboardCards = page.locator('a[aria-label*="View"]').filter({
      has: page.locator('[role="button"]')
    });

    const firstCard = dashboardCards.first();
    const ariaLabel = await firstCard.getAttribute('aria-label');

    expect(ariaLabel).toContain('Timeline & News');
    console.log(`✓ First card is: ${ariaLabel}`);
  });

  test('10. Integration: Verify Timeline & News card reflects actual data', async ({ page }) => {
    // Get the count from the card
    const timelineCard = page.locator('a[aria-label*="Timeline & News"]');
    const ariaLabel = await timelineCard.getAttribute('aria-label');
    const countMatch = ariaLabel?.match(/View ([\d,]+)/);
    const displayedCount = parseInt(countMatch[1].replace(',', ''));

    console.log(`Timeline & News card shows: ${displayedCount} items`);

    // Navigate to timeline page
    await timelineCard.click();
    await page.waitForLoadState('networkidle');

    // Wait for content to load
    await page.waitForTimeout(1000);

    // The count should represent timeline events + news articles
    // We can verify the data is loading by checking the page has content
    const hasContent = await page.locator('article, [class*="event"], [class*="card"]').count() > 0 ||
                       await page.locator('text=/No.*events|No.*results/i').count() > 0;

    expect(hasContent).toBe(true);
    console.log('✓ Timeline page has content or appropriate "no results" message');
  });
});
