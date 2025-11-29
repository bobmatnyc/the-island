const puppeteer = require('puppeteer');

(async () => {
  console.log('Starting browser...');
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: { width: 1920, height: 1080 }
  });

  const page = await browser.newPage();

  // Listen to console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    if (msg.type() === 'error') {
      console.log('❌ Console Error:', text);
    }
  });

  // Listen to network requests
  let newsApiCalled = false;
  let newsApiResponse = null;

  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/news/articles') && url.includes('entity=jeffrey_epstein')) {
      newsApiCalled = true;
      console.log('📡 News API called:', url);
      console.log('   Status:', response.status());
      try {
        const data = await response.json();
        newsApiResponse = data;
        console.log('   Articles returned:', data.articles ? data.articles.length : 'N/A');
        console.log('   Total count:', data.total);
      } catch (e) {
        console.log('   Failed to parse response:', e.message);
      }
    }
  });

  console.log('Navigating to entity detail page...');
  await page.goto('http://localhost:5173/entities/jeffrey_epstein', {
    waitUntil: 'networkidle2',
    timeout: 30000
  });

  console.log('Page loaded. Waiting for News Coverage section...');

  // Wait for News Coverage section
  try {
    await page.waitForSelector('h2:has-text("News Coverage")', { timeout: 10000 });
    console.log('✅ News Coverage section found');
  } catch (e) {
    console.log('❌ News Coverage section not found');
  }

  // Wait a bit for data to load
  await page.waitForTimeout(3000);

  // Check for article count badge
  const badgeText = await page.evaluate(() => {
    // Try multiple selectors for the badge
    const selectors = [
      '.badge',
      '[class*="badge"]',
      '[class*="bg-blue"]',
      'span.rounded-full',
      '.text-xs.font-semibold'
    ];

    for (const selector of selectors) {
      const badges = Array.from(document.querySelectorAll(selector));
      for (const badge of badges) {
        const text = badge.textContent || '';
        if (text.match(/\d+/)) {
          return text;
        }
      }
    }
    return null;
  });

  console.log('\n📊 News Coverage Badge:', badgeText || 'Not found');

  // Count visible article cards
  const articleCount = await page.evaluate(() => {
    const selectors = [
      'article',
      '.news-article',
      '[class*="article"]',
      '.grid > div',
      '.rounded-lg.border'
    ];

    let maxCount = 0;
    for (const selector of selectors) {
      const count = document.querySelectorAll(selector).length;
      if (count > maxCount) maxCount = count;
    }
    return maxCount;
  });

  console.log('📰 Visible article cards:', articleCount);

  // Get article titles
  const titles = await page.evaluate(() => {
    const titleSelectors = ['h3', 'h4', '.font-semibold'];
    const titles = [];

    for (const selector of titleSelectors) {
      const elements = document.querySelectorAll(selector);
      elements.forEach(el => {
        const text = el.textContent?.trim();
        if (text && text.length > 10 && !titles.includes(text)) {
          titles.push(text);
        }
      });
    }
    return titles.slice(0, 5);
  });

  console.log('\n📝 Sample article titles:');
  titles.forEach((title, i) => console.log(`   ${i + 1}. ${title}`));

  // Check for "View All" button
  const viewAllButton = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, a'));
    for (const btn of buttons) {
      const text = btn.textContent || '';
      if (text.includes('View All') && text.toLowerCase().includes('news')) {
        return text.trim();
      }
    }
    return null;
  });

  console.log('\n🔘 View All button:', viewAllButton || 'Not found');

  // Take screenshot
  await page.screenshot({
    path: '/Users/masa/Projects/epstein/news-coverage-verification.png',
    fullPage: true
  });
  console.log('\n📸 Screenshot saved: news-coverage-verification.png');

  // Check for console errors related to news
  const newsErrors = consoleMessages.filter(msg =>
    msg.type === 'error' &&
    (msg.text.includes('news') || msg.text.includes('api') || msg.text.includes('articles'))
  );

  console.log('\n🔍 Console Errors (news-related):', newsErrors.length);
  if (newsErrors.length > 0) {
    newsErrors.forEach(err => console.log('   -', err.text));
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('VERIFICATION SUMMARY');
  console.log('='.repeat(60));
  console.log('✓ API Call Made:', newsApiCalled ? 'YES' : 'NO');
  console.log('✓ API Response:', newsApiResponse ? `${newsApiResponse.articles?.length || 0} articles` : 'N/A');
  console.log('✓ Badge Display:', badgeText || 'MISSING');
  console.log('✓ Article Cards:', articleCount);
  console.log('✓ View All Button:', viewAllButton ? 'YES' : 'NO');
  console.log('✓ Console Errors:', newsErrors.length);

  const success = newsApiCalled &&
                  newsApiResponse?.articles?.length >= 90 &&
                  articleCount >= 10 &&
                  newsErrors.length === 0;

  console.log('\n' + (success ? '✅ VERIFICATION PASSED' : '❌ VERIFICATION FAILED'));
  console.log('='.repeat(60));

  // Keep browser open for manual inspection
  console.log('\nBrowser will remain open for 10 seconds for manual inspection...');
  await page.waitForTimeout(10000);

  await browser.close();
})();
