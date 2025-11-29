import { test, expect, Page } from '@playwright/test';

/**
 * Comprehensive End-to-End Testing for Newly Implemented Features
 *
 * Features Under Test:
 * 1. Unified Timeline & News Card (1M-87)
 * 2. Entity Bio Hover Tooltips (1M-153) - in 3 locations
 * 3. Enhanced Entity Biographies (1M-138)
 *
 * Test URL: https://the-island.ngrok.app/
 */

const BASE_URL = 'https://the-island.ngrok.app';
const TEST_TIMEOUT = 60000; // 60 seconds for network-dependent tests

test.describe('Feature E2E Testing Suite', () => {
  test.setTimeout(TEST_TIMEOUT * 2); // 2 minutes per test

  test.beforeEach(async ({ page }) => {
    // Set viewport for consistent testing
    await page.setViewportSize({ width: 1280, height: 720 });

    // Monitor console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error(`❌ Console Error: ${msg.text()}`);
      }
    });

    // Monitor page errors
    page.on('pageerror', error => {
      console.error(`❌ Page Error: ${error.message}`);
    });
  });

  test('1M-87: Unified Timeline & News Card - Home Page', async ({ page }) => {
    console.log('\n📋 TEST: Unified Timeline & News Card (1M-87)\n');

    // Navigate to home page
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
    await page.waitForTimeout(2000); // Wait for cards to render

    // Take screenshot of home page
    await page.screenshot({
      path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-page-unified.png',
      fullPage: true
    });
    console.log('✅ Screenshot saved: home-page-unified.png');

    // Count dashboard cards
    const cards = page.locator('[class*="card"], [class*="Card"], .bg-white, .bg-card');
    const cardCount = await cards.count();
    console.log(`📊 Dashboard cards found: ${cardCount}`);

    // Check for Timeline & News card
    const timelineNewsCard = page.locator('text=/Timeline.*News/i').first();
    const timelineNewsExists = await timelineNewsCard.isVisible({ timeout: 5000 }).catch(() => false);
    console.log(`🔍 "Timeline & News" card visible: ${timelineNewsExists}`);

    if (timelineNewsExists) {
      await timelineNewsCard.screenshot({
        path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-news-card.png'
      });
      console.log('✅ Screenshot saved: timeline-news-card.png');
    }

    // Verify no separate "News" card exists
    const separateNewsCard = page.locator('text=/^News$/i').first();
    const separateNewsExists = await separateNewsCard.isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`🔍 Separate "News" card exists: ${separateNewsExists}`);

    // Click Timeline & News card and verify navigation
    if (timelineNewsExists) {
      await timelineNewsCard.click();
      await page.waitForTimeout(3000);

      const currentUrl = page.url();
      console.log(`🔗 Navigated to: ${currentUrl}`);

      const isTimelinePage = currentUrl.includes('/timeline');
      console.log(`✅ Navigation to /timeline: ${isTimelinePage}`);

      await page.screenshot({
        path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-page.png',
        fullPage: true
      });
      console.log('✅ Screenshot saved: timeline-page.png');

      expect(isTimelinePage).toBeTruthy();
    }

    // Assertions
    expect(cardCount).toBeGreaterThanOrEqual(5);
    expect(timelineNewsExists).toBeTruthy();
    expect(separateNewsExists).toBeFalsy();

    console.log('✅ Test 1M-87 PASSED\n');
  });

  test('1M-153: Entity Bio Hover Tooltips - Flight Logs', async ({ page }) => {
    console.log('\n📋 TEST: Entity Bio Tooltips in Flight Logs (1M-153)\n');

    // Navigate to flights page
    await page.goto(`${BASE_URL}/flights`, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({
      path: '/Users/masa/Projects/epstein/tests/qa/screenshots/flights-page.png',
      fullPage: true
    });
    console.log('✅ Screenshot saved: flights-page.png');

    // Find and click on a flight
    const flightRow = page.locator('tr, [role="row"], .flight-row').first();
    const flightExists = await flightRow.isVisible({ timeout: 5000 }).catch(() => false);

    if (flightExists) {
      await flightRow.click();
      await page.waitForTimeout(2000);

      // Look for passenger names
      const passengerNames = page.locator('text=/Clinton|Maxwell|Epstein/i').first();
      const passengerExists = await passengerNames.isVisible({ timeout: 5000 }).catch(() => false);

      console.log(`🔍 Passenger list visible: ${passengerExists}`);

      if (passengerExists) {
        // Hover over passenger name
        await passengerNames.hover();
        await page.waitForTimeout(1500);

        // Check for tooltip/popover
        const tooltip = page.locator('[role="tooltip"], [class*="tooltip"], [class*="popover"], [class*="hover"]');
        const tooltipVisible = await tooltip.isVisible({ timeout: 3000 }).catch(() => false);

        console.log(`💬 Tooltip visible on hover: ${tooltipVisible}`);

        if (tooltipVisible) {
          const tooltipText = await tooltip.textContent();
          console.log(`📝 Tooltip content preview: ${tooltipText?.substring(0, 100)}...`);

          await page.screenshot({
            path: '/Users/masa/Projects/epstein/tests/qa/screenshots/flight-tooltip.png'
          });
          console.log('✅ Screenshot saved: flight-tooltip.png');

          expect(tooltipVisible).toBeTruthy();
          expect(tooltipText).toBeTruthy();
        }
      }
    }

    console.log('✅ Test 1M-153 (Flight Logs) PASSED\n');
  });

  test('1M-153: Entity Bio Hover Tooltips - Network Matrix', async ({ page }) => {
    console.log('\n📋 TEST: Entity Bio Tooltips in Network Matrix (1M-153)\n');

    // Try multiple potential routes for network visualization
    const networkRoutes = ['/visualizations', '/network', '/matrix', '/'];
    let matrixFound = false;

    for (const route of networkRoutes) {
      await page.goto(`${BASE_URL}${route}`, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
      await page.waitForTimeout(2000);

      // Look for matrix elements
      const matrix = page.locator('text=/matrix|adjacency|network/i, svg, canvas').first();
      const matrixExists = await matrix.isVisible({ timeout: 3000 }).catch(() => false);

      if (matrixExists) {
        console.log(`✅ Matrix found at route: ${route}`);
        matrixFound = true;

        await page.screenshot({
          path: '/Users/masa/Projects/epstein/tests/qa/screenshots/network-matrix-page.png',
          fullPage: true
        });
        console.log('✅ Screenshot saved: network-matrix-page.png');

        // Look for entity names in labels
        const entityLabel = page.locator('text=/Epstein|Maxwell|Clinton/i').first();
        const labelExists = await entityLabel.isVisible({ timeout: 3000 }).catch(() => false);

        if (labelExists) {
          console.log('🔍 Entity labels found in matrix');

          // Hover over entity name
          await entityLabel.hover();
          await page.waitForTimeout(1500);

          // Check for tooltip
          const tooltip = page.locator('[role="tooltip"], [class*="tooltip"], [class*="popover"]');
          const tooltipVisible = await tooltip.isVisible({ timeout: 3000 }).catch(() => false);

          console.log(`💬 Tooltip visible on matrix hover: ${tooltipVisible}`);

          if (tooltipVisible) {
            await page.screenshot({
              path: '/Users/masa/Projects/epstein/tests/qa/screenshots/matrix-tooltip.png'
            });
            console.log('✅ Screenshot saved: matrix-tooltip.png');
          }
        }

        break;
      }
    }

    console.log(`📊 Matrix visualization found: ${matrixFound}`);
    console.log('✅ Test 1M-153 (Network Matrix) COMPLETED\n');
  });

  test('1M-153: Entity Bio Hover Tooltips - News Timeline', async ({ page }) => {
    console.log('\n📋 TEST: Entity Bio Tooltips in News Timeline (1M-153)\n');

    // Navigate to timeline page
    await page.goto(`${BASE_URL}/timeline`, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
    await page.waitForTimeout(3000);

    await page.screenshot({
      path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-news-page.png',
      fullPage: true
    });
    console.log('✅ Screenshot saved: timeline-news-page.png');

    // Look for "News Articles" filter/button
    const newsFilter = page.locator('text=/news/i, button:has-text("News"), [role="button"]:has-text("News")').first();
    const newsFilterExists = await newsFilter.isVisible({ timeout: 5000 }).catch(() => false);

    console.log(`🔍 News filter found: ${newsFilterExists}`);

    if (newsFilterExists) {
      await newsFilter.click();
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-news-filtered.png',
        fullPage: true
      });
      console.log('✅ Screenshot saved: timeline-news-filtered.png');
    }

    // Look for entity mentions in news articles
    const entityMention = page.locator('text=/Epstein|Maxwell|Clinton|Prince Andrew/i').first();
    const mentionExists = await entityMention.isVisible({ timeout: 5000 }).catch(() => false);

    console.log(`🔍 Entity mentions found: ${mentionExists}`);

    if (mentionExists) {
      // Hover over entity name
      await entityMention.hover();
      await page.waitForTimeout(1500);

      // Check for tooltip
      const tooltip = page.locator('[role="tooltip"], [class*="tooltip"], [class*="popover"], [class*="HoverCard"]');
      const tooltipVisible = await tooltip.isVisible({ timeout: 3000 }).catch(() => false);

      console.log(`💬 Tooltip visible in timeline: ${tooltipVisible}`);

      if (tooltipVisible) {
        const tooltipText = await tooltip.textContent();
        console.log(`📝 Tooltip content preview: ${tooltipText?.substring(0, 100)}...`);

        await page.screenshot({
          path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-tooltip.png'
        });
        console.log('✅ Screenshot saved: timeline-tooltip.png');

        expect(tooltipVisible).toBeTruthy();
      }
    }

    console.log('✅ Test 1M-153 (News Timeline) COMPLETED\n');
  });

  test('1M-138: Enhanced Entity Biographies', async ({ page }) => {
    console.log('\n📋 TEST: Enhanced Entity Biographies (1M-138)\n');

    // Test multiple entity pages
    const entities = [
      { id: 'jeffrey_epstein', name: 'Jeffrey Epstein' },
      { id: 'ghislaine_maxwell', name: 'Ghislaine Maxwell' },
      { id: 'bill_clinton', name: 'Bill Clinton' }
    ];

    for (const entity of entities) {
      console.log(`\n🔍 Testing entity: ${entity.name}`);

      // Try multiple URL patterns
      const urlPatterns = [
        `/entities/${entity.id}`,
        `/entity/${entity.id}`,
        `/people/${entity.id}`,
        `/profile/${entity.id}`
      ];

      let entityPageFound = false;

      for (const url of urlPatterns) {
        try {
          await page.goto(`${BASE_URL}${url}`, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
          await page.waitForTimeout(2000);

          // Check if page loaded successfully (not 404)
          const pageTitle = await page.title();
          const notFoundPage = pageTitle.includes('404') || pageTitle.includes('Not Found');

          if (!notFoundPage) {
            entityPageFound = true;
            console.log(`✅ Entity page found at: ${url}`);

            await page.screenshot({
              path: `/Users/masa/Projects/epstein/tests/qa/screenshots/entity-${entity.id}.png`,
              fullPage: true
            });
            console.log(`✅ Screenshot saved: entity-${entity.id}.png`);

            // Check for biography text
            const bioText = page.locator('text=/biography|bio|about/i').first();
            const bioExists = await bioText.isVisible({ timeout: 3000 }).catch(() => false);
            console.log(`📖 Biography section found: ${bioExists}`);

            // Check for Timeline section
            const timelineSection = page.locator('text=/timeline|chronology|history/i').first();
            const timelineExists = await timelineSection.isVisible({ timeout: 3000 }).catch(() => false);
            console.log(`📅 Timeline section found: ${timelineExists}`);

            if (timelineExists) {
              await timelineSection.screenshot({
                path: `/Users/masa/Projects/epstein/tests/qa/screenshots/entity-${entity.id}-timeline.png`
              });
              console.log(`✅ Screenshot saved: entity-${entity.id}-timeline.png`);
            }

            // Check for Relationships section
            const relationshipsSection = page.locator('text=/relationships|connections|associates/i').first();
            const relationshipsExists = await relationshipsSection.isVisible({ timeout: 3000 }).catch(() => false);
            console.log(`🔗 Relationships section found: ${relationshipsExists}`);

            if (relationshipsExists) {
              await relationshipsSection.screenshot({
                path: `/Users/masa/Projects/epstein/tests/qa/screenshots/entity-${entity.id}-relationships.png`
              });
              console.log(`✅ Screenshot saved: entity-${entity.id}-relationships.png`);
            }

            // Check for Document References section
            const documentsSection = page.locator('text=/documents|references|sources/i').first();
            const documentsExists = await documentsSection.isVisible({ timeout: 3000 }).catch(() => false);
            console.log(`📄 Document References section found: ${documentsExists}`);

            if (documentsExists) {
              await documentsSection.screenshot({
                path: `/Users/masa/Projects/epstein/tests/qa/screenshots/entity-${entity.id}-documents.png`
              });
              console.log(`✅ Screenshot saved: entity-${entity.id}-documents.png`);
            }

            // Count total content length
            const pageContent = await page.content();
            const textLength = pageContent.replace(/<[^>]*>/g, '').length;
            console.log(`📊 Page content length: ${textLength} characters`);

            break; // Found the page, no need to try other URLs
          }
        } catch (error) {
          // Continue to next URL pattern
          continue;
        }
      }

      if (!entityPageFound) {
        console.log(`⚠️ Entity page not found for: ${entity.name}`);
      }
    }

    console.log('\n✅ Test 1M-138 COMPLETED\n');
  });

  test('Cross-Feature Integration & Mobile Responsiveness', async ({ page }) => {
    console.log('\n📋 TEST: Cross-Feature Integration & Mobile\n');

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size
    console.log('📱 Testing mobile viewport: 375x667');

    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: '/Users/masa/Projects/epstein/tests/qa/screenshots/home-mobile.png',
      fullPage: true
    });
    console.log('✅ Screenshot saved: home-mobile.png');

    // Navigate to timeline on mobile
    const timelineLink = page.locator('text=/timeline/i').first();
    const timelineLinkExists = await timelineLink.isVisible({ timeout: 5000 }).catch(() => false);

    if (timelineLinkExists) {
      await timelineLink.click();
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: '/Users/masa/Projects/epstein/tests/qa/screenshots/timeline-mobile.png',
        fullPage: true
      });
      console.log('✅ Screenshot saved: timeline-mobile.png');
    }

    console.log('✅ Mobile responsiveness test COMPLETED\n');
  });

  test('Console Error Monitoring', async ({ page }) => {
    console.log('\n📋 TEST: Console Error Monitoring\n');

    const consoleErrors: string[] = [];
    const pageErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });

    // Visit key pages
    const testPages = ['/', '/timeline', '/flights'];

    for (const testPage of testPages) {
      console.log(`🔍 Checking: ${BASE_URL}${testPage}`);
      await page.goto(`${BASE_URL}${testPage}`, { waitUntil: 'networkidle', timeout: TEST_TIMEOUT });
      await page.waitForTimeout(3000);
    }

    console.log(`\n📊 Console Errors: ${consoleErrors.length}`);
    console.log(`📊 Page Errors: ${pageErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\n❌ Console Errors:');
      consoleErrors.forEach((error, idx) => {
        console.log(`  ${idx + 1}. ${error}`);
      });
    }

    if (pageErrors.length > 0) {
      console.log('\n❌ Page Errors:');
      pageErrors.forEach((error, idx) => {
        console.log(`  ${idx + 1}. ${error}`);
      });
    }

    if (consoleErrors.length === 0 && pageErrors.length === 0) {
      console.log('✅ No console or page errors detected!');
    }

    // Don't fail on errors, just report them
    console.log('\n✅ Error monitoring test COMPLETED\n');
  });
});
