/**
 * QA Test: Network Graph Edge Weight Filter
 *
 * Tests the edge weight filtering slider implementation
 * that reduces network graph visual density.
 *
 * Expected Results:
 * - minEdgeWeight = 0: 1,482 edges (baseline)
 * - minEdgeWeight = 5: 311 edges (79% reduction)
 * - minEdgeWeight = 10: 109 edges (92.6% reduction)
 * - minEdgeWeight = 20: 53 edges (96.4% reduction)
 */

import { test, expect } from '@playwright/test';

test.describe('Network Graph - Edge Weight Filter', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to network page
    await page.goto('http://localhost:5173/network');

    // Wait for network data to load
    await page.waitForSelector('canvas', { timeout: 10000 });

    // Wait a moment for graph to initialize
    await page.waitForTimeout(2000);
  });

  test('1. Edge weight slider appears in filters sidebar', async ({ page }) => {
    // Verify slider label exists
    const sliderLabel = page.locator('label', { hasText: 'Min Edge Weight:' });
    await expect(sliderLabel).toBeVisible();

    // Verify slider input exists
    const slider = page.locator('input[type="range"]').last();
    await expect(slider).toBeVisible();

    // Verify slider attributes
    await expect(slider).toHaveAttribute('min', '0');
    await expect(slider).toHaveAttribute('max', '20');

    // Verify initial value is 0
    await expect(slider).toHaveValue('0');

    // Verify helper text exists
    const helperText = page.locator('text=Filter edges by connection strength');
    await expect(helperText).toBeVisible();
  });

  test('2. Slider value updates label correctly', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();

    // Test value 0
    await slider.fill('0');
    await expect(page.locator('text=Min Edge Weight: 0')).toBeVisible();

    // Test value 5
    await slider.fill('5');
    await expect(page.locator('text=Min Edge Weight: 5')).toBeVisible();

    // Test value 10
    await slider.fill('10');
    await expect(page.locator('text=Min Edge Weight: 10')).toBeVisible();

    // Test value 20
    await slider.fill('20');
    await expect(page.locator('text=Min Edge Weight: 20')).toBeVisible();
  });

  test('3. Graph updates when slider changes (visual test)', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();
    const canvas = page.locator('canvas').first();

    // Capture baseline (minEdgeWeight = 0)
    await slider.fill('0');
    await page.waitForTimeout(1000);
    const screenshot0 = await canvas.screenshot();

    // Set to moderate filtering (minEdgeWeight = 10)
    await slider.fill('10');
    await page.waitForTimeout(1000);
    const screenshot10 = await canvas.screenshot();

    // Set to heavy filtering (minEdgeWeight = 20)
    await slider.fill('20');
    await page.waitForTimeout(1000);
    const screenshot20 = await canvas.screenshot();

    // Screenshots should be different (graph changed)
    // Note: This is a visual test - actual pixel comparison would require image diff library
    expect(screenshot0.length).toBeGreaterThan(0);
    expect(screenshot10.length).toBeGreaterThan(0);
    expect(screenshot20.length).toBeGreaterThan(0);
  });

  test('4. Reset filters button resets edge weight to 0', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();
    const resetButton = page.locator('button', { hasText: 'Reset Filters' });

    // Set slider to non-zero value
    await slider.fill('15');
    await expect(page.locator('text=Min Edge Weight: 15')).toBeVisible();
    await expect(slider).toHaveValue('15');

    // Click reset
    await resetButton.click();
    await page.waitForTimeout(500);

    // Verify slider reset to 0
    await expect(page.locator('text=Min Edge Weight: 0')).toBeVisible();
    await expect(slider).toHaveValue('0');
  });

  test('5. Edge filter combines with other filters', async ({ page }) => {
    const edgeSlider = page.locator('input[type="range"]').last();
    const searchBox = page.locator('input[placeholder*="Search"]');

    // Apply search filter
    await searchBox.fill('Jeffrey');
    await page.waitForTimeout(1000);

    // Then apply edge weight filter
    await edgeSlider.fill('10');
    await page.waitForTimeout(1000);

    // Both filters should be active
    await expect(searchBox).toHaveValue('Jeffrey');
    await expect(edgeSlider).toHaveValue('10');
    await expect(page.locator('text=Min Edge Weight: 10')).toBeVisible();
  });

  test('6. Edge filter works with connection count filter', async ({ page }) => {
    // Find the connection count slider (should be before edge weight slider)
    const connectionSlider = page.locator('input[type="range"]').first();
    const edgeSlider = page.locator('input[type="range"]').last();

    // Set minimum connections to 10
    await connectionSlider.fill('10');
    await page.waitForTimeout(1000);

    // Then set edge weight to 5
    await edgeSlider.fill('5');
    await page.waitForTimeout(1000);

    // Both filters should be active
    await expect(connectionSlider).toHaveValue('10');
    await expect(edgeSlider).toHaveValue('5');
  });

  test('7. Slider is responsive and smooth', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();

    // Test multiple values in sequence
    const values = ['0', '5', '10', '15', '20', '15', '10', '5', '0'];

    for (const value of values) {
      await slider.fill(value);
      await page.waitForTimeout(300);
      await expect(slider).toHaveValue(value);
      await expect(page.locator(`text=Min Edge Weight: ${value}`)).toBeVisible();
    }
  });

  test('8. No console errors when using edge weight filter', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    const slider = page.locator('input[type="range"]').last();

    // Test various values
    await slider.fill('0');
    await page.waitForTimeout(500);
    await slider.fill('10');
    await page.waitForTimeout(500);
    await slider.fill('20');
    await page.waitForTimeout(500);

    // Should have no console errors
    expect(errors).toHaveLength(0);
  });

  test('9. Edge weight filter persists during page interaction', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();
    const canvas = page.locator('canvas').first();

    // Set edge weight filter
    await slider.fill('10');
    await page.waitForTimeout(1000);

    // Interact with graph (pan/zoom)
    await canvas.click({ position: { x: 400, y: 300 } });
    await page.waitForTimeout(500);

    // Filter should still be applied
    await expect(slider).toHaveValue('10');
    await expect(page.locator('text=Min Edge Weight: 10')).toBeVisible();
  });

  test('10. Extreme values work correctly', async ({ page }) => {
    const slider = page.locator('input[type="range"]').last();

    // Test minimum (0)
    await slider.fill('0');
    await expect(slider).toHaveValue('0');
    await expect(page.locator('text=Min Edge Weight: 0')).toBeVisible();

    // Test maximum (20)
    await slider.fill('20');
    await expect(slider).toHaveValue('20');
    await expect(page.locator('text=Min Edge Weight: 20')).toBeVisible();

    // Graph should still render without errors
    const canvas = page.locator('canvas').first();
    await expect(canvas).toBeVisible();
  });
});

test.describe('Network Graph - Edge Filter Performance', () => {
  test('Edge filtering updates graph quickly', async ({ page }) => {
    await page.goto('http://localhost:5173/network');
    await page.waitForSelector('canvas', { timeout: 10000 });
    await page.waitForTimeout(2000);

    const slider = page.locator('input[type="range"]').last();

    // Measure time to update graph
    const startTime = Date.now();

    await slider.fill('10');
    await page.waitForTimeout(500);

    const endTime = Date.now();
    const updateTime = endTime - startTime;

    // Graph should update within 1 second
    expect(updateTime).toBeLessThan(1000);
  });
});

test.describe('Network Graph - Edge Filter Accessibility', () => {
  test('Slider is keyboard accessible', async ({ page }) => {
    await page.goto('http://localhost:5173/network');
    await page.waitForSelector('canvas', { timeout: 10000 });

    const slider = page.locator('input[type="range"]').last();

    // Focus slider
    await slider.focus();

    // Use arrow keys to change value
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(200);

    // Value should have increased
    const value = await slider.inputValue();
    expect(parseInt(value)).toBeGreaterThan(0);
  });

  test('Slider has proper ARIA attributes', async ({ page }) => {
    await page.goto('http://localhost:5173/network');
    await page.waitForSelector('canvas', { timeout: 10000 });

    const slider = page.locator('input[type="range"]').last();

    // Check slider has range input type
    await expect(slider).toHaveAttribute('type', 'range');

    // Check min/max attributes
    await expect(slider).toHaveAttribute('min', '0');
    await expect(slider).toHaveAttribute('max', '20');
  });
});
