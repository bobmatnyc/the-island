import { test, expect } from '@playwright/test';

test.describe('PDF Viewer CORS Fix Verification', () => {
  test('should load PDF document with correct CORS headers', async ({ page }) => {
    // Track network requests
    const networkRequests = {
      options: null as any,
      get: null as any,
    };

    // Listen to network activity
    page.on('request', request => {
      const url = request.url();
      if (url.includes('/download')) {
        console.log(`[REQUEST] ${request.method()} ${url}`);
      }
    });

    page.on('response', async response => {
      const url = response.url();
      if (url.includes('/download')) {
        const method = response.request().method();
        console.log(`[RESPONSE] ${method} ${url} - Status: ${response.status()}`);

        // Capture OPTIONS request
        if (method === 'OPTIONS') {
          networkRequests.options = {
            status: response.status(),
            headers: await response.allHeaders(),
          };
          console.log('[OPTIONS HEADERS]', JSON.stringify(networkRequests.options.headers, null, 2));
        }

        // Capture GET request
        if (method === 'GET') {
          networkRequests.get = {
            status: response.status(),
            headers: await response.allHeaders(),
            contentType: response.headers()['content-type'],
          };
          console.log('[GET HEADERS]', JSON.stringify(networkRequests.get.headers, null, 2));
        }
      }
    });

    // Track console messages (for errors)
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log('[CONSOLE ERROR]', msg.text());
      }
    });

    // Navigate to documents page
    console.log('\n=== Navigating to Documents Page ===');
    await page.goto('http://localhost:5173/documents', { waitUntil: 'networkidle' });

    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 10000 });
    const title = await page.locator('h1').first().textContent();
    console.log(`Page title: ${title}`);

    // Look for document items in the table
    console.log('\n=== Finding Documents ===');
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    // Get all document rows
    const rows = await page.locator('table tbody tr').all();
    console.log(`Found ${rows.length} documents`);

    // Find a small PDF (preferably < 50MB)
    let selectedRow = null;
    let selectedDoc = null;

    for (let i = 0; i < Math.min(rows.length, 20); i++) {
      const row = rows[i];
      const cells = await row.locator('td').all();

      if (cells.length >= 3) {
        const titleCell = await cells[0].textContent();
        const typeCell = await cells[1].textContent();
        const sizeCell = cells.length > 2 ? await cells[2].textContent() : null;

        // Look for PDF documents
        if (typeCell?.includes('PDF')) {
          console.log(`Document ${i + 1}: ${titleCell} - ${typeCell} - ${sizeCell}`);

          // Skip if too large
          if (sizeCell && (sizeCell.includes('MB') || sizeCell.includes('GB'))) {
            const sizeMB = parseFloat(sizeCell);
            if (sizeMB > 50) {
              console.log(`  -> Skipping (too large: ${sizeMB}MB)`);
              continue;
            }
          }

          selectedRow = row;
          selectedDoc = {
            title: titleCell,
            type: typeCell,
            size: sizeCell,
          };
          console.log(`  -> Selected this document`);
          break;
        }
      }
    }

    if (!selectedRow || !selectedDoc) {
      console.log('No suitable PDF document found. Checking first available document...');
      selectedRow = rows[0];
      const cells = await selectedRow.locator('td').all();
      selectedDoc = {
        title: await cells[0].textContent(),
        type: await cells[1].textContent(),
        size: cells.length > 2 ? await cells[2].textContent() : 'unknown',
      };
    }

    console.log(`\n=== Testing Document: ${selectedDoc.title} ===`);

    // Click on the document to open viewer
    console.log('Clicking document to open viewer...');
    await selectedRow.click();

    // Wait for viewer modal/page to appear
    console.log('Waiting for PDF viewer to load...');
    await page.waitForTimeout(2000); // Give time for viewer to initialize

    // Check for PDF viewer elements
    const hasEnhancedViewer = await page.locator('.pdf-viewer, #pdf-viewer, [class*="DocumentViewer"]').count() > 0;
    const hasIframeViewer = await page.locator('iframe[src*="/download"]').count() > 0;
    const hasPdfCanvas = await page.locator('canvas[class*="pdf"]').count() > 0;

    console.log('\n=== Viewer Detection ===');
    console.log(`Enhanced viewer: ${hasEnhancedViewer}`);
    console.log(`Iframe viewer: ${hasIframeViewer}`);
    console.log(`PDF canvas: ${hasPdfCanvas}`);

    // Wait a bit more for network requests to complete
    await page.waitForTimeout(3000);

    // Check for CORS errors
    const corsErrors = consoleErrors.filter(err =>
      err.toLowerCase().includes('cors') ||
      err.toLowerCase().includes('access-control')
    );

    // Check for PDF.js errors
    const pdfErrors = consoleErrors.filter(err =>
      err.toLowerCase().includes('pdf') ||
      err.toLowerCase().includes('worker')
    );

    console.log('\n=== Network Request Results ===');
    if (networkRequests.options) {
      console.log('OPTIONS Request:');
      console.log(`  Status: ${networkRequests.options.status}`);
      console.log(`  CORS Headers:`);
      console.log(`    Access-Control-Allow-Origin: ${networkRequests.options.headers['access-control-allow-origin'] || 'MISSING'}`);
      console.log(`    Access-Control-Allow-Methods: ${networkRequests.options.headers['access-control-allow-methods'] || 'MISSING'}`);
      console.log(`    Access-Control-Allow-Headers: ${networkRequests.options.headers['access-control-allow-headers'] || 'MISSING'}`);
      console.log(`    Access-Control-Allow-Credentials: ${networkRequests.options.headers['access-control-allow-credentials'] || 'MISSING'}`);
    } else {
      console.log('OPTIONS Request: NOT DETECTED (may not be needed if same-origin or cached)');
    }

    if (networkRequests.get) {
      console.log('\nGET Request:');
      console.log(`  Status: ${networkRequests.get.status}`);
      console.log(`  Content-Type: ${networkRequests.get.contentType || 'MISSING'}`);
      console.log(`  CORS Headers:`);
      console.log(`    Access-Control-Allow-Origin: ${networkRequests.get.headers['access-control-allow-origin'] || 'MISSING'}`);
      console.log(`    Access-Control-Allow-Credentials: ${networkRequests.get.headers['access-control-allow-credentials'] || 'MISSING'}`);
    } else {
      console.log('\nGET Request: NOT DETECTED');
    }

    console.log('\n=== Console Errors ===');
    console.log(`Total errors: ${consoleErrors.length}`);
    console.log(`CORS errors: ${corsErrors.length}`);
    console.log(`PDF errors: ${pdfErrors.length}`);

    if (corsErrors.length > 0) {
      console.log('\nCORS Errors:');
      corsErrors.forEach(err => console.log(`  - ${err}`));
    }

    if (pdfErrors.length > 0) {
      console.log('\nPDF Errors:');
      pdfErrors.forEach(err => console.log(`  - ${err}`));
    }

    console.log('\n=== Test Results Summary ===');
    console.log(`✓ Document selected: ${selectedDoc.title}`);
    console.log(`✓ Viewer type: ${hasEnhancedViewer ? 'Enhanced' : hasIframeViewer ? 'Iframe' : 'Unknown'}`);
    console.log(`${networkRequests.options ? '✓' : '○'} OPTIONS request: ${networkRequests.options?.status || 'N/A'}`);
    console.log(`${networkRequests.get?.status === 200 ? '✓' : '✗'} GET request: ${networkRequests.get?.status || 'FAILED'}`);
    console.log(`${corsErrors.length === 0 ? '✓' : '✗'} No CORS errors: ${corsErrors.length === 0}`);
    console.log(`${pdfErrors.length === 0 ? '✓' : '○'} No PDF errors: ${pdfErrors.length === 0}`);

    // Assertions
    expect(networkRequests.get).not.toBeNull();
    expect(networkRequests.get.status).toBe(200);
    expect(corsErrors.length).toBe(0);

    // If OPTIONS request was made, verify it succeeded
    if (networkRequests.options) {
      expect(networkRequests.options.status).toBe(200);
      expect(networkRequests.options.headers['access-control-allow-origin']).toBeTruthy();
    }
  });
});
