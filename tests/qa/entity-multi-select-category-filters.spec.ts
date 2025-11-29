/**
 * QA Test: Multi-Select Category Filters with Individual Removal
 *
 * Tests the multi-select category filter functionality on the Entities page.
 *
 * Requirements:
 * - Category filters should be multi-select (not single-select)
 * - Clicking multiple category badges should add them to the filter
 * - Filter bar shows all selected categories as removable badges
 * - Each category badge in filter bar can be removed individually
 * - "Clear All" button to remove all filters at once
 * - Entities filtered by ANY of the selected categories (OR logic)
 * - URL parameter supports comma-separated categories
 * - Selected badges in cards show visual indication
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

test.describe('Entity Multi-Select Category Filters', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to entities page
    await page.goto(`${BASE_URL}/entities`);
    await page.waitForLoadState('networkidle');
  });

  test('should support multi-select by clicking multiple category badges', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Find first two different category badges
    const categoryBadges = await page.locator('button[title*="Filter by"]').all();
    expect(categoryBadges.length).toBeGreaterThan(0);

    // Click first category badge
    const firstBadge = categoryBadges[0];
    const firstCategoryText = await firstBadge.textContent();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar appears with first category
    await expect(page.locator('text=Filters:')).toBeVisible();
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    await expect(filterBar).toBeVisible();

    // Verify first category is in filter bar
    const filterBadge1 = filterBar.locator(`button:has-text("${firstCategoryText}")`);
    await expect(filterBadge1).toBeVisible();

    // Click second category badge (different from first)
    if (categoryBadges.length > 1) {
      const secondBadge = categoryBadges[1];
      const secondCategoryText = await secondBadge.textContent();

      if (firstCategoryText !== secondCategoryText) {
        await secondBadge.click();
        await page.waitForLoadState('networkidle');

        // Verify both categories are in filter bar
        const filterBadge2 = filterBar.locator(`button:has-text("${secondCategoryText}")`);
        await expect(filterBadge1).toBeVisible();
        await expect(filterBadge2).toBeVisible();

        // Verify URL has comma-separated categories
        const url = new URL(page.url());
        const categoriesParam = url.searchParams.get('categories');
        expect(categoriesParam).toBeTruthy();
        expect(categoriesParam?.split(',').length).toBeGreaterThanOrEqual(2);
      }
    }
  });

  test('should show selected categories as removable badges in filter bar', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click a category badge
    const firstBadge = page.locator('button[title*="Filter by"]').first();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar is visible
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    await expect(filterBar).toBeVisible();

    // Verify filter badge has X icon for removal
    const removableBadge = filterBar.locator('button').first();
    await expect(removableBadge).toBeVisible();

    // Check for X icon (lucide-react X component)
    const xIcon = removableBadge.locator('svg.lucide-x, svg[class*="lucide"]');
    await expect(xIcon).toBeVisible();
  });

  test('should remove individual category when clicking X on filter badge', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click two different category badges
    const categoryBadges = await page.locator('button[title*="Filter by"]').all();
    if (categoryBadges.length >= 2) {
      const firstCategoryText = await categoryBadges[0].textContent();
      const secondCategoryText = await categoryBadges[1].textContent();

      await categoryBadges[0].click();
      await page.waitForLoadState('networkidle');

      if (firstCategoryText !== secondCategoryText) {
        await categoryBadges[1].click();
        await page.waitForLoadState('networkidle');

        // Get filter bar
        const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');

        // Click X on first filter badge to remove it
        const firstFilterBadge = filterBar.locator(`button:has-text("${firstCategoryText}")`);
        await firstFilterBadge.click();
        await page.waitForLoadState('networkidle');

        // Verify first category removed, second remains
        await expect(firstFilterBadge).not.toBeVisible();
        const secondFilterBadge = filterBar.locator(`button:has-text("${secondCategoryText}")`);
        await expect(secondFilterBadge).toBeVisible();

        // Verify URL updated
        const url = new URL(page.url());
        const categoriesParam = url.searchParams.get('categories');
        expect(categoriesParam).not.toContain(','); // Only one category left
      }
    }
  });

  test('should clear all filters when clicking "Clear All" button', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click a category badge to activate filter
    const firstBadge = page.locator('button[title*="Filter by"]').first();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar is visible
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    await expect(filterBar).toBeVisible();

    // Click "Clear All" button
    const clearAllButton = filterBar.locator('button:has-text("Clear All")');
    await expect(clearAllButton).toBeVisible();
    await clearAllButton.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar is gone
    await expect(filterBar).not.toBeVisible();

    // Verify URL parameter removed
    const url = new URL(page.url());
    const categoriesParam = url.searchParams.get('categories');
    expect(categoriesParam).toBeNull();
  });

  test('should show visual indication on selected category badges in cards', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click first category badge
    const firstBadge = page.locator('button[title*="Filter by"]').first();
    const categoryText = await firstBadge.textContent();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Find the category badge in a card (should have visual indicator)
    const cardBadge = page.locator(`[data-testid="entity-card"] button:has-text("${categoryText}")`).first();
    await expect(cardBadge).toBeVisible();

    // Check for checkmark or visual indicator
    const checkmark = cardBadge.locator('text=✓');
    await expect(checkmark).toBeVisible();

    // Verify badge has different styling (ring/border)
    const badgeClass = await cardBadge.getAttribute('class');
    expect(badgeClass).toContain('ring'); // Should have ring styling when selected
  });

  test('should support URL parameter with comma-separated categories', async ({ page }) => {
    // Navigate with multiple categories in URL
    await page.goto(`${BASE_URL}/entities?categories=frequent_travelers,associates`);
    await page.waitForLoadState('networkidle');

    // Verify filter bar shows both categories
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    await expect(filterBar).toBeVisible();

    // Check for presence of both category badges (approximate text match)
    const badges = await filterBar.locator('button[title*="Remove"]').all();
    expect(badges.length).toBe(2);

    // Verify entities are filtered
    const resultsText = page.locator('text=/Showing.*entities/');
    await expect(resultsText).toBeVisible();
  });

  test('should toggle category off when clicking selected badge again', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click category badge to select it
    const firstBadge = page.locator('button[title*="Filter by"]').first();
    const categoryText = await firstBadge.textContent();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter is active
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    await expect(filterBar).toBeVisible();

    // Click the same badge again in a card (should be in "Remove" state now)
    const selectedBadge = page.locator(`[data-testid="entity-card"] button[title*="Remove ${categoryText}"]`).first();
    await selectedBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar is gone
    await expect(filterBar).not.toBeVisible();

    // Verify URL parameter removed
    const url = new URL(page.url());
    const categoriesParam = url.searchParams.get('categories');
    expect(categoriesParam).toBeNull();
  });

  test('should filter entities by ANY selected category (OR logic)', async ({ page }) => {
    // Navigate with multiple categories
    await page.goto(`${BASE_URL}/entities?categories=frequent_travelers,social_contacts`);
    await page.waitForLoadState('networkidle');

    // Get entity count
    const resultsText = await page.locator('text=/Showing.*of.*entities/').textContent();
    const match = resultsText?.match(/of (\d+)/);
    const totalWithBoth = match ? parseInt(match[1]) : 0;

    // Remove one category
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    const firstBadge = filterBar.locator('button').first();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Get new entity count (should be less or equal)
    const newResultsText = await page.locator('text=/Showing.*of.*entities/').textContent();
    const newMatch = newResultsText?.match(/of (\d+)/);
    const totalWithOne = newMatch ? parseInt(newMatch[1]) : 0;

    // Verify OR logic: entities with both categories >= entities with one category
    expect(totalWithBoth).toBeGreaterThanOrEqual(totalWithOne);
  });

  test('should show entity count in filter bar', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Click category badge
    const firstBadge = page.locator('button[title*="Filter by"]').first();
    await firstBadge.click();
    await page.waitForLoadState('networkidle');

    // Verify filter bar shows count
    const filterBar = page.locator('.bg-primary\\/5.border-primary\\/20');
    const countText = filterBar.locator('text=/\\(\\d+ (entity|entities)\\)/');
    await expect(countText).toBeVisible();
  });
});
