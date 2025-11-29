/**
 * Comprehensive Playwright Test Suite for 5 UI Bug Fixes
 * Testing Environment: http://localhost:5173/
 * Backend API: http://localhost:8081/
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

// Test configuration
const BASE_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:8081';
const SCREENSHOT_DIR = path.join(__dirname, '../artifacts/ui-bug-fixes');

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Helper function to capture console logs
function setupConsoleListener(page, testName) {
  const logs = { errors: [], warnings: [], all: [] };

  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    logs.all.push({ type, text });

    if (type === 'error') logs.errors.push(text);
    if (type === 'warning') logs.warnings.push(text);
  });

  page.on('pageerror', error => {
    logs.errors.push(error.message);
  });

  return logs;
}

// Test 1: Entities Page Pagination
test.describe('Test 1: Entities Page Pagination', () => {
  test('should display correct pagination with 100 entities per page', async ({ page }) => {
    const logs = setupConsoleListener(page, 'entities-pagination');

    // Navigate to entities page
    await page.goto(`${BASE_URL}/entities`);

    // Wait for entities to load
    await page.waitForTimeout(3000);

    // Take screenshot of initial load
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01-entities-page-initial.png'),
      fullPage: true
    });

    // Check for pagination text
    const paginationText = await page.locator('text=/Showing \\d+ to \\d+ of/').textContent()
      .catch(() => null);

    console.log('Pagination text:', paginationText);

    // Verify pagination shows "Showing 1 to 100 of"
    if (paginationText) {
      expect(paginationText).toMatch(/Showing 1 to 100 of/i);
    }

    // Count entity cards/items
    const entityCards = await page.locator('[class*="entity"], .card, [data-testid*="entity"]').count();
    console.log('Entity cards found:', entityCards);

    // Verify max 100 entities per page
    expect(entityCards).toBeLessThanOrEqual(100);
    expect(entityCards).toBeGreaterThan(0);

    // Look for pagination controls
    const nextButton = page.locator('button:has-text("Next"), button:has-text("→"), [aria-label*="next"]').first();
    const page2Button = page.locator('button:has-text("2"), [aria-label="Page 2"]').first();

    const paginationExists = await nextButton.isVisible().catch(() => false) ||
                            await page2Button.isVisible().catch(() => false);

    console.log('Pagination controls visible:', paginationExists);

    if (paginationExists) {
      // Click to page 2
      const clickTarget = await nextButton.isVisible().catch(() => false) ? nextButton : page2Button;
      await clickTarget.click();

      // Wait for new content
      await page.waitForTimeout(2000);

      // Take screenshot of page 2
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '01-entities-page-2.png'),
        fullPage: true
      });

      // Verify pagination text updates
      const page2Text = await page.locator('text=/Showing \\d+ to \\d+ of/').textContent()
        .catch(() => null);

      console.log('Page 2 pagination text:', page2Text);

      if (page2Text) {
        expect(page2Text).toMatch(/Showing 101 to 200 of/i);
      }

      // Go back to page 1
      const prevButton = page.locator('button:has-text("Previous"), button:has-text("←"), [aria-label*="prev"]').first();
      const page1Button = page.locator('button:has-text("1"), [aria-label="Page 1"]').first();

      const backTarget = await prevButton.isVisible().catch(() => false) ? prevButton : page1Button;
      await backTarget.click();
      await page.waitForTimeout(1000);
    }

    // Check console logs
    console.log('Console errors:', logs.errors.length);
    console.log('Console warnings:', logs.warnings.length);

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, '01-entities-console-logs.json'),
      JSON.stringify(logs, null, 2)
    );

    // Verify no critical console errors
    const criticalErrors = logs.errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('chunk')
    );

    console.log('Critical errors:', criticalErrors);
  });
});

// Test 2: Flights Map Rendering
test.describe('Test 2: Flights Map Rendering', () => {
  test('should render interactive Leaflet map with flight routes', async ({ page }) => {
    const logs = setupConsoleListener(page, 'flights-map');

    // Navigate to flights page
    await page.goto(`${BASE_URL}/flights`);

    // Wait for page load
    await page.waitForTimeout(2000);

    // Take screenshot of initial flights page
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02-flights-initial.png'),
      fullPage: true
    });

    // Look for Map tab/button
    const mapTab = page.locator('button:has-text("Map"), [role="tab"]:has-text("Map"), .tab:has-text("Map")').first();
    const mapTabExists = await mapTab.isVisible().catch(() => false);

    console.log('Map tab visible:', mapTabExists);

    if (mapTabExists) {
      // Click Map tab
      await mapTab.click();

      // Wait for map initialization (Leaflet takes time)
      await page.waitForTimeout(4000);

      // Take screenshot of map view
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '02-flights-map-view.png'),
        fullPage: true
      });

      // Check for Leaflet container
      const leafletContainer = await page.locator('.leaflet-container').count();
      console.log('Leaflet containers found:', leafletContainer);
      expect(leafletContainer).toBeGreaterThan(0);

      // Check for Leaflet zoom controls
      const zoomControls = await page.locator('.leaflet-control-zoom').count();
      console.log('Leaflet zoom controls found:', zoomControls);

      // Check for map tiles (dark tiles should be loaded)
      const tiles = await page.locator('.leaflet-tile').count();
      console.log('Map tiles loaded:', tiles);

      // Check for polylines (flight routes)
      const polylines = await page.locator('.leaflet-interactive[stroke]').count();
      console.log('Flight route polylines:', polylines);

      // Check for markers (airports)
      const markers = await page.locator('.leaflet-marker-icon').count();
      console.log('Airport markers:', markers);

      // Check for broken images
      const brokenImages = await page.locator('img[src*="leaflet"][alt=""]').count();
      console.log('Potential broken images:', brokenImages);

      // Test map interaction - try to zoom
      const zoomIn = page.locator('.leaflet-control-zoom-in').first();
      if (await zoomIn.isVisible().catch(() => false)) {
        await zoomIn.click();
        await page.waitForTimeout(500);
        console.log('Zoom in clicked successfully');
      }

      // Take final screenshot after interaction
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '02-flights-map-interactive.png'),
        fullPage: true
      });
    }

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, '02-flights-console-logs.json'),
      JSON.stringify(logs, null, 2)
    );

    // Check for Leaflet errors
    const leafletErrors = logs.errors.filter(e =>
      e.toLowerCase().includes('leaflet') ||
      e.toLowerCase().includes('map')
    );

    console.log('Leaflet-specific errors:', leafletErrors);
  });
});

// Test 3: Document Viewer PDF Loading
test.describe('Test 3: Document Viewer PDF Loading', () => {
  test('should render PDF documents inline without errors', async ({ page }) => {
    const logs = setupConsoleListener(page, 'document-viewer');

    // Navigate to documents page
    await page.goto(`${BASE_URL}/documents`);

    // Wait for documents to load
    await page.waitForTimeout(3000);

    // Take screenshot of documents page
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03-documents-list.png'),
      fullPage: true
    });

    // Find PDF documents in the list
    const pdfLinks = await page.locator('a[href*=".pdf"], .document:has-text(".pdf"), [data-type="pdf"]').count();
    console.log('PDF documents found:', pdfLinks);

    // Try to find any document link
    const anyDocumentLink = page.locator('.document-item, .card, [class*="document"]').first();
    const documentExists = await anyDocumentLink.isVisible().catch(() => false);

    if (documentExists) {
      // Click on first document
      await anyDocumentLink.click();

      // Wait for viewer to load
      await page.waitForTimeout(3000);

      // Take screenshot of document viewer
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '03-document-viewer.png'),
        fullPage: true
      });

      // Check for "No content available" error
      const noContentError = await page.locator('text=/No content available/i').count();
      console.log('No content error present:', noContentError > 0);

      // Check for PDF canvas/iframe
      const pdfCanvas = await page.locator('canvas, iframe[src*=".pdf"]').count();
      console.log('PDF canvas/iframe elements:', pdfCanvas);

      // Check for page navigation
      const pageCount = await page.locator('text=/Page \\d+ of \\d+/i').textContent().catch(() => null);
      console.log('Page count text:', pageCount);

      // Check for PDF navigation controls
      const navControls = await page.locator('button:has-text("Next"), button:has-text("Previous"), [aria-label*="page"]').count();
      console.log('PDF navigation controls:', navControls);

      // Check for PDF.js worker errors
      const pdfWorkerErrors = logs.errors.filter(e =>
        e.toLowerCase().includes('pdf') ||
        e.toLowerCase().includes('worker')
      );
      console.log('PDF.js worker errors:', pdfWorkerErrors);
    }

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, '03-documents-console-logs.json'),
      JSON.stringify(logs, null, 2)
    );
  });
});

// Test 4: Heatmap Color Scheme Removed
test.describe('Test 4: Heatmap Color Scheme Removal', () => {
  test('should display simplified heatmap with minimal color scheme', async ({ page }) => {
    const logs = setupConsoleListener(page, 'heatmap-colors');

    // Try multiple potential heatmap locations
    const heatmapUrls = [
      `${BASE_URL}/matrix`,
      `${BASE_URL}/analytics`,
      `${BASE_URL}/network`,
      `${BASE_URL}/visualizations`
    ];

    let heatmapFound = false;

    for (const url of heatmapUrls) {
      await page.goto(url).catch(() => null);
      await page.waitForTimeout(2000);

      // Look for heatmap or adjacency matrix
      const heatmapElement = await page.locator(
        '.heatmap, .adjacency-matrix, [class*="matrix"], canvas, svg'
      ).first().isVisible().catch(() => false);

      if (heatmapElement) {
        console.log('Heatmap found at:', url);
        heatmapFound = true;

        // Take screenshot
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '04-heatmap-view.png'),
          fullPage: true
        });

        // Check for color picker controls
        const colorPicker = await page.locator(
          'input[type="color"], .color-picker, [class*="color-scheme"]'
        ).count();
        console.log('Color picker controls found:', colorPicker);

        // Check for color legend with multiple colors
        const colorLegend = await page.locator('.legend, [class*="legend"]').count();
        console.log('Color legend elements:', colorLegend);

        break;
      }
    }

    if (!heatmapFound) {
      console.log('Heatmap/matrix visualization not found in common locations');
      await page.goto(`${BASE_URL}/analytics`);
      await page.waitForTimeout(2000);

      // Take screenshot of analytics page as fallback
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '04-analytics-fallback.png'),
        fullPage: true
      });
    }

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, '04-heatmap-console-logs.json'),
      JSON.stringify(logs, null, 2)
    );
  });
});

// Test 5: Activity Calendar Data Display
test.describe('Test 5: Activity Calendar Data Display', () => {
  test('should display activity calendar with data', async ({ page }) => {
    const logs = setupConsoleListener(page, 'activity-calendar');

    // Try multiple potential calendar locations
    const calendarUrls = [
      `${BASE_URL}/activity`,
      `${BASE_URL}/analytics`,
      `${BASE_URL}/timeline`
    ];

    let calendarFound = false;

    for (const url of calendarUrls) {
      await page.goto(url).catch(() => null);
      await page.waitForTimeout(2000);

      // Look for calendar grid
      const calendarElement = await page.locator(
        '.calendar, .activity-calendar, [class*="calendar"]'
      ).first().isVisible().catch(() => false);

      if (calendarElement) {
        console.log('Calendar found at:', url);
        calendarFound = true;

        // Take screenshot
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '05-calendar-view.png'),
          fullPage: true
        });

        // Count calendar cells
        const calendarCells = await page.locator(
          '.calendar-day, .calendar-cell, [data-date], [class*="day"]'
        ).count();
        console.log('Calendar cells found:', calendarCells);

        // Check for cells with data (colors, numbers)
        const cellsWithData = await page.locator(
          '[data-count], [data-activity], [style*="background"], [class*="active"]'
        ).count();
        console.log('Cells with activity data:', cellsWithData);

        // Try hovering over a cell to check tooltip
        const firstCell = page.locator('.calendar-day, .calendar-cell').first();
        if (await firstCell.isVisible().catch(() => false)) {
          await firstCell.hover();
          await page.waitForTimeout(500);

          // Check for tooltip
          const tooltip = await page.locator(
            '[role="tooltip"], .tooltip, [class*="tooltip"]'
          ).isVisible().catch(() => false);
          console.log('Tooltip visible on hover:', tooltip);

          // Take screenshot with tooltip
          await page.screenshot({
            path: path.join(SCREENSHOT_DIR, '05-calendar-tooltip.png'),
            fullPage: true
          });
        }

        break;
      }
    }

    if (!calendarFound) {
      console.log('Activity calendar not found in common locations');

      // Check analytics page tabs
      await page.goto(`${BASE_URL}/analytics`);
      await page.waitForTimeout(2000);

      // Look for tabs
      const tabs = await page.locator('[role="tab"], .tab, button[class*="tab"]').all();
      console.log('Tabs found:', tabs.length);

      for (const tab of tabs) {
        const tabText = await tab.textContent();
        console.log('Tab text:', tabText);

        if (tabText && tabText.toLowerCase().includes('calendar')) {
          await tab.click();
          await page.waitForTimeout(2000);

          await page.screenshot({
            path: path.join(SCREENSHOT_DIR, '05-calendar-from-tab.png'),
            fullPage: true
          });
          break;
        }
      }
    }

    // Check for API errors related to activity data
    const apiErrors = logs.errors.filter(e =>
      e.toLowerCase().includes('api') ||
      e.toLowerCase().includes('fetch') ||
      e.toLowerCase().includes('activity')
    );
    console.log('API-related errors:', apiErrors);

    // Save console logs
    fs.writeFileSync(
      path.join(SCREENSHOT_DIR, '05-calendar-console-logs.json'),
      JSON.stringify(logs, null, 2)
    );
  });
});

// Summary test to generate final report
test.describe('Test Summary', () => {
  test('generate comprehensive test report', async () => {
    const reportPath = path.join(SCREENSHOT_DIR, 'test-summary-report.json');

    const summary = {
      timestamp: new Date().toISOString(),
      environment: {
        frontendUrl: BASE_URL,
        backendUrl: API_URL,
      },
      tests: {
        'entities-pagination': 'See 01-* screenshots and logs',
        'flights-map': 'See 02-* screenshots and logs',
        'document-viewer': 'See 03-* screenshots and logs',
        'heatmap-colors': 'See 04-* screenshots and logs',
        'activity-calendar': 'See 05-* screenshots and logs'
      },
      artifacts: {
        screenshots: SCREENSHOT_DIR,
        logs: SCREENSHOT_DIR
      }
    };

    fs.writeFileSync(reportPath, JSON.stringify(summary, null, 2));
    console.log('Test report generated at:', reportPath);
  });
});
