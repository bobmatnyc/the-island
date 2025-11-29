/**
 * Chat/Search Page UAT Test
 * Tests the /chat page for UI rendering, search functionality, and error handling
 */

import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:5173';
const SCREENSHOTS_DIR = path.join(__dirname, 'test-screenshots', 'chat-search');

// Ensure screenshots directory exists
if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

async function testChatSearchPage() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500 // Slow down for better observation
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Collect console logs
  const consoleLogs = [];
  const consoleErrors = [];

  page.on('console', msg => {
    const logEntry = `[${msg.type()}] ${msg.text()}`;
    consoleLogs.push(logEntry);
    if (msg.type() === 'error') {
      consoleErrors.push(logEntry);
    }
  });

  // Collect network errors
  const networkErrors = [];
  page.on('requestfailed', request => {
    networkErrors.push(`Failed: ${request.url()} - ${request.failure().errorText}`);
  });

  const results = {
    timestamp: new Date().toISOString(),
    url: `${BASE_URL}/chat`,
    tests: [],
    consoleLogs: [],
    consoleErrors: [],
    networkErrors: [],
    screenshots: []
  };

  try {
    console.log('\n=== TEST 1: Page Load ===');
    await page.goto(`${BASE_URL}/chat`, { waitUntil: 'networkidle', timeout: 10000 });

    // Wait for app to be ready
    await page.waitForTimeout(2000);

    // Screenshot: Initial state
    const initialScreenshot = path.join(SCREENSHOTS_DIR, '01-initial-state.png');
    await page.screenshot({ path: initialScreenshot, fullPage: true });
    results.screenshots.push('01-initial-state.png');
    console.log('✓ Page loaded, screenshot saved');

    results.tests.push({
      name: 'Page Load',
      status: 'PASS',
      notes: 'Page loaded successfully without timeout'
    });

    console.log('\n=== TEST 2: UI Elements - Header and Description ===');

    // Check for "Document Search" header
    const headerExists = await page.locator('h1:has-text("Document Search")').count() > 0;
    console.log(`Header "Document Search": ${headerExists ? '✓ Found' : '✗ Not Found'}`);

    results.tests.push({
      name: 'Document Search Header',
      status: headerExists ? 'PASS' : 'FAIL',
      notes: headerExists ? 'Header displays correctly' : 'Header not found'
    });

    // Check for description
    const descriptionExists = await page.locator('text=Semantic search powered by RAG').count() > 0;
    console.log(`Description: ${descriptionExists ? '✓ Found' : '✗ Not Found'}`);

    results.tests.push({
      name: 'RAG Description',
      status: descriptionExists ? 'PASS' : 'FAIL',
      notes: descriptionExists ? 'Description displays correctly' : 'Description not found'
    });

    console.log('\n=== TEST 3: UI Elements - Empty State ===');

    // Check for empty state with search icon
    const emptyStateIcon = await page.locator('svg.lucide-search, svg.search-icon').count() > 0;
    console.log(`Empty State Icon: ${emptyStateIcon ? '✓ Found' : '✗ Not Found'}`);

    // Check for example queries
    const exampleQueriesText = await page.locator('text=/Try asking about|Example queries|Get started/i').count() > 0;
    console.log(`Example Queries Text: ${exampleQueriesText ? '✓ Found' : '✗ Not Found'}`);

    results.tests.push({
      name: 'Empty State Display',
      status: (emptyStateIcon || exampleQueriesText) ? 'PASS' : 'FAIL',
      notes: 'Empty state with search icon and example queries'
    });

    console.log('\n=== TEST 4: UI Elements - Search Input ===');

    // Find search input
    const searchInput = page.locator('input[type="text"], input[placeholder*="search" i], textarea[placeholder*="search" i]').first();
    const searchInputExists = await searchInput.count() > 0;
    console.log(`Search Input Field: ${searchInputExists ? '✓ Found' : '✗ Not Found'}`);

    // Find send button
    const sendButton = page.locator('button:has-text("Send"), button[type="submit"], button:has(svg.lucide-send)').first();
    const sendButtonExists = await sendButton.count() > 0;
    console.log(`Send Button: ${sendButtonExists ? '✓ Found' : '✗ Not Found'}`);

    results.tests.push({
      name: 'Search Input Elements',
      status: (searchInputExists && sendButtonExists) ? 'PASS' : 'FAIL',
      notes: `Input: ${searchInputExists}, Button: ${sendButtonExists}`
    });

    // Screenshot: Empty state
    const emptyStateScreenshot = path.join(SCREENSHOTS_DIR, '02-empty-state.png');
    await page.screenshot({ path: emptyStateScreenshot, fullPage: true });
    results.screenshots.push('02-empty-state.png');

    console.log('\n=== TEST 5: Navigation Header ===');

    // Check for Search link in navigation
    const navSearch = await page.locator('nav a:has-text("Search"), header a:has-text("Search")').count() > 0;
    console.log(`Navigation "Search" Link: ${navSearch ? '✓ Found' : '✗ Not Found'}`);

    // Check position between Timeline and Flights
    const navLinks = await page.locator('nav a, header a').allTextContents();
    console.log('Navigation Links:', navLinks);

    const timelineIndex = navLinks.findIndex(text => text.includes('Timeline'));
    const searchIndex = navLinks.findIndex(text => text.includes('Search'));
    const flightsIndex = navLinks.findIndex(text => text.includes('Flights'));

    const correctOrder = timelineIndex >= 0 && searchIndex > timelineIndex && flightsIndex > searchIndex;
    console.log(`Navigation Order (Timeline -> Search -> Flights): ${correctOrder ? '✓ Correct' : '✗ Incorrect'}`);

    results.tests.push({
      name: 'Navigation Header',
      status: navSearch ? 'PASS' : 'FAIL',
      notes: `Search link found: ${navSearch}, Correct order: ${correctOrder}`
    });

    console.log('\n=== TEST 6: Search Functionality ===');

    if (!searchInputExists || !sendButtonExists) {
      console.log('✗ Cannot test search - input elements not found');
      results.tests.push({
        name: 'Search Functionality',
        status: 'SKIP',
        notes: 'Search input elements not found'
      });
    } else {
      // Enter search query
      await searchInput.fill('Ghislaine Maxwell');
      console.log('✓ Entered query: "Ghislaine Maxwell"');

      // Screenshot: Query entered
      const queryEnteredScreenshot = path.join(SCREENSHOTS_DIR, '03-query-entered.png');
      await page.screenshot({ path: queryEnteredScreenshot, fullPage: true });
      results.screenshots.push('03-query-entered.png');

      // Click send button
      await sendButton.click();
      console.log('✓ Clicked send button');

      // Wait for loading indicator or results
      await page.waitForTimeout(1000);

      // Screenshot: Loading state
      const loadingScreenshot = path.join(SCREENSHOTS_DIR, '04-loading-state.png');
      await page.screenshot({ path: loadingScreenshot, fullPage: true });
      results.screenshots.push('04-loading-state.png');

      // Check for loading indicator
      const loadingIndicator = await page.locator('[class*="loading"], [class*="spinner"], .animate-spin').count() > 0;
      console.log(`Loading Indicator: ${loadingIndicator ? '✓ Found' : '✗ Not Found'}`);

      results.tests.push({
        name: 'Loading Indicator',
        status: loadingIndicator ? 'PASS' : 'WARN',
        notes: loadingIndicator ? 'Loading indicator displays' : 'No loading indicator detected'
      });

      // Wait for results (up to 10 seconds)
      try {
        await page.waitForSelector('[class*="result"], [class*="document"], [class*="card"]', { timeout: 10000 });
        console.log('✓ Results appeared');
      } catch (e) {
        console.log('⚠ Results did not appear within 10 seconds');
      }

      // Wait a bit more for rendering
      await page.waitForTimeout(2000);

      // Screenshot: Search results
      const resultsScreenshot = path.join(SCREENSHOTS_DIR, '05-search-results.png');
      await page.screenshot({ path: resultsScreenshot, fullPage: true });
      results.screenshots.push('05-search-results.png');

      console.log('\n=== TEST 7: Search Results Display ===');

      // Check for document cards
      const documentCards = await page.locator('[class*="result"], [class*="document-card"], [class*="message"]').count();
      console.log(`Document Cards Found: ${documentCards}`);

      // Check for similarity scores
      const similarityScores = await page.locator('text=/%|similarity|score/i').count();
      console.log(`Similarity Scores: ${similarityScores}`);

      // Check for text excerpts
      const textExcerpts = await page.locator('[class*="excerpt"], [class*="content"], [class*="text"]').count();
      console.log(`Text Excerpts: ${textExcerpts}`);

      // Check for metadata
      const metadata = await page.locator('text=/doc|filename|source|date|size/i').count();
      console.log(`Metadata Elements: ${metadata}`);

      // Check for entity badges
      const entityBadges = await page.locator('[class*="badge"], [class*="tag"], [class*="chip"]').count();
      console.log(`Entity Badges: ${entityBadges}`);

      results.tests.push({
        name: 'Search Results Display',
        status: documentCards > 0 ? 'PASS' : 'FAIL',
        notes: `Cards: ${documentCards}, Scores: ${similarityScores}, Excerpts: ${textExcerpts}, Metadata: ${metadata}, Badges: ${entityBadges}`
      });

      console.log('\n=== TEST 8: Color Coding ===');

      // Check for color-coded results (green, yellow, blue based on similarity)
      const coloredElements = await page.locator('[class*="green"], [class*="yellow"], [class*="blue"], [style*="green"], [style*="yellow"], [style*="blue"]').count();
      console.log(`Color-Coded Elements: ${coloredElements}`);

      results.tests.push({
        name: 'Color Coding',
        status: coloredElements > 0 ? 'PASS' : 'WARN',
        notes: `${coloredElements} color-coded elements found`
      });

      console.log('\n=== TEST 9: Auto-Scrolling ===');

      // Check if page scrolled to show results
      const scrollPosition = await page.evaluate(() => window.scrollY);
      console.log(`Scroll Position: ${scrollPosition}px`);

      results.tests.push({
        name: 'Auto-Scrolling',
        status: scrollPosition > 0 ? 'PASS' : 'WARN',
        notes: `Page scrolled ${scrollPosition}px`
      });
    }

    console.log('\n=== TEST 10: Console Errors ===');
    console.log(`Total Console Logs: ${consoleLogs.length}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\nConsole Errors:');
      consoleErrors.forEach(err => console.log(`  ${err}`));
    }

    if (networkErrors.length > 0) {
      console.log('\nNetwork Errors:');
      networkErrors.forEach(err => console.log(`  ${err}`));
    }

    results.tests.push({
      name: 'Console Errors Check',
      status: consoleErrors.length === 0 ? 'PASS' : 'FAIL',
      notes: `${consoleErrors.length} console errors, ${networkErrors.length} network errors`
    });

    // Store logs
    results.consoleLogs = consoleLogs;
    results.consoleErrors = consoleErrors;
    results.networkErrors = networkErrors;

  } catch (error) {
    console.error('\n✗ Test execution failed:', error);
    results.tests.push({
      name: 'Test Execution',
      status: 'ERROR',
      notes: error.message
    });

    // Screenshot: Error state
    const errorScreenshot = path.join(SCREENSHOTS_DIR, '99-error-state.png');
    try {
      await page.screenshot({ path: errorScreenshot, fullPage: true });
      results.screenshots.push('99-error-state.png');
    } catch (screenshotError) {
      console.error('Failed to capture error screenshot:', screenshotError);
    }
  } finally {
    await browser.close();
  }

  // Write results to JSON
  const resultsPath = path.join(SCREENSHOTS_DIR, 'test-results.json');
  fs.writeFileSync(resultsPath, JSON.stringify(results, null, 2));
  console.log(`\n✓ Results saved to: ${resultsPath}`);

  // Generate summary report
  generateSummaryReport(results);

  return results;
}

function generateSummaryReport(results) {
  console.log('\n' + '='.repeat(80));
  console.log('CHAT/SEARCH PAGE UAT TEST SUMMARY');
  console.log('='.repeat(80));

  const passed = results.tests.filter(t => t.status === 'PASS').length;
  const failed = results.tests.filter(t => t.status === 'FAIL').length;
  const warnings = results.tests.filter(t => t.status === 'WARN').length;
  const skipped = results.tests.filter(t => t.status === 'SKIP').length;
  const errors = results.tests.filter(t => t.status === 'ERROR').length;

  console.log(`\nTest Results: ${results.tests.length} total tests`);
  console.log(`  ✓ PASS: ${passed}`);
  console.log(`  ✗ FAIL: ${failed}`);
  console.log(`  ⚠ WARN: ${warnings}`);
  console.log(`  ○ SKIP: ${skipped}`);
  console.log(`  ✗ ERROR: ${errors}`);

  console.log('\nDetailed Results:');
  results.tests.forEach((test, i) => {
    const icon = test.status === 'PASS' ? '✓' : test.status === 'FAIL' ? '✗' : test.status === 'WARN' ? '⚠' : '○';
    console.log(`  ${i + 1}. [${icon} ${test.status}] ${test.name}`);
    if (test.notes) {
      console.log(`     ${test.notes}`);
    }
  });

  console.log(`\nScreenshots: ${results.screenshots.length} captured`);
  results.screenshots.forEach(screenshot => {
    console.log(`  - ${screenshot}`);
  });

  console.log(`\nConsole Output:`);
  console.log(`  - Total logs: ${results.consoleLogs.length}`);
  console.log(`  - Errors: ${results.consoleErrors.length}`);
  console.log(`  - Network errors: ${results.networkErrors.length}`);

  if (results.consoleErrors.length > 0) {
    console.log('\n⚠ CONSOLE ERRORS DETECTED:');
    results.consoleErrors.slice(0, 10).forEach(err => {
      console.log(`  ${err}`);
    });
    if (results.consoleErrors.length > 10) {
      console.log(`  ... and ${results.consoleErrors.length - 10} more`);
    }
  }

  console.log('\n' + '='.repeat(80));

  // Overall status
  const overallStatus = errors > 0 ? 'ERROR' : failed > 0 ? 'FAILED' : warnings > 0 ? 'PASSED WITH WARNINGS' : 'PASSED';
  console.log(`\nOVERALL STATUS: ${overallStatus}`);
  console.log('='.repeat(80) + '\n');
}

// Run the test
testChatSearchPage()
  .then(() => {
    console.log('Test execution complete');
    process.exit(0);
  })
  .catch(error => {
    console.error('Test failed:', error);
    process.exit(1);
  });
