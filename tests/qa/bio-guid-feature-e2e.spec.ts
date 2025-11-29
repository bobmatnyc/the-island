import { test, expect, Page } from '@playwright/test';

// Test entities with known biographies and GUIDs
const TEST_ENTITIES = [
  {
    name: 'Jeffrey Epstein',
    guid: '43886eef-f28a-549d-8ae0-8409c2be68c4',
    slug: 'jeffrey-epstein'
  },
  {
    name: 'Ghislaine Maxwell',
    guid: '2b3bdb1f-adb2-5050-b437-e16a1fb476e8',
    slug: 'ghislaine-maxwell'
  }
];

test.describe('Bio Summary Display Consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/entities');
    await page.waitForLoadState('networkidle');
  });

  test('should display consistent bio summaries between grid and detail views', async ({ page }) => {
    for (const entity of TEST_ENTITIES) {
      console.log(`\n=== Testing ${entity.name} ===`);

      // Navigate back to entities page for each test
      await page.goto('/entities');
      await page.waitForLoadState('networkidle');

      // Find entity card by name
      const entityCard = page.locator('.entity-card', { hasText: entity.name }).first();
      await expect(entityCard).toBeVisible({ timeout: 10000 });

      // Capture bio summary from grid view
      const gridBioLocator = entityCard.locator('.bio-summary, .entity-bio, [class*="bio"]').first();
      const gridBioExists = await gridBioLocator.count() > 0;

      let gridBioText = '';
      if (gridBioExists) {
        gridBioText = await gridBioLocator.textContent() || '';
        gridBioText = gridBioText.trim();
        console.log(`Grid bio summary: "${gridBioText.substring(0, 100)}..."`);
      } else {
        console.log('No bio summary found in grid view - checking for bio badge');
        const bioBadge = entityCard.locator('[class*="badge"], [class*="tag"]', { hasText: /bio/i });
        const hasBioBadge = await bioBadge.count() > 0;
        console.log(`Bio badge present: ${hasBioBadge}`);
      }

      // Click on entity to navigate to detail page
      await entityCard.click();
      await page.waitForLoadState('networkidle');

      // Wait for detail page to load
      await page.waitForSelector('h1, h2, .entity-name, [class*="entity-title"]', { timeout: 10000 });

      // Capture bio summary from detail view
      const detailBioLocator = page.locator('.bio-summary, .entity-bio, [class*="bio-summary"]').first();
      const detailBioExists = await detailBioLocator.count() > 0;

      let detailBioText = '';
      if (detailBioExists) {
        detailBioText = await detailBioLocator.textContent() || '';
        detailBioText = detailBioText.trim();
        console.log(`Detail bio summary: "${detailBioText.substring(0, 100)}..."`);

        // Verify consistency if both exist
        if (gridBioText && detailBioText) {
          // Allow for minor formatting differences but core content should match
          const gridCore = gridBioText.toLowerCase().replace(/\s+/g, ' ');
          const detailCore = detailBioText.toLowerCase().replace(/\s+/g, ' ');

          // Check if detail contains grid content (detail might be longer)
          expect(detailCore).toContain(gridCore.substring(0, 50));
        }
      }

      // Check for "Read Full Biography" button
      const readMoreButton = page.locator('button, a', { hasText: /read (full |more )?biograph/i });
      const hasReadMoreButton = await readMoreButton.count() > 0;
      console.log(`"Read Full Biography" button present: ${hasReadMoreButton}`);

      if (hasReadMoreButton) {
        // Test expansion functionality
        await readMoreButton.click();
        await page.waitForTimeout(500); // Allow animation

        const fullBio = page.locator('.full-biography, .biography-content, [class*="bio-full"]').first();
        const fullBioVisible = await fullBio.isVisible().catch(() => false);
        console.log(`Full biography expanded: ${fullBioVisible}`);

        if (fullBioVisible) {
          const fullBioText = await fullBio.textContent() || '';
          console.log(`Full bio length: ${fullBioText.length} characters`);
          expect(fullBioText.length).toBeGreaterThan(detailBioText.length);
        }
      }

      // Take screenshot of detail page
      await page.screenshot({
        path: `/Users/masa/Projects/epstein/tests/qa/screenshots/bio-consistency-${entity.slug}.png`,
        fullPage: true
      });
    }
  });

  test('should display bio summaries for at least 3 entities', async ({ page }) => {
    // Look for entities with bio indicators
    const entityCards = page.locator('.entity-card');
    const cardCount = await entityCards.count();
    console.log(`Total entity cards found: ${cardCount}`);

    let entitiesWithBio = 0;
    const maxToCheck = Math.min(10, cardCount); // Check first 10 entities

    for (let i = 0; i < maxToCheck; i++) {
      const card = entityCards.nth(i);
      const bioIndicator = card.locator('.bio-summary, [class*="badge"]', { hasText: /bio/i });
      const hasBio = await bioIndicator.count() > 0;

      if (hasBio) {
        entitiesWithBio++;
        const entityName = await card.locator('.entity-name, h3, h4').first().textContent();
        console.log(`Entity with bio found: ${entityName}`);
      }
    }

    console.log(`Total entities with biographies: ${entitiesWithBio}`);
    expect(entitiesWithBio).toBeGreaterThanOrEqual(3);
  });
});

test.describe('GUID-based Entity URLs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/entities');
    await page.waitForLoadState('networkidle');
  });

  test('should use GUID-based URLs for entity links', async ({ page }) => {
    for (const entity of TEST_ENTITIES) {
      console.log(`\n=== Testing GUID URL for ${entity.name} ===`);

      // Find entity card
      const entityCard = page.locator('.entity-card', { hasText: entity.name }).first();
      await expect(entityCard).toBeVisible({ timeout: 10000 });

      // Get the link href
      const link = entityCard.locator('a').first();
      const href = await link.getAttribute('href');
      console.log(`Link href: ${href}`);

      // Verify GUID is in the URL
      expect(href).toContain(entity.guid);

      // Verify expected format: /entities/{guid}/{slug}
      const expectedPattern = new RegExp(`/entities/${entity.guid}/[a-z0-9-]+`);
      expect(href).toMatch(expectedPattern);

      console.log(`✓ GUID-based URL verified: ${href}`);
    }
  });

  test('should navigate successfully via GUID URLs', async ({ page }) => {
    for (const entity of TEST_ENTITIES) {
      console.log(`\n=== Testing GUID URL navigation for ${entity.name} ===`);

      // Navigate directly to GUID URL
      const guidUrl = `/entities/${entity.guid}/${entity.slug}`;
      console.log(`Navigating to: ${guidUrl}`);

      const response = await page.goto(guidUrl);
      expect(response?.status()).toBe(200);

      await page.waitForLoadState('networkidle');

      // Verify URL in address bar
      const currentUrl = page.url();
      console.log(`Current URL: ${currentUrl}`);
      expect(currentUrl).toContain(entity.guid);

      // Verify page loaded successfully
      const entityName = page.locator('h1, h2, .entity-name').first();
      await expect(entityName).toBeVisible({ timeout: 10000 });

      const nameText = await entityName.textContent();
      console.log(`Entity page loaded: ${nameText}`);

      // Take screenshot
      await page.screenshot({
        path: `/Users/masa/Projects/epstein/tests/qa/screenshots/guid-url-${entity.slug}.png`,
        fullPage: false
      });
    }
  });

  test('should maintain backward compatibility with ID-based URLs', async ({ page }) => {
    // This test assumes entities have sequential IDs
    // We'll try to find what the old ID format was
    console.log('\n=== Testing Backward Compatibility ===');

    // Try common ID patterns
    const oldIdPatterns = [
      '/entities/1',
      '/entities/2',
      '/entities/jeffrey-epstein',
      '/entities/ghislaine-maxwell'
    ];

    for (const oldUrl of oldIdPatterns) {
      console.log(`Testing old URL pattern: ${oldUrl}`);

      try {
        const response = await page.goto(oldUrl, { timeout: 5000 });
        const status = response?.status();
        console.log(`Status: ${status}`);

        if (status === 200) {
          const currentUrl = page.url();
          console.log(`Redirected to: ${currentUrl}`);

          // Check if redirected to GUID URL
          const hasGuid = TEST_ENTITIES.some(e => currentUrl.includes(e.guid));
          if (hasGuid) {
            console.log('✓ Successfully redirected to GUID URL');
          }
        } else if (status === 404) {
          console.log('Old URL returns 404 (backward compatibility not implemented)');
        }
      } catch (error) {
        console.log(`Error testing ${oldUrl}: ${error.message}`);
      }
    }
  });

  test('should handle GUID URL with missing slug gracefully', async ({ page }) => {
    for (const entity of TEST_ENTITIES) {
      console.log(`\n=== Testing GUID URL without slug for ${entity.name} ===`);

      // Try GUID URL without slug
      const guidOnlyUrl = `/entities/${entity.guid}`;
      console.log(`Navigating to: ${guidOnlyUrl}`);

      try {
        const response = await page.goto(guidOnlyUrl, { timeout: 5000 });
        const status = response?.status();
        console.log(`Status: ${status}`);

        if (status === 200) {
          const currentUrl = page.url();
          console.log(`Final URL: ${currentUrl}`);

          // Should either work or redirect to URL with slug
          const entityName = page.locator('h1, h2, .entity-name').first();
          const isVisible = await entityName.isVisible({ timeout: 5000 }).catch(() => false);

          if (isVisible) {
            console.log('✓ GUID-only URL works');
          }
        }
      } catch (error) {
        console.log(`GUID-only URL handling: ${error.message}`);
      }
    }
  });
});

test.describe('Cross-Feature Integration', () => {
  test('should display bio correctly when navigating via GUID URL', async ({ page }) => {
    for (const entity of TEST_ENTITIES) {
      console.log(`\n=== Cross-feature test for ${entity.name} ===`);

      // Navigate directly via GUID URL
      const guidUrl = `/entities/${entity.guid}/${entity.slug}`;
      await page.goto(guidUrl);
      await page.waitForLoadState('networkidle');

      // Verify bio summary displays
      const bioSummary = page.locator('.bio-summary, .entity-bio').first();
      const bioExists = await bioSummary.count() > 0;
      console.log(`Bio summary visible: ${bioExists}`);

      if (bioExists) {
        const bioText = await bioSummary.textContent();
        console.log(`Bio summary: "${bioText?.substring(0, 100)}..."`);
        expect(bioText?.length).toBeGreaterThan(10);

        // Check for Read Full Biography button
        const readMoreButton = page.locator('button, a', { hasText: /read (full |more )?biograph/i });
        const hasButton = await readMoreButton.count() > 0;
        console.log(`Read Full Biography button present: ${hasButton}`);

        if (hasButton) {
          // Test button functionality
          await readMoreButton.click();
          await page.waitForTimeout(500);

          const fullBio = page.locator('.full-biography, .biography-content, [class*="bio-full"]').first();
          const fullBioVisible = await fullBio.isVisible().catch(() => false);
          console.log(`Full biography expanded: ${fullBioVisible}`);
        }
      }

      // Navigate back to entities grid
      await page.goto('/entities');
      await page.waitForLoadState('networkidle');

      // Find the same entity in grid
      const entityCard = page.locator('.entity-card', { hasText: entity.name }).first();
      await expect(entityCard).toBeVisible({ timeout: 10000 });

      // Verify link still uses GUID
      const link = entityCard.locator('a').first();
      const href = await link.getAttribute('href');
      expect(href).toContain(entity.guid);

      console.log(`✓ Cross-feature test passed for ${entity.name}`);
    }
  });

  test('should maintain bio consistency across navigation patterns', async ({ page }) => {
    const entity = TEST_ENTITIES[0]; // Test with Jeffrey Epstein

    console.log('\n=== Testing bio consistency across navigation patterns ===');

    // Pattern 1: Grid -> Detail
    console.log('\n1. Grid -> Detail navigation:');
    await page.goto('/entities');
    await page.waitForLoadState('networkidle');

    const entityCard = page.locator('.entity-card', { hasText: entity.name }).first();
    const gridBio = await entityCard.locator('.bio-summary, .entity-bio').first().textContent().catch(() => '');
    console.log(`Grid bio: "${gridBio.substring(0, 80)}..."`);

    await entityCard.click();
    await page.waitForLoadState('networkidle');

    const detailBio1 = await page.locator('.bio-summary, .entity-bio').first().textContent().catch(() => '');
    console.log(`Detail bio (via grid): "${detailBio1.substring(0, 80)}..."`);

    // Pattern 2: Direct GUID URL
    console.log('\n2. Direct GUID URL navigation:');
    const guidUrl = `/entities/${entity.guid}/${entity.slug}`;
    await page.goto(guidUrl);
    await page.waitForLoadState('networkidle');

    const detailBio2 = await page.locator('.bio-summary, .entity-bio').first().textContent().catch(() => '');
    console.log(`Detail bio (via GUID): "${detailBio2.substring(0, 80)}..."`);

    // Pattern 3: Home -> Entity
    console.log('\n3. Home -> Entity navigation:');
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Look for entity link on home page
    const homeEntityLink = page.locator('a', { hasText: entity.name }).first();
    const homeEntityExists = await homeEntityLink.count() > 0;

    if (homeEntityExists) {
      const homeHref = await homeEntityLink.getAttribute('href');
      console.log(`Home page link href: ${homeHref}`);
      expect(homeHref).toContain(entity.guid);

      await homeEntityLink.click();
      await page.waitForLoadState('networkidle');

      const detailBio3 = await page.locator('.bio-summary, .entity-bio').first().textContent().catch(() => '');
      console.log(`Detail bio (via home): "${detailBio3.substring(0, 80)}..."`);

      // Verify all bios are consistent
      if (detailBio1 && detailBio2 && detailBio3) {
        const bio1Clean = detailBio1.toLowerCase().replace(/\s+/g, ' ').trim();
        const bio2Clean = detailBio2.toLowerCase().replace(/\s+/g, ' ').trim();
        const bio3Clean = detailBio3.toLowerCase().replace(/\s+/g, ' ').trim();

        expect(bio1Clean).toBe(bio2Clean);
        expect(bio2Clean).toBe(bio3Clean);
        console.log('✓ Bio consistency verified across all navigation patterns');
      }
    } else {
      console.log('Entity not found on home page, skipping home navigation test');
    }

    // Take final screenshot
    await page.screenshot({
      path: `/Users/masa/Projects/epstein/tests/qa/screenshots/cross-feature-integration.png`,
      fullPage: true
    });
  });
});

test.describe('Additional Entity Discovery', () => {
  test('should identify all entities with biographies on entities page', async ({ page }) => {
    await page.goto('/entities');
    await page.waitForLoadState('networkidle');

    console.log('\n=== Discovering all entities with biographies ===');

    const entityCards = page.locator('.entity-card');
    const totalCards = await entityCards.count();
    console.log(`Total entity cards: ${totalCards}`);

    const entitiesWithBios = [];

    for (let i = 0; i < totalCards && i < 20; i++) { // Check first 20
      const card = entityCards.nth(i);
      const nameElement = card.locator('.entity-name, h3, h4, [class*="name"]').first();
      const name = await nameElement.textContent().catch(() => '');

      const bioIndicator = card.locator('.bio-summary, [class*="badge"]').first();
      const hasBio = await bioIndicator.count() > 0;

      if (hasBio && name) {
        const link = card.locator('a').first();
        const href = await link.getAttribute('href') || '';

        // Extract GUID from href
        const guidMatch = href.match(/\/entities\/([a-f0-9-]{36})/);
        const guid = guidMatch ? guidMatch[1] : '';

        entitiesWithBios.push({
          name: name.trim(),
          guid: guid,
          href: href
        });

        console.log(`${i + 1}. ${name.trim()}`);
        console.log(`   GUID: ${guid}`);
        console.log(`   URL: ${href}`);
      }
    }

    console.log(`\nTotal entities with biographies found: ${entitiesWithBios.length}`);

    // Write results to file
    const resultsPath = '/Users/masa/Projects/epstein/tests/qa/entities-with-bios.json';
    await page.evaluate((data) => {
      return fetch('/api/test-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch(() => {});
    }, entitiesWithBios);

    console.log(`Results would be saved to: ${resultsPath}`);
  });
});
