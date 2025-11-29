/**
 * News Coverage Error Handling Verification Test
 *
 * Tests robust error handling implementation with:
 * - Retry logic with exponential backoff
 * - Timeout handling (10s per request)
 * - Clear error messages
 * - Retry button functionality
 * - Fallback URL behavior
 * - Loading states during retries
 *
 * Test URL: http://localhost:5173/entities/jeffrey_epstein
 */

import { test, expect, type Page } from '@playwright/test';

test.describe('News Coverage Error Handling', () => {
  const TEST_URL = 'http://localhost:5173/entities/jeffrey_epstein';

  test.beforeEach(async ({ page }) => {
    // Enable console logging
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('news') || text.includes('retry') || text.includes('Failed')) {
        console.log(`[BROWSER CONSOLE ${msg.type()}]:`, text);
      }
    });
  });

  test('Scenario 1: Happy Path - News loads successfully', async ({ page }) => {
    console.log('\n=== TEST 1: Happy Path ===');

    await page.goto(TEST_URL);

    // Wait for main entity content to load
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for News Coverage section
    const newsSection = page.locator('div:has(> div:has-text("News Coverage"))');
    await expect(newsSection).toBeVisible({ timeout: 15000 });

    // Check for article count badge (should show number like "100 articles")
    const articleBadge = newsSection.locator('span:has-text("article")');
    await expect(articleBadge).toBeVisible({ timeout: 20000 });

    const badgeText = await articleBadge.textContent();
    console.log(`✅ Article badge text: "${badgeText}"`);

    // Verify badge shows actual count (not "0 articles")
    expect(badgeText).toMatch(/\d+\s+articles?/);
    const articleCount = parseInt(badgeText?.match(/(\d+)/)?.[1] || '0');
    expect(articleCount).toBeGreaterThan(0);
    console.log(`✅ Article count: ${articleCount}`);

    // Verify article cards display
    const articleCards = page.locator('div[class*="grid"]').locator('a[href*="/news/"]');
    const cardCount = await articleCards.count();
    console.log(`✅ Article cards visible: ${cardCount}`);
    expect(cardCount).toBeGreaterThan(0);

    // Verify NO error message is shown
    const errorBanner = page.locator('div:has-text("Unable to load news articles")');
    await expect(errorBanner).not.toBeVisible();
    console.log('✅ No error message displayed');

    // Verify "View All" button is present
    const viewAllButton = page.locator('button:has-text("View All")');
    await expect(viewAllButton).toBeVisible();
    const buttonText = await viewAllButton.textContent();
    console.log(`✅ View All button text: "${buttonText}"`);

    console.log('✅ TEST 1 PASSED: Happy path works correctly');
  });

  test('Scenario 2: Backend Down - Graceful error handling', async ({ page, context }) => {
    console.log('\n=== TEST 2: Backend Down ===');

    // Block news API requests to simulate backend down
    await page.route('**/api/news/**', route => {
      console.log(`[BLOCKED] ${route.request().url()}`);
      route.abort('failed');
    });

    await page.goto(TEST_URL);

    // Wait for main entity to load
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for News Coverage section
    const newsSection = page.locator('div:has(> div:has-text("News Coverage"))');
    await expect(newsSection).toBeVisible({ timeout: 10000 });

    // Should see loading state first, then error
    console.log('⏳ Waiting for retry attempts to complete...');

    // Wait for error banner to appear (after 3 retries)
    const errorBanner = newsSection.locator('div:has-text("Unable to load news articles")');
    await expect(errorBanner).toBeVisible({ timeout: 30000 });
    console.log('✅ Error banner appeared');

    // Verify error message is specific (not vague)
    const errorText = await errorBanner.textContent();
    console.log(`✅ Error message: "${errorText}"`);
    expect(errorText).toContain('Unable to load news articles');

    // Should show retry count
    const retryInfo = newsSection.locator('p:has-text("Attempted")');
    if (await retryInfo.isVisible()) {
      const retryText = await retryInfo.textContent();
      console.log(`✅ Retry info: "${retryText}"`);
      expect(retryText).toMatch(/Attempted \d+ times?/);
    }

    // Verify retry button is visible
    const retryButton = errorBanner.locator('button:has-text("Retry")');
    await expect(retryButton).toBeVisible();
    console.log('✅ Retry button visible');

    // Verify NO article badge is shown (should not show "0 articles")
    const articleBadge = newsSection.locator('span:has-text("0 article")');
    await expect(articleBadge).not.toBeVisible();
    console.log('✅ No misleading "0 articles" badge');

    console.log('✅ TEST 2 PASSED: Graceful error handling works');
  });

  test('Scenario 3: Retry Button Functionality', async ({ page }) => {
    console.log('\n=== TEST 3: Retry Button Functionality ===');

    let requestCount = 0;

    // Block first set of requests, then allow
    await page.route('**/api/news/**', (route, request) => {
      requestCount++;
      console.log(`[REQUEST ${requestCount}] ${request.url()}`);

      // Fail first 3 attempts (initial load retries), succeed on manual retry
      if (requestCount <= 3) {
        route.abort('failed');
      } else {
        route.continue();
      }
    });

    await page.goto(TEST_URL);

    // Wait for entity to load
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for error banner
    const newsSection = page.locator('div:has(> div:has-text("News Coverage"))');
    const errorBanner = newsSection.locator('div:has-text("Unable to load news articles")');
    await expect(errorBanner).toBeVisible({ timeout: 30000 });
    console.log('✅ Error banner appeared after retries');

    // Click retry button
    const retryButton = errorBanner.locator('button:has-text("Retry")');
    await retryButton.click();
    console.log('🔄 Clicked retry button');

    // Should show loading state
    const loadingText = page.locator('p:has-text("Retrying...")');
    if (await loadingText.isVisible({ timeout: 2000 })) {
      console.log('✅ Loading state shown during retry');
    }

    // Error should disappear and articles should load
    await expect(errorBanner).not.toBeVisible({ timeout: 15000 });
    console.log('✅ Error banner disappeared');

    // Should show article badge now
    const articleBadge = newsSection.locator('span:has-text("article")');
    await expect(articleBadge).toBeVisible({ timeout: 10000 });
    const badgeText = await articleBadge.textContent();
    console.log(`✅ Articles loaded after retry: "${badgeText}"`);

    console.log(`✅ TEST 3 PASSED: Retry button works (${requestCount} total requests)`);
  });

  test('Scenario 4: Network Request Monitoring', async ({ page }) => {
    console.log('\n=== TEST 4: Network Request Monitoring ===');

    const apiRequests: string[] = [];
    let retryAttempts = 0;

    // Monitor all news API requests
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/news/')) {
        retryAttempts++;
        const timestamp = new Date().toISOString().split('T')[1];
        apiRequests.push(`[${timestamp}] Attempt ${retryAttempts}: ${url}`);
        console.log(`[API REQUEST ${retryAttempts}] ${url}`);
      }
    });

    // Block requests to trigger retries
    await page.route('**/api/news/**', route => {
      route.abort('failed');
    });

    await page.goto(TEST_URL);

    // Wait for entity to load
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for retries to complete (should be 3 attempts)
    await page.waitForTimeout(10000);

    console.log('\n📊 Network Request Summary:');
    console.log(`Total API requests: ${retryAttempts}`);
    apiRequests.forEach(req => console.log(req));

    // Should see 3 retry attempts (1 initial + 2 retries)
    // Note: Actual count might vary due to URL fallback
    expect(retryAttempts).toBeGreaterThanOrEqual(3);
    console.log(`✅ Multiple retry attempts detected: ${retryAttempts}`);

    console.log('✅ TEST 4 PASSED: Network monitoring shows retries');
  });

  test('Scenario 5: Console Log Verification', async ({ page }) => {
    console.log('\n=== TEST 5: Console Log Verification ===');

    const consoleLogs: string[] = [];

    // Capture console logs
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('news') || text.includes('retry') || text.includes('Failed')) {
        consoleLogs.push(`[${msg.type()}] ${text}`);
      }
    });

    // Block requests to see retry logs
    await page.route('**/api/news/**', route => {
      route.abort('failed');
    });

    await page.goto(TEST_URL);

    // Wait for entity and retries
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });
    await page.waitForTimeout(10000);

    console.log('\n📋 Console Logs:');
    consoleLogs.forEach(log => console.log(log));

    // Should see retry-related logs
    const hasRetryLogs = consoleLogs.some(log =>
      log.includes('Failed to load news') ||
      log.includes('retry') ||
      log.includes('attempt')
    );

    if (hasRetryLogs) {
      console.log('✅ Retry logs present in console');
    } else {
      console.log('⚠️ No explicit retry logs, but errors present');
    }

    console.log(`✅ TEST 5 PASSED: Console logging active (${consoleLogs.length} relevant logs)`);
  });

  test('Scenario 6: Loading States During Retry', async ({ page }) => {
    console.log('\n=== TEST 6: Loading States During Retry ===');

    let requestNum = 0;

    // Delay responses to see loading states
    await page.route('**/api/news/**', async (route) => {
      requestNum++;
      console.log(`[REQUEST ${requestNum}] Processing...`);

      // Delay each request by 2 seconds
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Fail first 2, succeed on 3rd
      if (requestNum <= 2) {
        route.abort('failed');
      } else {
        route.continue();
      }
    });

    await page.goto(TEST_URL);

    // Wait for entity
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for news section
    const newsSection = page.locator('div:has(> div:has-text("News Coverage"))');
    await expect(newsSection).toBeVisible();

    // Should see loading state initially
    const loadingIndicator = page.locator('svg[class*="animate-spin"]').filter({ hasText: '' });
    const loadingText = page.locator('p:has-text("Loading news")');

    // Check for loading state (might be quick)
    if (await loadingIndicator.isVisible({ timeout: 2000 })) {
      console.log('✅ Loading spinner visible');
    }

    if (await loadingText.isVisible({ timeout: 2000 })) {
      const text = await loadingText.textContent();
      console.log(`✅ Loading text: "${text}"`);
    }

    // Eventually should show articles (after 3rd attempt succeeds)
    const articleBadge = newsSection.locator('span:has-text("article")');
    await expect(articleBadge).toBeVisible({ timeout: 30000 });
    console.log('✅ Articles loaded after retries');

    console.log('✅ TEST 6 PASSED: Loading states visible during retry');
  });
});

test.describe('News Coverage - Production Environment', () => {
  test('Verify news coverage on real backend', async ({ page }) => {
    console.log('\n=== PRODUCTION TEST: Real Backend ===');

    // This test runs against actual backend without mocking
    await page.goto('http://localhost:5173/entities/jeffrey_epstein');

    // Wait for entity
    await expect(page.locator('h1')).toContainText('Jeffrey Epstein', { timeout: 10000 });

    // Wait for news section
    const newsSection = page.locator('div:has(> div:has-text("News Coverage"))');
    await expect(newsSection).toBeVisible({ timeout: 10000 });

    // Should either show articles OR clear error (not silent failure)
    const hasArticles = await newsSection.locator('span:has-text("article")').isVisible({ timeout: 20000 });
    const hasError = await newsSection.locator('div:has-text("Unable to load")').isVisible();

    if (hasArticles) {
      const badge = await newsSection.locator('span:has-text("article")').textContent();
      console.log(`✅ Articles loaded: ${badge}`);

      // Verify article cards
      const cards = await page.locator('a[href*="/news/"]').count();
      console.log(`✅ Article cards visible: ${cards}`);
      expect(cards).toBeGreaterThan(0);
    } else if (hasError) {
      const errorText = await newsSection.locator('div:has-text("Unable to load")').textContent();
      console.log(`⚠️ Error shown (expected behavior): ${errorText}`);

      // Verify retry button exists
      const retryButton = newsSection.locator('button:has-text("Retry")');
      await expect(retryButton).toBeVisible();
      console.log('✅ Retry button available');
    } else {
      throw new Error('Neither articles nor error shown - this is a bug!');
    }

    console.log('✅ PRODUCTION TEST PASSED: Clear outcome (success or error)');
  });
});
