/**
 * QA Test Specification: Entity Category Badge Filtering
 *
 * Feature: Clickable category badges that filter the entity grid
 *
 * Test Scenarios:
 * 1. Category badge click in grid view filters entities
 * 2. Category badge click in tooltip navigates to filtered view
 * 3. Category badge click in detail page navigates to filtered view
 * 4. URL parameter persists category filter
 * 5. Filter indicator displays active category
 * 6. Clear filter button resets view
 * 7. Category filter works with other filters (type, search, bio)
 * 8. Navigation to entities page from other pages preserves filter
 */

import { test, expect } from '@playwright/test';

test.describe('Entity Category Badge Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/entities');
    await page.waitForLoadState('networkidle');
  });

  test('should display category badges on entities with biographies', async ({ page }) => {
    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]', { timeout: 10000 });

    // Check if any category badges are visible
    const categoryBadges = page.locator('.cursor-pointer[title*="Click to filter"]');
    const count = await categoryBadges.count();

    // Should have at least some entities with category badges
    expect(count).toBeGreaterThan(0);
  });

  test('should filter entities when category badge is clicked', async ({ page }) => {
    // Find first entity with category badge
    const firstCategoryBadge = page.locator('.cursor-pointer').filter({
      hasText: /Victims|Associates|Co-Conspirators|Frequent Travelers|Social Contacts|Legal Professionals|Business Associates|Political Figures|Staff\/Employees/
    }).first();

    // Get the category label before clicking
    const categoryLabel = await firstCategoryBadge.textContent();

    if (!categoryLabel) {
      test.skip();
      return;
    }

    // Click the badge
    await firstCategoryBadge.click();

    // Wait for filter to apply
    await page.waitForTimeout(500);

    // Check that filter indicator is visible
    const filterIndicator = page.locator('text=Filtered by category:');
    await expect(filterIndicator).toBeVisible();

    // Check that URL has category parameter
    const url = new URL(page.url());
    expect(url.searchParams.has('category')).toBeTruthy();

    // Check that filtered badge matches clicked badge
    const displayedCategory = page.locator('.bg-primary\\/5 .font-medium').filter({
      hasText: categoryLabel
    });
    await expect(displayedCategory).toBeVisible();
  });

  test('should clear filter when clear button is clicked', async ({ page }) => {
    // Navigate directly to filtered view
    await page.goto('http://localhost:5173/entities?category=victims');
    await page.waitForLoadState('networkidle');

    // Verify filter is active
    await expect(page.locator('text=Filtered by category:')).toBeVisible();

    // Click clear filter button
    await page.locator('button:has-text("Clear Filter")').click();

    // Wait for filter to clear
    await page.waitForTimeout(500);

    // Check that filter indicator is gone
    await expect(page.locator('text=Filtered by category:')).not.toBeVisible();

    // Check that URL no longer has category parameter
    const url = new URL(page.url());
    expect(url.searchParams.has('category')).toBeFalsy();
  });

  test('should preserve category filter in URL for sharing', async ({ page }) => {
    // Navigate directly to filtered view
    await page.goto('http://localhost:5173/entities?category=associates');
    await page.waitForLoadState('networkidle');

    // Verify filter is applied
    await expect(page.locator('text=Filtered by category:')).toBeVisible();

    // Get the URL
    const url = page.url();
    expect(url).toContain('category=associates');

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Filter should still be active
    await expect(page.locator('text=Filtered by category:')).toBeVisible();
  });

  test('should work with biography filter', async ({ page }) => {
    // Enable biography filter
    await page.locator('button:has-text("With Biography")').click();
    await page.waitForTimeout(500);

    // Find and click a category badge
    const categoryBadge = page.locator('.cursor-pointer').filter({
      hasText: /Victims|Associates/
    }).first();

    if ((await categoryBadge.count()) > 0) {
      await categoryBadge.click();
      await page.waitForTimeout(500);

      // Check both filters are active
      const url = new URL(page.url());
      expect(url.searchParams.get('bio')).toBe('true');
      expect(url.searchParams.has('category')).toBeTruthy();

      // Filter indicator should be visible
      await expect(page.locator('text=Filtered by category:')).toBeVisible();
    }
  });

  test('should navigate from entity detail page to filtered grid', async ({ page }) => {
    // Go to an entity detail page (using a known entity)
    await page.goto('http://localhost:5173/entities');
    await page.waitForLoadState('networkidle');

    // Click on first entity with a category badge
    const entityLink = page.locator('[data-testid="entity-card"]').first();
    await entityLink.click();
    await page.waitForLoadState('networkidle');

    // Find and click category badge in bio view
    const categoryBadge = page.locator('.cursor-pointer').filter({
      hasText: /Victims|Associates|Co-Conspirators/
    }).first();

    if ((await categoryBadge.count()) > 0) {
      await categoryBadge.click();
      await page.waitForLoadState('networkidle');

      // Should be on entities page with filter
      expect(page.url()).toContain('/entities?category=');

      // Filter indicator should be visible
      await expect(page.locator('text=Filtered by category:')).toBeVisible();
    }
  });

  test('should scroll to top when category filter is applied', async ({ page }) => {
    // Scroll down first
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(200);

    // Click category badge
    const categoryBadge = page.locator('.cursor-pointer').filter({
      hasText: /Victims|Associates/
    }).first();

    if ((await categoryBadge.count()) > 0) {
      await categoryBadge.click();
      await page.waitForTimeout(500);

      // Check scroll position is near top
      const scrollY = await page.evaluate(() => window.scrollY);
      expect(scrollY).toBeLessThan(100);
    }
  });

  test('should show correct entity count in filter indicator', async ({ page }) => {
    // Navigate to filtered view
    await page.goto('http://localhost:5173/entities?category=victims');
    await page.waitForLoadState('networkidle');

    // Get count from filter indicator
    const filterText = await page.locator('.bg-primary\\/5').textContent();

    // Should contain entity count
    expect(filterText).toMatch(/\d+\s+(entity|entities)/);
  });

  test('should show empty state when no entities match category', async ({ page }) => {
    // Navigate to filtered view with unlikely category combination
    await page.goto('http://localhost:5173/entities?category=nonexistent&bio=true&search=zzzzz');
    await page.waitForLoadState('networkidle');

    // Should show empty state
    await expect(page.locator('text=No entities found')).toBeVisible();
    await expect(page.locator('text=Try adjusting your search or filter criteria')).toBeVisible();
  });
});

test.describe('Category Badge Hover Effects', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/entities');
    await page.waitForLoadState('networkidle');
  });

  test('should show hover effect on category badges', async ({ page }) => {
    const categoryBadge = page.locator('.cursor-pointer').first();

    if ((await categoryBadge.count()) > 0) {
      // Hover over badge
      await categoryBadge.hover();

      // Check cursor is pointer (indicated by cursor-pointer class)
      const classes = await categoryBadge.getAttribute('class');
      expect(classes).toContain('cursor-pointer');
      expect(classes).toContain('hover:opacity-80');
    }
  });

  test('should show tooltip on hover', async ({ page }) => {
    const categoryBadge = page.locator('.cursor-pointer[title*="Click to filter"]').first();

    if ((await categoryBadge.count()) > 0) {
      // Hover over badge
      await categoryBadge.hover();

      // Get title attribute
      const title = await categoryBadge.getAttribute('title');
      expect(title).toContain('Click to filter entities by');
    }
  });
});
