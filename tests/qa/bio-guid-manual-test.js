const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

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

const BASE_URL = 'http://localhost:5173';
const SCREENSHOT_DIR = path.join(__dirname, 'screenshots');

class TestReporter {
  constructor() {
    this.results = [];
    this.startTime = Date.now();
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    console.log(`[${type.toUpperCase()}] ${message}`);
    this.results.push({ timestamp, type, message });
  }

  success(message) {
    this.log(`✓ ${message}`, 'success');
  }

  error(message) {
    this.log(`✗ ${message}`, 'error');
  }

  warn(message) {
    this.log(`⚠ ${message}`, 'warn');
  }

  async generateReport() {
    const duration = Date.now() - this.startTime;
    const successCount = this.results.filter(r => r.type === 'success').length;
    const errorCount = this.results.filter(r => r.type === 'error').length;
    const warnCount = this.results.filter(r => r.type === 'warn').length;

    const report = {
      summary: {
        duration: `${(duration / 1000).toFixed(2)}s`,
        totalChecks: this.results.length,
        passed: successCount,
        failed: errorCount,
        warnings: warnCount
      },
      results: this.results
    };

    const reportPath = path.join(__dirname, 'bio-guid-test-results.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    this.log(`Report saved to: ${reportPath}`, 'info');

    return report;
  }
}

async function testBioSummaryConsistency(page, reporter) {
  reporter.log('\n=== TEST 1: Bio Summary Display Consistency ===');

  for (const entity of TEST_ENTITIES) {
    reporter.log(`\nTesting: ${entity.name}`);

    // Navigate to entities page
    await page.goto(`${BASE_URL}/entities`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Find entity card
    const entityCards = await page.locator('.entity-card').all();
    let entityCard = null;

    for (const card of entityCards) {
      const text = await card.textContent();
      if (text.includes(entity.name)) {
        entityCard = card;
        break;
      }
    }

    if (!entityCard) {
      reporter.error(`Entity card not found: ${entity.name}`);
      continue;
    }

    reporter.success(`Found entity card: ${entity.name}`);

    // Capture bio summary from grid view
    let gridBioText = '';
    try {
      const bioElements = await entityCard.locator('.bio-summary, .entity-bio, [class*="bio"]').all();
      if (bioElements.length > 0) {
        gridBioText = await bioElements[0].textContent() || '';
        gridBioText = gridBioText.trim();
        reporter.log(`Grid bio: "${gridBioText.substring(0, 80)}..."`);
      } else {
        reporter.warn('No bio summary found in grid view');
      }
    } catch (error) {
      reporter.warn(`Error reading grid bio: ${error.message}`);
    }

    // Click on entity card
    await entityCard.click();
    await page.waitForLoadState('networkidle', { timeout: 10000 });
    await page.waitForTimeout(1000); // Allow for animations

    // Capture bio summary from detail view
    let detailBioText = '';
    try {
      const detailBioElements = await page.locator('.bio-summary, .entity-bio, [class*="bio-summary"]').all();
      if (detailBioElements.length > 0) {
        detailBioText = await detailBioElements[0].textContent() || '';
        detailBioText = detailBioText.trim();
        reporter.log(`Detail bio: "${detailBioText.substring(0, 80)}..."`);
      } else {
        reporter.warn('No bio summary found in detail view');
      }
    } catch (error) {
      reporter.warn(`Error reading detail bio: ${error.message}`);
    }

    // Verify consistency
    if (gridBioText && detailBioText) {
      const gridCore = gridBioText.toLowerCase().replace(/\s+/g, ' ').substring(0, 100);
      const detailCore = detailBioText.toLowerCase().replace(/\s+/g, ' ').substring(0, 100);

      if (detailCore.includes(gridCore.substring(0, 50))) {
        reporter.success('Bio summaries are consistent between grid and detail views');
      } else {
        reporter.error('Bio summaries differ between views');
        reporter.log(`Grid: ${gridCore}`);
        reporter.log(`Detail: ${detailCore}`);
      }
    }

    // Check for "Read Full Biography" button
    try {
      const readMoreButtons = await page.locator('button, a').all();
      let hasReadMoreButton = false;

      for (const button of readMoreButtons) {
        const text = await button.textContent();
        if (text && /read (full |more )?biograph/i.test(text)) {
          hasReadMoreButton = true;
          reporter.success('"Read Full Biography" button found');

          // Test expansion
          await button.click();
          await page.waitForTimeout(500);

          const fullBioElements = await page.locator('.full-biography, .biography-content, [class*="bio-full"]').all();
          if (fullBioElements.length > 0) {
            const fullBioText = await fullBioElements[0].textContent() || '';
            reporter.success(`Full biography expanded (${fullBioText.length} characters)`);
          }
          break;
        }
      }

      if (!hasReadMoreButton) {
        reporter.warn('"Read Full Biography" button not found');
      }
    } catch (error) {
      reporter.warn(`Error testing Read Full Biography button: ${error.message}`);
    }

    // Take screenshot
    const screenshotPath = path.join(SCREENSHOT_DIR, `bio-consistency-${entity.slug}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    reporter.log(`Screenshot saved: ${screenshotPath}`);
  }
}

async function testGuidUrls(page, reporter) {
  reporter.log('\n=== TEST 2: GUID-based Entity URLs ===');

  for (const entity of TEST_ENTITIES) {
    reporter.log(`\nTesting GUID URL: ${entity.name}`);

    // Navigate to entities page
    await page.goto(`${BASE_URL}/entities`);
    await page.waitForLoadState('networkidle', { timeout: 10000 });

    // Find entity card and check link href
    const entityCards = await page.locator('.entity-card').all();
    let foundLink = false;

    for (const card of entityCards) {
      const text = await card.textContent();
      if (text.includes(entity.name)) {
        const links = await card.locator('a').all();
        if (links.length > 0) {
          const href = await links[0].getAttribute('href');
          reporter.log(`Link href: ${href}`);

          if (href && href.includes(entity.guid)) {
            reporter.success(`GUID found in URL: ${entity.guid}`);
            foundLink = true;

            // Verify format: /entities/{guid}/{slug}
            const expectedPattern = new RegExp(`/entities/${entity.guid}/[a-z0-9-]+`);
            if (expectedPattern.test(href)) {
              reporter.success('URL format matches expected pattern');
            } else {
              reporter.error(`URL format incorrect: ${href}`);
            }
          } else {
            reporter.error(`GUID not found in URL: ${href}`);
          }
        }
        break;
      }
    }

    if (!foundLink) {
      reporter.error(`Could not find link for: ${entity.name}`);
      continue;
    }

    // Test direct GUID URL navigation
    const guidUrl = `/entities/${entity.guid}/${entity.slug}`;
    reporter.log(`Navigating to: ${guidUrl}`);

    try {
      const response = await page.goto(`${BASE_URL}${guidUrl}`);
      const status = response.status();
      reporter.log(`HTTP Status: ${status}`);

      if (status === 200) {
        reporter.success('GUID URL navigation successful');

        // Verify URL in address bar
        const currentUrl = page.url();
        if (currentUrl.includes(entity.guid)) {
          reporter.success('GUID present in address bar');
        } else {
          reporter.error('GUID missing from address bar');
        }

        // Verify page loaded
        await page.waitForSelector('h1, h2, .entity-name', { timeout: 5000 });
        reporter.success('Entity detail page loaded');

        // Take screenshot
        const screenshotPath = path.join(SCREENSHOT_DIR, `guid-url-${entity.slug}.png`);
        await page.screenshot({ path: screenshotPath, fullPage: false });
        reporter.log(`Screenshot saved: ${screenshotPath}`);
      } else {
        reporter.error(`GUID URL returned status ${status}`);
      }
    } catch (error) {
      reporter.error(`GUID URL navigation failed: ${error.message}`);
    }

    // Test GUID-only URL (without slug)
    const guidOnlyUrl = `/entities/${entity.guid}`;
    reporter.log(`Testing GUID-only URL: ${guidOnlyUrl}`);

    try {
      const response = await page.goto(`${BASE_URL}${guidOnlyUrl}`, { timeout: 5000 });
      const status = response.status();

      if (status === 200) {
        reporter.success('GUID-only URL works');
      } else if (status === 301 || status === 302) {
        reporter.success(`GUID-only URL redirects (${status})`);
      } else {
        reporter.warn(`GUID-only URL returned ${status}`);
      }
    } catch (error) {
      reporter.warn(`GUID-only URL: ${error.message}`);
    }
  }
}

async function testCrossFeatureIntegration(page, reporter) {
  reporter.log('\n=== TEST 3: Cross-Feature Integration ===');

  const entity = TEST_ENTITIES[0]; // Test with Jeffrey Epstein
  reporter.log(`Testing cross-feature with: ${entity.name}`);

  // Navigate directly via GUID URL
  const guidUrl = `/entities/${entity.guid}/${entity.slug}`;
  await page.goto(`${BASE_URL}${guidUrl}`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  // Verify bio displays correctly
  try {
    const bioElements = await page.locator('.bio-summary, .entity-bio').all();
    if (bioElements.length > 0) {
      const bioText = await bioElements[0].textContent() || '';
      reporter.success(`Bio displayed via GUID URL (${bioText.length} chars)`);
      reporter.log(`Bio text: "${bioText.substring(0, 80)}..."`);

      // Check for Read Full Biography button
      const buttons = await page.locator('button, a').all();
      let foundButton = false;

      for (const button of buttons) {
        const text = await button.textContent();
        if (text && /read (full |more )?biograph/i.test(text)) {
          foundButton = true;
          reporter.success('"Read Full Biography" button works via GUID URL');

          // Test button
          await button.click();
          await page.waitForTimeout(500);

          const fullBioElements = await page.locator('.full-biography, .biography-content').all();
          if (fullBioElements.length > 0) {
            reporter.success('Full biography expansion works');
          }
          break;
        }
      }

      if (!foundButton) {
        reporter.warn('"Read Full Biography" button not found');
      }
    } else {
      reporter.error('No bio displayed via GUID URL');
    }
  } catch (error) {
    reporter.error(`Bio verification failed: ${error.message}`);
  }

  // Navigate back to grid
  await page.goto(`${BASE_URL}/entities`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  // Verify link still uses GUID
  const entityCards = await page.locator('.entity-card').all();
  for (const card of entityCards) {
    const text = await card.textContent();
    if (text.includes(entity.name)) {
      const links = await card.locator('a').all();
      if (links.length > 0) {
        const href = await links[0].getAttribute('href');
        if (href && href.includes(entity.guid)) {
          reporter.success('Grid link still uses GUID after navigation');
        } else {
          reporter.error('Grid link does not use GUID');
        }
      }
      break;
    }
  }

  // Take final screenshot
  const screenshotPath = path.join(SCREENSHOT_DIR, 'cross-feature-integration.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  reporter.log(`Screenshot saved: ${screenshotPath}`);
}

async function testEntityDiscovery(page, reporter) {
  reporter.log('\n=== TEST 4: Entity Discovery ===');

  await page.goto(`${BASE_URL}/entities`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  const entityCards = await page.locator('.entity-card').all();
  reporter.log(`Total entity cards found: ${entityCards.length}`);

  let entitiesWithBio = 0;
  const entitiesFound = [];

  for (let i = 0; i < Math.min(20, entityCards.length); i++) {
    const card = entityCards[i];
    const nameElements = await card.locator('.entity-name, h3, h4, [class*="name"]').all();
    const name = nameElements.length > 0 ? await nameElements[0].textContent() : '';

    const bioIndicators = await card.locator('.bio-summary, [class*="badge"]').all();
    const hasBio = bioIndicators.length > 0;

    if (hasBio && name) {
      entitiesWithBio++;
      const links = await card.locator('a').all();
      const href = links.length > 0 ? await links[0].getAttribute('href') : '';

      // Extract GUID
      const guidMatch = href ? href.match(/\/entities\/([a-f0-9-]{36})/) : null;
      const guid = guidMatch ? guidMatch[1] : '';

      entitiesFound.push({
        name: name.trim(),
        guid: guid,
        href: href
      });

      reporter.log(`${i + 1}. ${name.trim()} - GUID: ${guid}`);
    }
  }

  reporter.log(`Entities with biographies: ${entitiesWithBio}`);

  if (entitiesWithBio >= 3) {
    reporter.success('Found at least 3 entities with biographies');
  } else {
    reporter.error(`Only found ${entitiesWithBio} entities with biographies (expected ≥3)`);
  }

  // Save discovered entities
  const discoveryPath = path.join(__dirname, 'entities-with-bios.json');
  await fs.writeFile(discoveryPath, JSON.stringify(entitiesFound, null, 2));
  reporter.log(`Discovered entities saved to: ${discoveryPath}`);
}

async function runAllTests() {
  const reporter = new TestReporter();
  let browser;

  try {
    // Create screenshots directory
    await fs.mkdir(SCREENSHOT_DIR, { recursive: true });

    reporter.log('Starting E2E tests...');
    reporter.log(`Base URL: ${BASE_URL}`);

    // Launch browser
    browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Run all test suites
    await testBioSummaryConsistency(page, reporter);
    await testGuidUrls(page, reporter);
    await testCrossFeatureIntegration(page, reporter);
    await testEntityDiscovery(page, reporter);

    // Generate report
    reporter.log('\n=== Generating Report ===');
    const report = await reporter.generateReport();

    console.log('\n=== TEST SUMMARY ===');
    console.log(`Duration: ${report.summary.duration}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
    console.log(`Warnings: ${report.summary.warnings}`);

    await browser.close();

    process.exit(report.summary.failed > 0 ? 1 : 0);
  } catch (error) {
    reporter.error(`Fatal error: ${error.message}`);
    console.error(error);

    if (browser) {
      await browser.close();
    }

    process.exit(1);
  }
}

// Run tests
runAllTests();
