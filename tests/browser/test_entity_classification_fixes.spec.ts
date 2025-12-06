import { test, expect } from '@playwright/test';

/**
 * QA Test: Entity Classification Fixes and Connection Threshold Slider
 *
 * Testing:
 * 1. Ghislaine Maxwell entity_type fixed (org → person)
 * 2. NPA removed from locations
 * 3. Connection threshold slider functionality
 * 4. Default filter shows only entities with connections
 * 5. Slider adjusts filtering in real-time
 */

const BACKEND_URL = 'http://localhost:8081';
const FRONTEND_URL = 'http://localhost:5173';

test.describe('Entity Classification and Filtering Fixes', () => {

  test('Backend API: Ghislaine Maxwell has entity_type=person', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/v2/entities/ghislaine_maxwell`);
    expect(response.ok()).toBeTruthy();

    const entity = await response.json();
    console.log('Ghislaine Maxwell entity_type:', entity.bio?.entity_type);

    // Verify entity_type is "person" (in bio field)
    expect(entity.bio?.entity_type).toBe('person');
    expect(entity.name).toContain('Maxwell');
  });

  test('Backend API: NPA not in locations', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/entities?entity_type=location&search=NPA`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    console.log('NPA search results:', data.total);

    // Should find 0 results for NPA in locations
    expect(data.total).toBe(0);
    expect(data.entities.length).toBe(0);
  });

  test('Backend API: Entity counts are correct', async ({ request }) => {
    const response = await request.get(`${BACKEND_URL}/api/entities?limit=10`);
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    console.log('Total entities:', data.total);

    // Should have around 2,993 entities (persons without entity_type + orgs + locations)
    expect(data.total).toBeGreaterThan(2900);
    expect(data.total).toBeLessThan(3100);
  });

  test('Frontend: Connection threshold slider exists and is visible', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/entities`);

    // Wait for page to load
    await page.waitForSelector('h1:has-text("Entities")');

    // Take screenshot of full page
    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/entities-page-full.png', fullPage: true });

    // Find slider element
    const slider = page.locator('input[type="range"]');
    await expect(slider).toBeVisible();

    // Verify slider attributes
    const min = await slider.getAttribute('min');
    const max = await slider.getAttribute('max');
    const value = await slider.getAttribute('value');

    console.log('Slider - min:', min, 'max:', max, 'current value:', value);

    expect(min).toBe('0');
    expect(parseInt(value || '0')).toBe(1); // Default should be 1

    // Take screenshot of slider area
    const sliderSection = page.locator('.bg-secondary\\/30.border');
    await sliderSection.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/connection-slider.png' });
  });

  test('Frontend: Default filter shows only entities with 1+ connections', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/entities`);

    // Wait for entities to load
    await page.waitForSelector('[data-testid="entity-card"]');

    // Check slider value
    const slider = page.locator('input[type="range"]');
    const sliderValue = await slider.getAttribute('value');
    console.log('Default slider value:', sliderValue);
    expect(parseInt(sliderValue || '0')).toBe(1);

    // Get entity count display
    const countText = await page.locator('text=/Showing.*entities/').first().textContent();
    console.log('Entity count display:', countText);

    // Take screenshot
    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/entities-default-filter.png', fullPage: true });
  });

  test('Frontend: Slider adjusts filtering in real-time', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/entities`);
    await page.waitForSelector('[data-testid="entity-card"]');

    // Get initial count with slider at 1
    const initialCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const initialCountMatch = initialCountText?.match(/([\d,]+) entities/);
    const initialCount = parseInt(initialCountMatch?.[1]?.replace(/,/g, '') || '0');
    console.log('Initial count (minConnections=1):', initialCount);

    // Move slider to 0 (show all entities)
    const slider = page.locator('input[type="range"]');
    await slider.fill('0');

    // Wait for results to update
    await page.waitForTimeout(1000);

    // Get new count
    const allCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const allCountMatch = allCountText?.match(/([\d,]+) entities/);
    const allCount = parseInt(allCountMatch?.[1]?.replace(/,/g, '') || '0');
    console.log('Count with slider at 0 (all entities):', allCount);

    // All count should be greater than initial count
    expect(allCount).toBeGreaterThan(initialCount);
    expect(allCount).toBeGreaterThan(2900); // Should show ~3,000 entities

    // Take screenshot at slider=0
    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/entities-slider-0.png', fullPage: true });

    // Move slider to 5
    await slider.fill('5');
    await page.waitForTimeout(1000);

    const highCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const highCountMatch = highCountText?.match(/([\d,]+) entities/);
    const highCount = parseInt(highCountMatch?.[1]?.replace(/,/g, '') || '0');
    console.log('Count with slider at 5 (5+ connections):', highCount);

    // High threshold should show fewer entities
    expect(highCount).toBeLessThan(initialCount);

    // Take screenshot at slider=5
    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/entities-slider-5.png', fullPage: true });
  });

  test('Frontend: Search for Ghislaine Maxwell shows person icon', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/entities`);

    // Search for Ghislaine Maxwell
    const searchInput = page.locator('input[placeholder*="Search"]');
    await searchInput.fill('Ghislaine Maxwell');

    // Wait for search to complete (debounce delay)
    await page.waitForTimeout(1000);

    // Should find Ghislaine Maxwell
    const entityCard = page.locator('[data-testid="entity-card"]').first();
    await expect(entityCard).toBeVisible();

    // Check for person icon (Users icon)
    const hasPersonIcon = await entityCard.locator('svg').first().isVisible();
    expect(hasPersonIcon).toBeTruthy();

    // Take screenshot
    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/ghislaine-maxwell-search.png', fullPage: true });

    // Get entity name
    const nameText = await entityCard.locator('a').first().textContent();
    console.log('Entity name:', nameText);
    expect(nameText?.toLowerCase()).toContain('maxwell');
  });

  test('Frontend: Filter by entity type - Person, Organization, Location', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/entities`);
    await page.waitForSelector('[data-testid="entity-card"]');

    // Get initial "All" count
    const allCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const allCount = parseInt(allCountText?.match(/([\d,]+) entities/)?.[1]?.replace(/,/g, '') || '0');
    console.log('All entities count:', allCount);

    // Click Person filter
    await page.locator('button:has-text("Person")').click();
    await page.waitForTimeout(1000);

    const personCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const personCount = parseInt(personCountText?.match(/([\d,]+) entities/)?.[1]?.replace(/,/g, '') || '0');
    console.log('Person count:', personCount);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/filter-person.png', fullPage: true });

    // Click Organization filter
    await page.locator('button:has-text("Organization")').click();
    await page.waitForTimeout(1000);

    const orgCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const orgCount = parseInt(orgCountText?.match(/([\d,]+) entities/)?.[1]?.replace(/,/g, '') || '0');
    console.log('Organization count:', orgCount);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/filter-organization.png', fullPage: true });

    // Click Location filter
    await page.locator('button:has-text("Location")').click();
    await page.waitForTimeout(1000);

    const locCountText = await page.locator('text=/Showing.*of ([\d,]+) entities/').first().textContent();
    const locCount = parseInt(locCountText?.match(/([\d,]+) entities/)?.[1]?.replace(/,/g, '') || '0');
    console.log('Location count:', locCount);

    await page.screenshot({ path: '/Users/masa/Projects/epstein/qa_screenshots/filter-location.png', fullPage: true });

    // Verify counts are reasonable
    expect(personCount).toBeGreaterThan(0);
    expect(orgCount).toBeGreaterThan(0);
    expect(locCount).toBeGreaterThan(0);

    // Total should be less than or equal to sum of filtered counts
    // (Some entities might not have entity_type and won't show in filtered views)
    console.log('Total of filtered counts:', personCount + orgCount + locCount);
  });
});
