import { test, expect } from '@playwright/test';

test.describe('News Coverage Display Verification', () => {
  test('DIAGNOSTIC: Verify news coverage display with full monitoring', async ({ page }) => {
    // Set longer timeout for this test
    test.setTimeout(60000);

    // === SETUP MONITORING ===
    const apiRequests: any[] = [];
    const apiResponses: any[] = [];
    const consoleMessages: string[] = [];
    const consoleErrors: string[] = [];

    // Monitor all API requests
    page.on('request', request => {
      if (request.url().includes('/api/news')) {
        const requestData = {
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
        };
        apiRequests.push(requestData);
        console.log('🌐 API Request:', request.url());
      }
    });

    // Monitor all API responses
    page.on('response', async response => {
      if (response.url().includes('/api/news')) {
        const responseData: any = {
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
          headers: response.headers(),
        };

        try {
          const body = await response.json();
          responseData.body = body;
          console.log('📥 API Response:', JSON.stringify({
            url: response.url(),
            status: response.status(),
            articleCount: Array.isArray(body.articles) ? body.articles.length : Array.isArray(body) ? body.length : 'N/A',
            total: body.total || body.count || 'N/A'
          }, null, 2));
        } catch (e) {
          responseData.bodyError = 'Failed to parse JSON';
          console.log('❌ Failed to parse response body');
        }

        apiResponses.push(responseData);
      }
    });

    // Monitor console messages
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push(text);
      if (msg.type() === 'error') {
        consoleErrors.push(text);
        console.log('🔴 Browser Console Error:', text);
      } else if (text.includes('news') || text.includes('article')) {
        console.log('💬 Browser Console:', text);
      }
    });

    // === NAVIGATE TO PAGE ===
    console.log('\n=== NAVIGATING TO PAGE ===');
    await page.goto('http://localhost:5173/entities/jeffrey_epstein', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait for page to load and network to be idle
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Allow time for API calls and rendering

    console.log('\n=== INSPECTING PAGE ELEMENTS ===');

    // Check if News Coverage section exists
    const newsCoverageSection = page.locator('h2:has-text("News Coverage"), h3:has-text("News Coverage")');
    const sectionExists = await newsCoverageSection.count() > 0;
    console.log('✓ News Coverage section exists:', sectionExists);

    // Check for badge elements
    const allBadges = page.locator('.badge, .bg-blue-100, [class*="badge"]');
    const badgeCount = await allBadges.count();
    console.log('✓ Total badge elements found:', badgeCount);

    // Look for article count badge specifically
    const articleBadge = page.locator('text=/\\d+\\s*articles?/i').first();
    const badgeVisible = await articleBadge.count() > 0;
    console.log('✓ Article count badge visible:', badgeVisible);

    if (badgeVisible) {
      const badgeText = await articleBadge.textContent();
      console.log('✓ Badge text:', badgeText);

      const countMatch = badgeText?.match(/(\d+)/);
      if (countMatch) {
        console.log('✓ Article count extracted:', countMatch[1]);
      }
    } else {
      console.log('❌ No article count badge found - checking why...');

      // Check if it says "0 articles"
      const zeroBadge = page.locator('text=/0\\s*articles?/i');
      const hasZero = await zeroBadge.count() > 0;
      if (hasZero) {
        console.log('⚠️ FOUND "0 articles" - This is the bug!');
      }
    }

    // Check for article cards
    const articleCards = page.locator('[class*="card"]').filter({
      has: page.locator('text=/source/i, text=/published/i, text=/credibility/i')
    });
    const cardCount = await articleCards.count();
    console.log('✓ Article cards found:', cardCount);

    // Check for error messages
    const errorMessages = page.locator('text=/error/i, text=/failed/i, text=/something went wrong/i');
    const hasError = await errorMessages.count() > 0;
    console.log('✓ Error messages visible:', hasError);

    if (hasError) {
      const errorText = await errorMessages.first().textContent();
      console.log('⚠️ Error message:', errorText);
    }

    // Check for loading states
    const loadingIndicators = page.locator('text=/loading/i, [class*="spinner"], [class*="skeleton"]');
    const isLoading = await loadingIndicators.count() > 0;
    console.log('✓ Loading indicators visible:', isLoading);

    // === API REQUEST ANALYSIS ===
    console.log('\n=== API REQUEST ANALYSIS ===');
    console.log('Total API requests made:', apiRequests.length);
    console.log('Total API responses received:', apiResponses.length);

    if (apiRequests.length === 0) {
      console.log('❌ CRITICAL: No API requests detected!');
      console.log('   This means the useEntityNews hook is not being called.');
      console.log('   Check if EntityDetail component renders the news section.');
    } else {
      console.log('✓ API requests detected:');
      apiRequests.forEach((req, i) => {
        console.log(`  ${i + 1}. ${req.method} ${req.url}`);
      });
    }

    if (apiResponses.length > 0) {
      console.log('\n✓ API responses received:');
      apiResponses.forEach((res, i) => {
        console.log(`  ${i + 1}. Status: ${res.status} ${res.statusText}`);
        if (res.body) {
          const articleCount = Array.isArray(res.body.articles)
            ? res.body.articles.length
            : Array.isArray(res.body)
            ? res.body.length
            : 'unknown';
          console.log(`      Articles in response: ${articleCount}`);
          console.log(`      Total count: ${res.body.total || res.body.count || 'N/A'}`);
        }
      });
    }

    // === CONSOLE ERRORS ===
    if (consoleErrors.length > 0) {
      console.log('\n=== CONSOLE ERRORS ===');
      consoleErrors.forEach((err, i) => {
        console.log(`${i + 1}. ${err}`);
      });
    } else {
      console.log('\n✓ No console errors detected');
    }

    // === GENERATE REPORT ===
    console.log('\n=== DIAGNOSTIC REPORT ===');

    const report = {
      timestamp: new Date().toISOString(),
      url: 'http://localhost:5173/entities/jeffrey_epstein',
      diagnosis: {
        newsSectionExists: sectionExists,
        badgeVisible: badgeVisible,
        articleCardsRendered: cardCount,
        apiRequestsMade: apiRequests.length,
        apiResponsesReceived: apiResponses.length,
        hasConsoleErrors: consoleErrors.length > 0,
        hasErrorMessages: hasError,
      },
      apiRequests: apiRequests.map(r => ({
        url: r.url,
        method: r.method,
      })),
      apiResponses: apiResponses.map(r => ({
        url: r.url,
        status: r.status,
        articleCount: Array.isArray(r.body?.articles)
          ? r.body.articles.length
          : Array.isArray(r.body)
          ? r.body.length
          : 0,
        total: r.body?.total || r.body?.count || 0,
      })),
      consoleErrors: consoleErrors,
      recommendations: [],
    };

    // Generate specific recommendations
    if (apiRequests.length === 0) {
      report.recommendations.push('CRITICAL: No API requests detected. Hook not being called.');
      report.recommendations.push('Check if useEntityNews is imported and used in EntityDetail.');
      report.recommendations.push('Verify entity name/ID is being passed to the hook.');
    } else if (apiResponses.length === 0) {
      report.recommendations.push('CRITICAL: Requests made but no responses. Network/CORS issue.');
    } else if (apiResponses.some(r => r.status !== 200)) {
      report.recommendations.push('API returned non-200 status. Check backend error logs.');
    } else if (
      apiResponses.some(r => (r.body?.articles?.length || r.body?.length || 0) > 0) &&
      cardCount === 0
    ) {
      report.recommendations.push('CRITICAL: Articles received but not rendered.');
      report.recommendations.push('Check if newsArticles state is being set correctly.');
      report.recommendations.push('Verify NewsArticleCard component rendering logic.');
    } else if (cardCount > 0) {
      report.recommendations.push('SUCCESS: Articles fetched and rendered correctly!');
    }

    console.log(JSON.stringify(report, null, 2));

    // Save report
    const fs = require('fs');
    const reportPath =
      '/Users/masa/Projects/epstein/news_coverage_verification_' +
      new Date().toISOString().replace(/[:.]/g, '-').replace(/\.\d+Z$/, '') +
      '.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log('\n📄 Report saved to:', reportPath);
  });

});
