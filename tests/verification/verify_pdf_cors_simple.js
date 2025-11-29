#!/usr/bin/env node

/**
 * Simple PDF Viewer CORS Fix Verification using Playwright
 */

const { chromium } = require('playwright');

const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
};

function log(message, color = COLORS.reset) {
  console.log(`${color}${message}${COLORS.reset}`);
}

function header(message) {
  log(`\n${'='.repeat(60)}`, COLORS.cyan);
  log(message, COLORS.cyan);
  log('='.repeat(60), COLORS.cyan);
}

async function main() {
  const results = {
    optionsRequest: null,
    getRequest: null,
    corsErrors: [],
    consoleErrors: [],
    success: false,
  };

  header('PDF Viewer CORS Fix Verification');
  log('Starting browser...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000,
  });

  try {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Track requests
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/download')) {
        log(`[REQUEST] ${request.method()} ${url}`, COLORS.cyan);
      }
    });

    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/download')) {
        const method = response.request().method();
        const status = response.status();
        const color = status === 200 ? COLORS.green : COLORS.red;
        log(`[RESPONSE] ${method} ${url} - ${status}`, color);

        const headers = response.headers();

        if (method === 'OPTIONS') {
          results.optionsRequest = {
            status,
            cors: {
              origin: headers['access-control-allow-origin'],
              methods: headers['access-control-allow-methods'],
              headers: headers['access-control-allow-headers'],
              credentials: headers['access-control-allow-credentials'],
            },
          };
        }

        if (method === 'GET') {
          results.getRequest = {
            status,
            contentType: headers['content-type'],
            cors: {
              origin: headers['access-control-allow-origin'],
              credentials: headers['access-control-allow-credentials'],
            },
          };
        }
      }
    });

    // Track console
    page.on('console', msg => {
      const text = msg.text();
      if (msg.type() === 'error') {
        results.consoleErrors.push(text);
        if (text.toLowerCase().includes('cors') || text.toLowerCase().includes('access-control')) {
          results.corsErrors.push(text);
          log(`[CORS ERROR] ${text}`, COLORS.red);
        }
      }
    });

    // Navigate
    header('Navigating to Documents Page');
    await page.goto('http://localhost:5173/documents');
    await page.waitForSelector('h1');

    const title = await page.locator('h1').first().textContent();
    log(`Page loaded: ${title}`, COLORS.green);

    // Find documents
    header('Finding Documents');
    await page.waitForSelector('table tbody tr');

    const rows = await page.locator('table tbody tr').all();
    log(`Found ${rows.length} documents`);

    // Click first document
    if (rows.length > 0) {
      const firstRow = rows[0];
      const cells = await firstRow.locator('td').all();
      const docTitle = await cells[0].textContent();
      const docType = cells.length > 1 ? await cells[1].textContent() : 'Unknown';

      log(`\nOpening: ${docTitle} (${docType})`, COLORS.cyan);
      await firstRow.click();

      // Wait for viewer
      await page.waitForTimeout(5000);

      // Take screenshot
      await page.screenshot({ path: 'pdf-viewer-test.png' });
      log('Screenshot saved: pdf-viewer-test.png', COLORS.green);
    }

    // Wait a bit more
    await page.waitForTimeout(3000);

    // Print results
    header('Results');

    if (results.optionsRequest) {
      log('\nOPTIONS Request:', COLORS.cyan);
      log(`  Status: ${results.optionsRequest.status}`);
      log('  CORS Headers:');
      Object.entries(results.optionsRequest.cors).forEach(([key, value]) => {
        const color = value ? COLORS.green : COLORS.yellow;
        log(`    ${key}: ${value || 'missing'}`, color);
      });
    } else {
      log('\nOPTIONS Request: Not detected (may be cached)', COLORS.yellow);
    }

    if (results.getRequest) {
      log('\nGET Request:', COLORS.cyan);
      const color = results.getRequest.status === 200 ? COLORS.green : COLORS.red;
      log(`  Status: ${results.getRequest.status}`, color);
      log(`  Content-Type: ${results.getRequest.contentType}`);
      log('  CORS Headers:');
      Object.entries(results.getRequest.cors).forEach(([key, value]) => {
        const color = value ? COLORS.green : COLORS.yellow;
        log(`    ${key}: ${value || 'missing'}`, color);
      });
    } else {
      log('\nGET Request: Not detected', COLORS.red);
    }

    log(`\nConsole Errors: ${results.consoleErrors.length}`);
    log(`CORS Errors: ${results.corsErrors.length}`, results.corsErrors.length === 0 ? COLORS.green : COLORS.red);

    if (results.corsErrors.length > 0) {
      log('\nCORS Error Details:', COLORS.red);
      results.corsErrors.forEach(err => log(`  - ${err}`, COLORS.red));
    }

    // Summary
    header('Summary');
    const success =
      results.getRequest?.status === 200 &&
      results.corsErrors.length === 0 &&
      (!results.optionsRequest || results.optionsRequest.status === 200);

    log(`GET Request: ${results.getRequest?.status === 200 ? '✓' : '✗'}`, results.getRequest?.status === 200 ? COLORS.green : COLORS.red);
    log(`No CORS Errors: ${results.corsErrors.length === 0 ? '✓' : '✗'}`, results.corsErrors.length === 0 ? COLORS.green : COLORS.red);
    log(`OPTIONS (if sent): ${!results.optionsRequest ? '○' : results.optionsRequest.status === 200 ? '✓' : '✗'}`);

    log(`\n${success ? '✓ TEST PASSED' : '✗ TEST FAILED'}`, success ? COLORS.green : COLORS.red);

    // Keep browser open
    log('\nBrowser will stay open. Press Ctrl+C to exit.', COLORS.cyan);
    await new Promise(() => {});

  } catch (error) {
    log(`\nError: ${error.message}`, COLORS.red);
    throw error;
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
