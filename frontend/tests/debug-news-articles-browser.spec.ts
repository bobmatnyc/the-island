/**
 * Automated Browser Debugging Test
 *
 * This test captures ALL the critical debugging information:
 * - Network requests (URL, status, response)
 * - Console logs (debug output, errors)
 * - DOM state (what's actually rendered)
 * - Response data format
 */

import { test, expect } from '@playwright/test';

test.describe('News Articles Browser Debugging', () => {
  let networkRequests: any[] = [];
  let consoleLogs: any[] = [];
  let consoleErrors: any[] = [];

  test.beforeEach(async ({ page }) => {
    // Capture network requests
    page.on('request', request => {
      if (request.url().includes('/api/news')) {
        networkRequests.push({
          url: request.url(),
          method: request.method(),
          timestamp: new Date().toISOString()
        });
      }
    });

    page.on('response', async response => {
      if (response.url().includes('/api/news')) {
        const request = networkRequests.find(r => r.url === response.url());
        if (request) {
          request.status = response.status();
          request.statusText = response.statusText();
          request.headers = await response.allHeaders();

          try {
            request.responseBody = await response.json();
          } catch (e) {
            request.responseBody = await response.text();
          }
        }
      }
    });

    // Capture console logs
    page.on('console', msg => {
      const text = msg.text();
      const logEntry = {
        type: msg.type(),
        text: text,
        timestamp: new Date().toISOString()
      };

      consoleLogs.push(logEntry);

      if (msg.type() === 'error') {
        consoleErrors.push(logEntry);
      }

      // Print debug logs that match our pattern
      if (text.includes('[EntityDetail]') ||
          text.includes('isArray:') ||
          text.includes('length:')) {
        console.log(`[BROWSER CONSOLE] ${msg.type()}: ${text}`);
      }
    });

    // Clear arrays for each test
    networkRequests = [];
    consoleLogs = [];
    consoleErrors = [];
  });

  test('Debug: jeffrey_epstein entity page - full analysis', async ({ page }) => {
    console.log('\n' + '='.repeat(80));
    console.log('STARTING BROWSER DEBUGGING SESSION');
    console.log('='.repeat(80));

    // Navigate to the page
    console.log('\n1. NAVIGATION');
    console.log('-'.repeat(80));
    const url = 'http://localhost:5173/entities/jeffrey_epstein';
    console.log('Navigating to:', url);

    await page.goto(url);
    console.log('Navigation complete');

    // Wait for page to load
    console.log('\n2. WAITING FOR PAGE LOAD');
    console.log('-'.repeat(80));
    await page.waitForLoadState('networkidle');
    console.log('Network idle reached');

    // Give React time to render
    await page.waitForTimeout(2000);
    console.log('Waited 2s for React rendering');

    // Report network requests
    console.log('\n3. NETWORK REQUESTS ANALYSIS');
    console.log('-'.repeat(80));
    console.log(`Total /api/news requests: ${networkRequests.length}`);

    if (networkRequests.length === 0) {
      console.error('❌ NO API REQUESTS MADE!');
      console.error('Possible causes:');
      console.error('  - useEffect not firing');
      console.error('  - Entity ID missing');
      console.error('  - Component not mounted');
    } else {
      networkRequests.forEach((req, index) => {
        console.log(`\nRequest #${index + 1}:`);
        console.log('  URL:', req.url);
        console.log('  Method:', req.method);
        console.log('  Status:', req.status, req.statusText);
        console.log('  Timestamp:', req.timestamp);

        if (req.headers) {
          console.log('  CORS Headers:');
          console.log('    Access-Control-Allow-Origin:', req.headers['access-control-allow-origin'] || 'MISSING');
          console.log('    Content-Type:', req.headers['content-type'] || 'MISSING');
        }

        if (req.responseBody) {
          console.log('  Response Type:', typeof req.responseBody);
          console.log('  Is Array:', Array.isArray(req.responseBody));

          if (Array.isArray(req.responseBody)) {
            console.log('  ✅ Response is Array (correct format)');
            console.log('  Articles Count:', req.responseBody.length);

            if (req.responseBody.length > 0) {
              console.log('  First Article:', {
                title: req.responseBody[0].title?.substring(0, 50),
                date: req.responseBody[0].date,
                source: req.responseBody[0].source
              });
            }
          } else if (req.responseBody && typeof req.responseBody === 'object') {
            console.log('  ⚠️  Response is Object');
            console.log('  Object Keys:', Object.keys(req.responseBody));

            if (req.responseBody.articles && Array.isArray(req.responseBody.articles)) {
              console.error('  ❌ FOUND THE ISSUE!');
              console.error('  Backend returns: { articles: Array }');
              console.error('  Frontend expects: Array');
              console.error('  Wrapped articles count:', req.responseBody.articles.length);
            }
          }
        }
      });
    }

    // Report console logs
    console.log('\n4. CONSOLE LOGS ANALYSIS');
    console.log('-'.repeat(80));
    console.log(`Total console messages: ${consoleLogs.length}`);
    console.log(`Console errors: ${consoleErrors.length}`);

    // Find the critical debug log
    const newsDebugLog = consoleLogs.find(log =>
      log.text.includes('[EntityDetail] Rendering news cards section:')
    );

    if (newsDebugLog) {
      console.log('\n✅ Found EntityDetail debug log:');
      console.log('  ', newsDebugLog.text);
    } else {
      console.error('\n❌ EntityDetail debug log NOT found!');
      console.error('  Component may not be rendering or console.log was removed');
    }

    // Print all errors
    if (consoleErrors.length > 0) {
      console.log('\n❌ CONSOLE ERRORS:');
      consoleErrors.forEach((err, index) => {
        console.log(`  Error #${index + 1}:`, err.text);
      });
    } else {
      console.log('\n✅ No console errors');
    }

    // Check DOM state
    console.log('\n5. DOM STATE ANALYSIS');
    console.log('-'.repeat(80));

    // Check for news section
    const newsSection = await page.locator('[class*="news"], [data-testid*="news"]').first();
    const newsSectionExists = await newsSection.count() > 0;
    console.log('News section exists:', newsSectionExists);

    // Check for article cards
    const articleCards = await page.locator('[class*="article"], [class*="card"]').count();
    console.log('Article cards rendered:', articleCards);

    // Check for "0 articles" text
    const pageText = await page.textContent('body');
    const hasZeroText = pageText?.includes('0 article') || false;
    console.log('Page shows "0 articles":', hasZeroText);

    if (hasZeroText) {
      // Try to find the exact element
      const zeroElement = await page.locator('text=/0 article/i').first();
      if (await zeroElement.count() > 0) {
        const html = await zeroElement.evaluate(el => el.outerHTML);
        console.log('Element showing "0 articles":', html.substring(0, 200));
      }
    }

    // Manual API test from browser context
    console.log('\n6. MANUAL API TEST (from browser context)');
    console.log('-'.repeat(80));

    const manualTestResult = await page.evaluate(async () => {
      try {
        const entityId = window.location.pathname.split('/').pop();
        const apiUrl = `http://localhost:8081/api/news/articles?entity=${entityId}`;

        const response = await fetch(apiUrl);
        const data = await response.json();

        return {
          success: true,
          status: response.status,
          isArray: Array.isArray(data),
          count: Array.isArray(data) ? data.length : 'N/A',
          hasArticlesKey: data && typeof data === 'object' && 'articles' in data,
          wrappedCount: data?.articles ? data.articles.length : 'N/A',
          dataType: typeof data,
          keys: data && typeof data === 'object' ? Object.keys(data) : []
        };
      } catch (error: any) {
        return {
          success: false,
          error: error.message
        };
      }
    });

    console.log('Manual API Test Result:', JSON.stringify(manualTestResult, null, 2));

    if (manualTestResult.success && manualTestResult.hasArticlesKey) {
      console.error('\n❌❌❌ ROOT CAUSE FOUND! ❌❌❌');
      console.error('Backend returns: { articles: [...] }');
      console.error('Frontend expects: [...]');
      console.error('The response is wrapped in an object!');
    }

    // Screenshot for visual inspection
    console.log('\n7. CAPTURING SCREENSHOT');
    console.log('-'.repeat(80));
    const screenshotPath = './test-results/news-debug-screenshot.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('Screenshot saved:', screenshotPath);

    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('DEBUGGING SUMMARY');
    console.log('='.repeat(80));
    console.log('API Requests Made:', networkRequests.length > 0 ? '✅ YES' : '❌ NO');
    console.log('Console Errors:', consoleErrors.length > 0 ? `❌ ${consoleErrors.length} errors` : '✅ None');
    console.log('News Section Exists:', newsSectionExists ? '✅ YES' : '❌ NO');
    console.log('Article Cards Rendered:', articleCards > 0 ? `✅ ${articleCards}` : '❌ 0');
    console.log('Shows "0 articles":', hasZeroText ? '❌ YES (bug confirmed)' : '✅ NO');

    if (networkRequests.length > 0 && networkRequests[0].responseBody) {
      const resp = networkRequests[0].responseBody;
      console.log('Response Format:', Array.isArray(resp) ? '✅ Array' : '❌ Object');
      console.log('Articles in Response:',
        Array.isArray(resp) ? `✅ ${resp.length}` :
        resp?.articles ? `⚠️  ${resp.articles.length} (wrapped)` : '❌ Unknown');
    }
    console.log('='.repeat(80));

    // Fail the test if we found the wrapping issue
    if (manualTestResult.success && manualTestResult.hasArticlesKey) {
      throw new Error(
        'Response format mismatch: Backend returns { articles: Array } but frontend expects Array directly'
      );
    }

    // Fail if no requests were made
    if (networkRequests.length === 0) {
      throw new Error('No API requests were made to /api/news/articles');
    }

    // Fail if "0 articles" is shown but API returned data
    if (hasZeroText && networkRequests.length > 0) {
      const resp = networkRequests[0].responseBody;
      const actualCount = Array.isArray(resp) ? resp.length : (resp?.articles?.length || 0);
      if (actualCount > 0) {
        throw new Error(`UI shows "0 articles" but API returned ${actualCount} articles`);
      }
    }
  });
});
