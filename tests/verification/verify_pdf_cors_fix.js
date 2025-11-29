#!/usr/bin/env node

/**
 * PDF Viewer CORS Fix Verification Script
 *
 * This script tests the PDF document viewer to verify:
 * 1. OPTIONS preflight requests return 200 OK with CORS headers
 * 2. GET requests to /download endpoint succeed
 * 3. PDF loads without CORS errors
 * 4. Browser console has no CORS-related errors
 */

const puppeteer = require('puppeteer');

const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
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

async function verifyPdfViewer() {
  let browser = null;
  const results = {
    documentSelected: false,
    optionsRequest: null,
    getRequest: null,
    corsErrors: [],
    pdfErrors: [],
    consoleErrors: [],
    viewerType: 'unknown',
    success: false,
  };

  try {
    // Launch browser
    header('Launching Browser');
    browser = await puppeteer.launch({
      headless: false, // Show browser for manual verification
      defaultViewport: { width: 1280, height: 720 },
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();

    // Track network requests
    const networkRequests = new Map();

    page.on('request', request => {
      const url = request.url();
      if (url.includes('/download')) {
        const method = request.method();
        log(`[REQUEST] ${method} ${url}`, COLORS.blue);
      }
    });

    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/download')) {
        const method = response.request().method();
        const status = response.status();
        log(`[RESPONSE] ${method} ${url} - Status: ${status}`, status === 200 ? COLORS.green : COLORS.red);

        // Store request details
        const headers = response.headers();

        if (method === 'OPTIONS') {
          results.optionsRequest = {
            status,
            headers: {
              'access-control-allow-origin': headers['access-control-allow-origin'],
              'access-control-allow-methods': headers['access-control-allow-methods'],
              'access-control-allow-headers': headers['access-control-allow-headers'],
              'access-control-allow-credentials': headers['access-control-allow-credentials'],
            },
          };
        }

        if (method === 'GET') {
          results.getRequest = {
            status,
            contentType: headers['content-type'],
            headers: {
              'access-control-allow-origin': headers['access-control-allow-origin'],
              'access-control-allow-credentials': headers['access-control-allow-credentials'],
            },
          };
        }

        networkRequests.set(`${method}:${url}`, { status, headers });
      }
    });

    // Track console messages
    page.on('console', msg => {
      const text = msg.text();
      const type = msg.type();

      if (type === 'error') {
        results.consoleErrors.push(text);

        // Categorize errors
        if (text.toLowerCase().includes('cors') || text.toLowerCase().includes('access-control')) {
          results.corsErrors.push(text);
          log(`[CORS ERROR] ${text}`, COLORS.red);
        } else if (text.toLowerCase().includes('pdf')) {
          results.pdfErrors.push(text);
          log(`[PDF ERROR] ${text}`, COLORS.yellow);
        }
      }
    });

    // Navigate to documents page
    header('Navigating to Documents Page');
    log('URL: http://localhost:5173/documents');
    await page.goto('http://localhost:5173/documents', {
      waitUntil: 'networkidle0',
      timeout: 30000,
    });

    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 10000 });
    const title = await page.$eval('h1', el => el.textContent);
    log(`Page Title: ${title}`, COLORS.green);

    // Find documents
    header('Finding PDF Documents');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    const documents = await page.$$eval('table tbody tr', rows => {
      return rows.slice(0, 20).map((row, index) => {
        const cells = Array.from(row.querySelectorAll('td'));
        return {
          index,
          title: cells[0]?.textContent?.trim() || '',
          type: cells[1]?.textContent?.trim() || '',
          size: cells[2]?.textContent?.trim() || '',
        };
      });
    });

    log(`Found ${documents.length} documents`);

    // Find a suitable PDF
    let selectedDoc = null;
    for (const doc of documents) {
      if (doc.type.includes('PDF')) {
        log(`  ${doc.index + 1}. ${doc.title} - ${doc.type} - ${doc.size}`);

        // Skip large files
        if (doc.size.includes('MB')) {
          const sizeMB = parseFloat(doc.size);
          if (sizeMB > 50) {
            log('    -> Skipping (too large)', COLORS.yellow);
            continue;
          }
        }

        selectedDoc = doc;
        log('    -> Selected', COLORS.green);
        break;
      }
    }

    if (!selectedDoc) {
      selectedDoc = documents[0];
      log('No PDF found, using first document', COLORS.yellow);
    }

    results.documentSelected = true;

    // Click document to open viewer
    header(`Opening Document: ${selectedDoc.title}`);
    const rows = await page.$$('table tbody tr');
    if (rows[selectedDoc.index]) {
      await rows[selectedDoc.index].click();
      log('Document clicked', COLORS.green);
    }

    // Wait for viewer to load
    log('Waiting for PDF viewer...');
    await page.waitForTimeout(3000);

    // Detect viewer type
    const hasEnhancedViewer = await page.$('.pdf-viewer, #pdf-viewer, [class*="DocumentViewer"]') !== null;
    const hasIframeViewer = await page.$('iframe[src*="/download"]') !== null;
    const hasPdfCanvas = await page.$('canvas[class*="pdf"]') !== null;

    if (hasEnhancedViewer) {
      results.viewerType = 'enhanced';
    } else if (hasIframeViewer) {
      results.viewerType = 'iframe';
    } else if (hasPdfCanvas) {
      results.viewerType = 'canvas';
    }

    log(`Viewer Type: ${results.viewerType}`, COLORS.cyan);

    // Wait a bit more for network requests
    await page.waitForTimeout(5000);

    // Take screenshot
    await page.screenshot({ path: '/Users/masa/Projects/epstein/pdf-viewer-verification.png' });
    log('Screenshot saved: pdf-viewer-verification.png', COLORS.green);

    // Print results
    header('Network Request Results');

    if (results.optionsRequest) {
      log('\nOPTIONS Request:', COLORS.cyan);
      log(`  Status: ${results.optionsRequest.status}`);
      log(`  CORS Headers:`);
      Object.entries(results.optionsRequest.headers).forEach(([key, value]) => {
        const status = value ? COLORS.green : COLORS.red;
        log(`    ${key}: ${value || 'MISSING'}`, status);
      });
    } else {
      log('\nOPTIONS Request: NOT DETECTED', COLORS.yellow);
      log('  (May not be needed if same-origin or cached)', COLORS.yellow);
    }

    if (results.getRequest) {
      log('\nGET Request:', COLORS.cyan);
      const statusColor = results.getRequest.status === 200 ? COLORS.green : COLORS.red;
      log(`  Status: ${results.getRequest.status}`, statusColor);
      log(`  Content-Type: ${results.getRequest.contentType}`);
      log(`  CORS Headers:`);
      Object.entries(results.getRequest.headers).forEach(([key, value]) => {
        const status = value ? COLORS.green : COLORS.yellow;
        log(`    ${key}: ${value || 'MISSING'}`, status);
      });
    } else {
      log('\nGET Request: NOT DETECTED', COLORS.red);
    }

    header('Console Errors Analysis');
    log(`Total Console Errors: ${results.consoleErrors.length}`);
    log(`CORS Errors: ${results.corsErrors.length}`, results.corsErrors.length === 0 ? COLORS.green : COLORS.red);
    log(`PDF Errors: ${results.pdfErrors.length}`, results.pdfErrors.length === 0 ? COLORS.green : COLORS.yellow);

    if (results.corsErrors.length > 0) {
      log('\nCORS Errors:', COLORS.red);
      results.corsErrors.forEach(err => log(`  - ${err}`, COLORS.red));
    }

    if (results.pdfErrors.length > 0) {
      log('\nPDF Errors:', COLORS.yellow);
      results.pdfErrors.forEach(err => log(`  - ${err}`, COLORS.yellow));
    }

    // Determine success
    results.success =
      results.documentSelected &&
      results.getRequest?.status === 200 &&
      results.corsErrors.length === 0 &&
      (results.optionsRequest?.status === 200 || !results.optionsRequest);

    header('Test Results Summary');
    log(`${results.documentSelected ? '✓' : '✗'} Document selected: ${selectedDoc.title}`);
    log(`${results.viewerType !== 'unknown' ? '✓' : '✗'} Viewer type: ${results.viewerType}`);
    log(`${results.optionsRequest ? (results.optionsRequest.status === 200 ? '✓' : '✗') : '○'} OPTIONS request: ${results.optionsRequest?.status || 'N/A'}`);
    log(`${results.getRequest?.status === 200 ? '✓' : '✗'} GET request: ${results.getRequest?.status || 'FAILED'}`, results.getRequest?.status === 200 ? COLORS.green : COLORS.red);
    log(`${results.corsErrors.length === 0 ? '✓' : '✗'} No CORS errors`, results.corsErrors.length === 0 ? COLORS.green : COLORS.red);
    log(`${results.pdfErrors.length === 0 ? '✓' : '○'} No PDF errors`, results.pdfErrors.length === 0 ? COLORS.green : COLORS.yellow);

    header('Overall Result');
    if (results.success) {
      log('✓ PDF VIEWER CORS FIX VERIFIED SUCCESSFULLY', COLORS.green);
    } else {
      log('✗ PDF VIEWER CORS FIX VERIFICATION FAILED', COLORS.red);
    }

    // Keep browser open for manual verification
    log('\nBrowser will remain open for manual verification.', COLORS.cyan);
    log('Press Ctrl+C to close and exit.', COLORS.cyan);

    // Wait indefinitely
    await new Promise(() => {});

  } catch (error) {
    log(`\nError: ${error.message}`, COLORS.red);
    console.error(error);
    results.success = false;
  }

  return results;
}

// Run verification
verifyPdfViewer().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
