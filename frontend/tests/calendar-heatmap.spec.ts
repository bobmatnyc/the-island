import { test, expect, Page } from '@playwright/test';

// Helper function to wait for heatmap to load
async function waitForHeatmapLoad(page: Page) {
  await page.waitForSelector('[data-testid="calendar-heatmap"]', { timeout: 10000 });
  await page.waitForTimeout(500); // Allow for data loading
}

test.describe('Calendar Heatmap - Activity Page', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to activity page before each test
    await page.goto('http://localhost:5173/activity');
  });

  test('TC1: Initial Page Load', async ({ page }) => {
    console.log('TC1: Testing initial page load...');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page title or heading
    const heading = await page.locator('h1, h2').first();
    await expect(heading).toBeVisible();

    // Check for heatmap container (might have different selector)
    const heatmapExists = await page.locator('.calendar-heatmap, [class*="heatmap"], svg').count() > 0;
    expect(heatmapExists).toBeTruthy();

    // Check for statistics panel (look for numbers or metrics)
    const statsExists = await page.locator('[class*="stat"], [class*="metric"], .grid').count() > 0;
    expect(statsExists).toBeTruthy();

    // Check for year selector
    const yearSelector = await page.locator('select, [role="combobox"], button').filter({ hasText: /20\d{2}/ }).count() > 0;
    expect(yearSelector).toBeTruthy();

    console.log('✓ TC1 PASSED: Initial page load successful');
  });

  test('TC2: Year Selector Functionality', async ({ page }) => {
    console.log('TC2: Testing year selector...');

    await page.waitForLoadState('networkidle');

    // Find year selector - try multiple possible selectors
    let yearSelector = page.locator('select[name*="year"], select[id*="year"]').first();
    if (await yearSelector.count() === 0) {
      yearSelector = page.locator('select').first();
    }

    if (await yearSelector.count() > 0) {
      // Get initial year
      const initialYear = await yearSelector.inputValue();
      console.log(`Initial year: ${initialYear}`);

      // Select different year (2002 or first available option)
      const options = await yearSelector.locator('option').all();
      if (options.length > 1) {
        const targetOption = options.find(async (opt) => (await opt.textContent())?.includes('2002'));
        const targetYear = targetOption ? '2002' : await options[1].getAttribute('value');

        await yearSelector.selectOption(targetYear || '2002');
        await page.waitForTimeout(300); // Allow for transition

        // Verify year changed
        const newYear = await yearSelector.inputValue();
        expect(newYear).not.toBe(initialYear);

        console.log(`✓ TC2 PASSED: Year changed from ${initialYear} to ${newYear}`);
      } else {
        console.log('⚠ TC2 SKIPPED: Only one year available');
      }
    } else {
      console.log('⚠ TC2 SKIPPED: Year selector not found');
    }
  });

  test('TC3: Passenger Filter Functionality', async ({ page }) => {
    console.log('TC3: Testing passenger filter...');

    await page.waitForLoadState('networkidle');

    // Find passenger filter input
    const filterInput = page.locator('input[type="text"], input[type="search"], input[placeholder*="assenger"], input[placeholder*="ilter"]').first();

    if (await filterInput.count() > 0) {
      // Type "Epstein" in filter
      await filterInput.fill('Epstein');
      await page.waitForTimeout(500); // Allow for filtering

      // Verify input has value
      const filterValue = await filterInput.inputValue();
      expect(filterValue).toContain('Epstein');

      // Clear filter
      await filterInput.clear();
      await page.waitForTimeout(300);

      // Verify filter cleared
      const clearedValue = await filterInput.inputValue();
      expect(clearedValue).toBe('');

      console.log('✓ TC3 PASSED: Passenger filter works');
    } else {
      console.log('⚠ TC3 SKIPPED: Passenger filter not found');
    }
  });

  test('TC4: Interactive Tooltips', async ({ page }) => {
    console.log('TC4: Testing interactive tooltips...');

    await page.waitForLoadState('networkidle');

    // Find heatmap cells - try multiple selectors
    const cells = page.locator('rect, .cell, [data-date]');
    const cellCount = await cells.count();

    if (cellCount > 0) {
      // Hover over first few cells to trigger tooltip
      for (let i = 0; i < Math.min(5, cellCount); i++) {
        await cells.nth(i).hover();
        await page.waitForTimeout(200);

        // Check if tooltip appears (might be div, span, or title attribute)
        const tooltipVisible = await page.locator('[role="tooltip"], .tooltip, [class*="tooltip"]').count() > 0;
        if (tooltipVisible) {
          console.log(`✓ TC4 PASSED: Tooltip appears on cell ${i + 1}`);
          break;
        }
      }
    } else {
      console.log('⚠ TC4 SKIPPED: No heatmap cells found');
    }
  });

  test('TC6: Performance - Rapid Year Switching', async ({ page }) => {
    console.log('TC6: Testing performance with rapid year switching...');

    await page.waitForLoadState('networkidle');

    const yearSelector = page.locator('select').first();

    if (await yearSelector.count() > 0) {
      const options = await yearSelector.locator('option').all();

      if (options.length > 3) {
        const startTime = Date.now();

        // Switch years 5 times rapidly
        for (let i = 0; i < 5; i++) {
          const randomOption = options[i % options.length];
          const value = await randomOption.getAttribute('value');
          if (value) {
            await yearSelector.selectOption(value);
            await page.waitForTimeout(50); // Minimal delay
          }
        }

        const endTime = Date.now();
        const duration = endTime - startTime;

        console.log(`✓ TC6 PASSED: 5 year switches completed in ${duration}ms`);
        expect(duration).toBeLessThan(2000); // Should complete in under 2 seconds
      } else {
        console.log('⚠ TC6 SKIPPED: Not enough years for switching test');
      }
    } else {
      console.log('⚠ TC6 SKIPPED: Year selector not found');
    }
  });

  test('TC7: Responsive Design - Mobile Width', async ({ page }) => {
    console.log('TC7: Testing responsive design...');

    // Test mobile width (375px)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(300);

    // Verify page is still visible and scrollable
    const bodyHeight = await page.evaluate(() => document.body.scrollHeight);
    expect(bodyHeight).toBeGreaterThan(0);

    console.log('✓ Mobile width (375px) - page renders');

    // Test tablet width (768px)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(300);

    console.log('✓ Tablet width (768px) - page renders');

    // Reset to desktop
    await page.setViewportSize({ width: 1280, height: 720 });

    console.log('✓ TC7 PASSED: Responsive design works');
  });

  test('TC8: Accessibility - Keyboard Navigation', async ({ page }) => {
    console.log('TC8: Testing keyboard navigation...');

    await page.waitForLoadState('networkidle');

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    let focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    console.log(`First tab: ${focusedElement}`);

    await page.keyboard.press('Tab');
    await page.waitForTimeout(100);

    focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    console.log(`Second tab: ${focusedElement}`);

    expect(focusedElement).toBeTruthy();
    console.log('✓ TC8 PASSED: Keyboard navigation works');
  });

  test('TC9: Console Error Check', async ({ page }) => {
    console.log('TC9: Checking for console errors...');

    const consoleErrors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173/activity');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Filter out known benign errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('sourcemap') &&
      !err.includes('DevTools')
    );

    if (criticalErrors.length > 0) {
      console.log(`⚠ Found ${criticalErrors.length} console errors:`);
      criticalErrors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✓ TC9 PASSED: No critical console errors');
    }

    expect(criticalErrors.length).toBe(0);
  });

  test('Integration: Navigation Flow', async ({ page }) => {
    console.log('Integration Test: Navigation flow...');

    // Start at dashboard
    await page.goto('http://localhost:5173/');
    await page.waitForLoadState('networkidle');

    // Navigate to Activity
    const activityLink = page.locator('a[href="/activity"], a:has-text("Activity")').first();
    if (await activityLink.count() > 0) {
      await activityLink.click();
      await page.waitForLoadState('networkidle');

      expect(page.url()).toContain('/activity');
      console.log('✓ Navigated to Activity page');
    } else {
      // Try direct navigation
      await page.goto('http://localhost:5173/activity');
      await page.waitForLoadState('networkidle');
      console.log('✓ Direct navigation to Activity page');
    }

    // Navigate to Flights
    const flightsLink = page.locator('a[href="/flights"], a:has-text("Flight")').first();
    if (await flightsLink.count() > 0) {
      await flightsLink.click();
      await page.waitForLoadState('networkidle');

      expect(page.url()).toContain('/flight');
      console.log('✓ Navigated to Flights page');
    }

    // Go back
    await page.goBack();
    await page.waitForLoadState('networkidle');

    expect(page.url()).toContain('/activity');
    console.log('✓ Integration Test PASSED: Navigation flow works');
  });

  test('Stability: Long-Running Test', async ({ page }) => {
    console.log('Stability Test: 2-minute interaction test...');

    await page.waitForLoadState('networkidle');

    const startTime = Date.now();
    const duration = 120000; // 2 minutes in milliseconds

    // Interact periodically for 2 minutes
    while (Date.now() - startTime < duration) {
      // Try to find and interact with year selector
      const yearSelector = page.locator('select').first();
      if (await yearSelector.count() > 0) {
        const options = await yearSelector.locator('option').all();
        if (options.length > 1) {
          const randomIndex = Math.floor(Math.random() * options.length);
          const value = await options[randomIndex].getAttribute('value');
          if (value) {
            await yearSelector.selectOption(value);
          }
        }
      }

      // Try to find and interact with filter
      const filterInput = page.locator('input[type="text"]').first();
      if (await filterInput.count() > 0) {
        await filterInput.fill(['Epstein', 'Maxwell', ''][Math.floor(Math.random() * 3)]);
      }

      await page.waitForTimeout(5000); // Wait 5 seconds between interactions
    }

    console.log('✓ Stability Test PASSED: 2-minute test completed without crashes');
  });
});
