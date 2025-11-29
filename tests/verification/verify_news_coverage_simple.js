const { chromium } = require('playwright');

(async () => {
  console.log('\n=== NEWS COVERAGE VERIFICATION ON PORT 5173 ===\n');

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Track API requests
  const apiRequests = [];
  let apiResponseData = null;

  page.on('request', request => {
    if (request.url().includes('/api/news/articles')) {
      const url = request.url();
      apiRequests.push({ url, method: request.method() });
      console.log(`[REQUEST] ${request.method()} ${url}`);
    }
  });

  page.on('response', async response => {
    if (response.url().includes('/api/news/articles')) {
      const status = response.status();
      console.log(`[RESPONSE] Status: ${status} for ${response.url()}`);

      if (status === 200) {
        try {
          const data = await response.json();
          apiResponseData = data;
          const articleCount = data.articles?.length || 0;
          console.log(`[API DATA] Received ${articleCount} articles from API`);
          if (articleCount > 0) {
            console.log(`[API DATA] First 3 article titles from API response:`);
            data.articles.slice(0, 3).forEach((article, idx) => {
              console.log(`  ${idx + 1}. ${article.title}`);
            });
          }
        } catch (e) {
          console.log(`[API ERROR] Failed to parse JSON: ${e.message}`);
        }
      }
    }
  });

  // Track console messages
  const consoleErrors = [];
  const consoleWarnings = [];

  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      consoleErrors.push(text);
      console.log(`[CONSOLE ERROR] ${text}`);
    } else if (type === 'warning') {
      consoleWarnings.push(text);
    }
  });

  // Navigate to entity page
  console.log('[NAVIGATION] Going to http://localhost:5173/entities/jeffrey_epstein');
  try {
    await page.goto('http://localhost:5173/entities/jeffrey_epstein', {
      waitUntil: 'networkidle',
      timeout: 30000
    });
    console.log('[NAVIGATION] Page loaded successfully');
  } catch (e) {
    console.log(`[NAVIGATION ERROR] ${e.message}`);
    await browser.close();
    process.exit(1);
  }

  // Wait for News Coverage section
  try {
    await page.waitForSelector('text=News Coverage', { timeout: 10000 });
    console.log('[DOM] Found "News Coverage" section');
  } catch (e) {
    console.log(`[DOM WARNING] Could not find "News Coverage" text: ${e.message}`);
  }

  // Wait for content to load
  await page.waitForTimeout(3000);

  // Extract News Coverage badge text
  try {
    const badgeText = await page.locator('text=News Coverage').locator('..').locator('span').first().textContent();
    console.log(`\n[BADGE TEXT] News Coverage badge shows: "${badgeText}"`);
  } catch (e) {
    console.log(`\n[BADGE WARNING] Could not extract badge text: ${e.message}`);

    // Try alternative approach - get all text content
    const pageText = await page.textContent('body');
    const newsCoverageMatch = pageText.match(/News Coverage[^\n]*?(\d+)\s*article/i);
    if (newsCoverageMatch) {
      console.log(`[BADGE TEXT] Found in page text: "${newsCoverageMatch[0]}"`);
    }
  }

  // Try to find article titles
  console.log('\n[SEARCHING FOR ARTICLE TITLES]');

  // Method 1: Look for h3 elements
  const h3Titles = await page.$$eval('h3', elements =>
    elements.map(el => el.textContent?.trim()).filter(text => text && text.length > 10)
  );

  if (h3Titles.length > 0) {
    console.log(`[PAGE TITLES] Found ${h3Titles.length} h3 titles, first 5:`);
    h3Titles.slice(0, 5).forEach((title, idx) => {
      console.log(`  ${idx + 1}. ${title}`);
    });
  }

  // Method 2: Look for any element with "article" or "title" in class
  const articleElements = await page.$$eval('[class*="article"], [class*="title"]', elements =>
    elements.map(el => ({
      tag: el.tagName,
      class: el.className,
      text: el.textContent?.trim().substring(0, 100)
    })).filter(item => item.text && item.text.length > 10).slice(0, 5)
  );

  if (articleElements.length > 0) {
    console.log(`\n[ARTICLE ELEMENTS] Found ${articleElements.length} potential article elements:`);
    articleElements.forEach((item, idx) => {
      console.log(`  ${idx + 1}. <${item.tag} class="${item.class}"> ${item.text}`);
    });
  }

  // Check if "No articles found" is present
  const noArticlesText = await page.locator('text=No articles found').count();
  if (noArticlesText > 0) {
    console.log('\n[WARNING] Page shows "No articles found" message');
  }

  // Summary
  console.log('\n=== VERIFICATION SUMMARY ===');
  console.log(`API Requests Made: ${apiRequests.length}`);
  console.log(`API Response Articles: ${apiResponseData?.articles?.length || 0}`);
  console.log(`Console Errors: ${consoleErrors.length}`);
  console.log(`Console Warnings: ${consoleWarnings.length}`);
  console.log(`Page shows "No articles found": ${noArticlesText > 0 ? 'YES (PROBLEM!)' : 'NO (Good)'}`);

  if (consoleErrors.length > 0) {
    console.log('\nConsole Errors Detected:');
    consoleErrors.slice(0, 10).forEach((err, idx) => {
      console.log(`  ${idx + 1}. ${err.substring(0, 200)}`);
    });
  } else {
    console.log('\nNo console errors detected ✓');
  }

  // Final verification
  console.log('\n=== TEST RESULTS ===');
  const apiSuccess = apiRequests.length > 0 && apiResponseData?.articles?.length > 0;
  const noErrors = consoleErrors.length === 0;
  const noNoArticlesMessage = noArticlesText === 0;

  console.log(`✓ API called: ${apiRequests.length > 0}`);
  console.log(`✓ API returned articles: ${apiResponseData?.articles?.length > 0} (${apiResponseData?.articles?.length || 0} articles)`);
  console.log(`✓ No console errors: ${noErrors}`);
  console.log(`✓ No "No articles found" message: ${noNoArticlesMessage}`);

  const allPassed = apiSuccess && noErrors;
  console.log(`\nOVERALL: ${allPassed ? 'PASS ✓' : 'FAIL ✗'}`);

  await browser.close();
  process.exit(allPassed ? 0 : 1);
})();
