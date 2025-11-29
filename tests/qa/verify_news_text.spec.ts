import { test, expect } from '@playwright/test';

test('Verify news coverage displays articles - TEXT ONLY', async ({ page }) => {
  console.log('\n=== NEWS COVERAGE TEXT VERIFICATION ===\n');

  // Track network requests
  const apiRequests: any[] = [];
  page.on('request', request => {
    if (request.url().includes('/api/news')) {
      apiRequests.push({
        url: request.url(),
        method: request.method()
      });
      console.log(`[REQUEST] ${request.method()} ${request.url()}`);
    }
  });

  page.on('response', async response => {
    if (response.url().includes('/api/news')) {
      console.log(`[RESPONSE] ${response.status()} ${response.url()}`);
      try {
        const json = await response.json();
        console.log(`[RESPONSE DATA] Articles count: ${json.articles?.length || 0}`);
        console.log(`[RESPONSE DATA] Total: ${json.total || 0}`);
        console.log(`[RESPONSE DATA] Has more: ${json.has_more}`);
      } catch (e) {
        console.log('[RESPONSE DATA] Failed to parse JSON');
      }
    }
  });

  // Track console messages
  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
      console.log(`[CONSOLE ERROR] ${msg.text()}`);
    }
  });

  // Navigate to entity page
  console.log('\n1. NAVIGATING TO PAGE...');
  await page.goto('http://localhost:3000/entities/jeffrey_epstein');

  // Wait for network to be idle
  console.log('\n2. WAITING FOR NETWORK IDLE...');
  await page.waitForLoadState('networkidle');

  // Wait a bit more for any delayed requests
  await page.waitForTimeout(2000);

  // Extract page title
  console.log('\n3. EXTRACTING PAGE CONTENT...');
  const pageTitle = await page.title();
  console.log(`Page Title: ${pageTitle}`);

  // Look for News Coverage section
  const newsCoverageSection = page.locator('text=News Coverage').first();
  const hasCoverageSection = await newsCoverageSection.isVisible().catch(() => false);
  console.log(`\nNews Coverage Section Visible: ${hasCoverageSection}`);

  if (hasCoverageSection) {
    // Try to find the badge with article count
    const badges = page.locator('[class*="badge"], [class*="Badge"]');
    const badgeCount = await badges.count();
    console.log(`\nFound ${badgeCount} badge elements`);

    for (let i = 0; i < Math.min(badgeCount, 10); i++) {
      const badgeText = await badges.nth(i).textContent();
      if (badgeText && badgeText.includes('article')) {
        console.log(`Badge ${i}: "${badgeText}"`);
      }
    }

    // Look for article titles
    const articleSelectors = [
      '[class*="article"]',
      '[class*="news"]',
      'h3',
      'h4',
      '[role="article"]'
    ];

    for (const selector of articleSelectors) {
      const elements = page.locator(selector);
      const count = await elements.count();
      if (count > 0) {
        console.log(`\nFound ${count} elements with selector: ${selector}`);

        // Get first 5 text contents
        for (let i = 0; i < Math.min(count, 5); i++) {
          const text = await elements.nth(i).textContent();
          if (text && text.length > 10 && text.length < 200) {
            console.log(`  ${i + 1}. ${text.trim().substring(0, 100)}`);
          }
        }
      }
    }
  }

  // Get all text content from the page
  console.log('\n4. SEARCHING FOR NEWS ARTICLE INDICATORS...');
  const bodyText = await page.locator('body').textContent();

  // Search for known article titles from API
  const knownTitles = [
    'Last Batch of Unsealed Jeffrey Epstein Documents',
    'Unsealed Court Documents Reveal Names',
    'Jeffrey Epstein List'
  ];

  for (const title of knownTitles) {
    const found = bodyText?.includes(title);
    console.log(`Looking for "${title}": ${found ? 'FOUND' : 'NOT FOUND'}`);
  }

  // Check for "100 articles" or similar text
  const articleCountMatches = bodyText?.match(/(\d+)\s*articles?/gi);
  if (articleCountMatches) {
    console.log(`\nArticle count indicators found: ${articleCountMatches.join(', ')}`);
  }

  // Summary
  console.log('\n=== VERIFICATION SUMMARY ===');
  console.log(`API Requests Made: ${apiRequests.length}`);
  console.log(`Console Errors: ${consoleErrors.length}`);
  if (consoleErrors.length > 0) {
    console.log('Errors:');
    consoleErrors.forEach((err, i) => console.log(`  ${i + 1}. ${err}`));
  }
  console.log(`News Coverage Section Present: ${hasCoverageSection}`);
  console.log('\n============================\n');

  // Assertions
  expect(apiRequests.length).toBeGreaterThan(0);
  expect(hasCoverageSection).toBe(true);
});
