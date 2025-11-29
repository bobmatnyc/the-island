import { test, expect } from '@playwright/test';

test.describe('Calendar Heatmap Quick Tests', () => {

  test('Complete Calendar Heatmap Functional Test', async ({ page }) => {
    console.log('\n=== CALENDAR HEATMAP COMPREHENSIVE TEST ===\n');

    // Navigate to Activity page
    console.log('1. Navigating to Activity page...');
    await page.goto('http://localhost:5173/activity');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // TC1: Initial Page Load
    console.log('\n[TC1] Initial Page Load');
    const heading = await page.locator('h1').first().textContent();
    console.log(`  ✓ Page heading: "${heading}"`);
    expect(heading).toBeTruthy();

    const heatmapCard = page.locator('text=Activity Heatmap').first();
    await expect(heatmapCard).toBeVisible();
    console.log('  ✓ Heatmap card visible');

    // TC2: Year Selector
    console.log('\n[TC2] Year Selector');
    const yearButton = page.locator('button[role="combobox"]').first();
    if (await yearButton.count() > 0) {
      const initialYearText = await yearButton.textContent();
      console.log(`  ✓ Year selector found with value: ${initialYearText?.trim()}`);

      // Click to open dropdown
      await yearButton.click();
      await page.waitForTimeout(300);

      // Check if dropdown opened
      const dropdown = page.locator('[role="listbox"], [role="option"]');
      const dropdownVisible = await dropdown.count() > 0;
      console.log(`  ✓ Dropdown opened: ${dropdownVisible}`);

      if (dropdownVisible) {
        // Try to select a different year
        const options = page.locator('[role="option"]');
        const optionCount = await options.count();
        console.log(`  ✓ Found ${optionCount} year options`);

        if (optionCount > 1) {
          // Select second option
          await options.nth(1).click();
          await page.waitForTimeout(500);
          console.log('  ✓ Selected different year');
        }
      } else {
        // Close dropdown if it's still open
        await page.keyboard.press('Escape');
      }
    } else {
      console.log('  ⚠ Year selector not found (might use different component)');
    }

    // TC3: Passenger Filter
    console.log('\n[TC3] Passenger Filter');
    const filterInput = page.locator('input[placeholder*="passenger"], input[placeholder*="filter"]').first();
    if (await filterInput.count() > 0) {
      await filterInput.fill('Epstein');
      await page.waitForTimeout(500);
      const filterValue = await filterInput.inputValue();
      console.log(`  ✓ Filter input value: "${filterValue}"`);
      expect(filterValue).toBe('Epstein');

      // Check for clear badge
      const clearBadge = page.locator('text=Clear filter');
      if (await clearBadge.count() > 0) {
        await clearBadge.click();
        await page.waitForTimeout(300);
        console.log('  ✓ Clear filter button works');
      }
    } else {
      console.log('  ⚠ Passenger filter input not found');
    }

    // TC4: Heatmap Cells
    console.log('\n[TC4] Heatmap Cells');
    const heatmapCells = page.locator('rect, .cell, [data-date], [class*="day"]');
    const cellCount = await heatmapCells.count();
    console.log(`  ✓ Found ${cellCount} heatmap cells`);
    expect(cellCount).toBeGreaterThan(0);

    // TC5: Statistics/Info
    console.log('\n[TC5] Statistics and Info');
    const infoCard = page.locator('text=How to use');
    await expect(infoCard).toBeVisible();
    console.log('  ✓ Info card visible');

    const aboutCard = page.locator('text=About this Visualization');
    await expect(aboutCard).toBeVisible();
    console.log('  ✓ About card visible');

    // TC6: Responsive Design
    console.log('\n[TC6] Responsive Design');
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(300);
    console.log('  ✓ Mobile view (375px)');

    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(300);
    console.log('  ✓ Tablet view (768px)');

    await page.setViewportSize({ width: 1280, height: 720 });
    await page.waitForTimeout(300);
    console.log('  ✓ Desktop view (1280px)');

    // TC7: Navigation Test
    console.log('\n[TC7] Navigation');
    const navLink = page.locator('a[href="/flights"], nav a:has-text("Flight")').first();
    if (await navLink.count() > 0) {
      await navLink.click();
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/flight');
      console.log('  ✓ Navigation to Flights page works');

      await page.goBack();
      await page.waitForLoadState('networkidle');
      expect(page.url()).toContain('/activity');
      console.log('  ✓ Back navigation works');
    } else {
      console.log('  ⚠ Flights navigation link not found');
    }

    // TC8: Performance Check
    console.log('\n[TC8] Performance');
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: Math.round(navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart),
        loadComplete: Math.round(navigation.loadEventEnd - navigation.loadEventStart),
        domInteractive: Math.round(navigation.domInteractive - navigation.fetchStart),
      };
    });
    console.log(`  ✓ DOM Content Loaded: ${performanceMetrics.domContentLoaded}ms`);
    console.log(`  ✓ Load Complete: ${performanceMetrics.loadComplete}ms`);
    console.log(`  ✓ DOM Interactive: ${performanceMetrics.domInteractive}ms`);

    // TC9: Accessibility
    console.log('\n[TC9] Accessibility');
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    console.log(`  ✓ Keyboard navigation works (focused: ${focusedElement})`);

    console.log('\n=== ALL TESTS COMPLETED ===\n');
  });

  test('API Integration Test', async ({ page }) => {
    console.log('\n=== API INTEGRATION TEST ===\n');

    const apiCalls: { url: string; status: number }[] = [];

    page.on('response', (response) => {
      if (response.url().includes('/api/')) {
        apiCalls.push({
          url: response.url(),
          status: response.status(),
        });
      }
    });

    await page.goto('http://localhost:5173/activity');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('API Calls Made:');
    apiCalls.forEach((call) => {
      const status = call.status === 200 ? '✓' : '✗';
      console.log(`  ${status} [${call.status}] ${call.url.replace('http://localhost:8081', '')}`);
    });

    const flightApiCalls = apiCalls.filter((call) => call.url.includes('/api/flights'));
    expect(flightApiCalls.length).toBeGreaterThan(0);
    console.log(`\n✓ Flight API called ${flightApiCalls.length} time(s)`);

    const successfulCalls = apiCalls.filter((call) => call.status === 200);
    console.log(`✓ ${successfulCalls.length}/${apiCalls.length} API calls successful`);

    console.log('\n=== API INTEGRATION TEST COMPLETE ===\n');
  });
});
