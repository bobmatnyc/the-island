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

async function findEntityContainer(page, entityName) {
  // Try multiple strategies to find the entity
  const allText = await page.content();

  // First, let's find all links and divs that might contain the entity name
  const links = await page.locator('a').all();

  for (const link of links) {
    const text = await link.textContent();
    if (text && text.trim() === entityName) {
      return link;
    }
  }

  // Try finding by partial text match
  const containers = await page.locator('div, article, section').all();
  for (const container of containers) {
    const text = await container.textContent();
    if (text && text.includes(entityName)) {
      return container;
    }
  }

  return null;
}

async function testEntityPage(page, reporter) {
  reporter.log('\n=== Inspecting Entities Page Structure ===');

  await page.goto(`${BASE_URL}/entities`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  // Take initial screenshot
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, 'entities-page-full.png'),
    fullPage: true
  });
  reporter.log('Full page screenshot captured');

  // Get all links and analyze them
  const links = await page.locator('a').all();
  reporter.log(`Total links found: ${links.length}`);

  let guidLinks = [];
  let entityLinksFound = 0;

  for (const link of links) {
    const href = await link.getAttribute('href');
    const text = await link.textContent();

    if (href && href.includes('/entities/')) {
      entityLinksFound++;

      // Check if it's a GUID-based URL
      const guidMatch = href.match(/\/entities\/([a-f0-9-]{36})/);
      if (guidMatch) {
        guidLinks.push({
          text: text?.trim() || '',
          href: href,
          guid: guidMatch[1]
        });
      }
    }
  }

  reporter.log(`Entity links found: ${entityLinksFound}`);
  reporter.log(`GUID-based links found: ${guidLinks.length}`);

  if (guidLinks.length > 0) {
    reporter.success(`Found ${guidLinks.length} GUID-based entity URLs`);

    // Show first few examples
    for (let i = 0; i < Math.min(5, guidLinks.length); i++) {
      reporter.log(`  - ${guidLinks[i].text}: ${guidLinks[i].href}`);
    }
  } else {
    reporter.error('No GUID-based URLs found on entities page');
  }

  return guidLinks;
}

async function testSpecificEntity(page, entity, reporter) {
  reporter.log(`\n=== Testing: ${entity.name} ===`);

  // Navigate to entities page
  await page.goto(`${BASE_URL}/entities`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  // Find the entity link by exact text match
  const links = await page.locator('a').all();
  let entityLink = null;

  for (const link of links) {
    const text = await link.textContent();
    if (text && text.trim() === entity.name) {
      entityLink = link;
      break;
    }
  }

  if (!entityLink) {
    reporter.error(`Entity link not found: ${entity.name}`);
    return false;
  }

  reporter.success(`Found link for: ${entity.name}`);

  // Check the href
  const href = await entityLink.getAttribute('href');
  reporter.log(`Link href: ${href}`);

  if (!href) {
    reporter.error('Link has no href attribute');
    return false;
  }

  // Verify GUID in URL
  if (href.includes(entity.guid)) {
    reporter.success(`GUID found in URL: ${entity.guid}`);
  } else {
    reporter.error(`GUID NOT found in URL. Expected: ${entity.guid}, Got: ${href}`);
    return false;
  }

  // Verify URL format
  const expectedPattern = new RegExp(`/entities/${entity.guid}(/[a-z0-9-]+)?`);
  if (expectedPattern.test(href)) {
    reporter.success('URL format matches expected pattern');
  } else {
    reporter.warn(`URL format may be incorrect: ${href}`);
  }

  // Click and navigate to detail page
  reporter.log('Clicking entity link...');
  await entityLink.click();
  await page.waitForLoadState('networkidle', { timeout: 10000 });
  await page.waitForTimeout(1000);

  // Verify URL in address bar
  const currentUrl = page.url();
  reporter.log(`Current URL: ${currentUrl}`);

  if (currentUrl.includes(entity.guid)) {
    reporter.success('GUID present in browser address bar');
  } else {
    reporter.error('GUID NOT present in browser address bar');
  }

  // Take screenshot of detail page
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, `entity-detail-${entity.slug}.png`),
    fullPage: true
  });
  reporter.log('Detail page screenshot captured');

  // Check for bio content on detail page
  const pageContent = await page.content();

  // Look for various bio indicators
  const bioKeywords = ['biography', 'bio', 'background', 'about'];
  let bioFound = false;

  for (const keyword of bioKeywords) {
    if (pageContent.toLowerCase().includes(keyword)) {
      bioFound = true;
      reporter.log(`Found keyword: ${keyword}`);
    }
  }

  if (bioFound) {
    reporter.success('Bio content appears to be present on detail page');
  } else {
    reporter.warn('No obvious bio content found on detail page');
  }

  // Look for "Read Full Biography" or similar buttons
  const buttons = await page.locator('button, a').all();
  let bioButtonFound = false;

  for (const button of buttons) {
    const text = await button.textContent();
    if (text && /read|view|show|biography|bio/i.test(text)) {
      bioButtonFound = true;
      reporter.log(`Found potential bio button: "${text.trim()}"`);
    }
  }

  if (bioButtonFound) {
    reporter.success('Bio expansion controls found');
  }

  return true;
}

async function testDirectGuidNavigation(page, entity, reporter) {
  reporter.log(`\n=== Testing Direct GUID Navigation: ${entity.name} ===`);

  // Test with slug
  const guidUrlWithSlug = `${BASE_URL}/entities/${entity.guid}/${entity.slug}`;
  reporter.log(`Navigating to: ${guidUrlWithSlug}`);

  try {
    const response = await page.goto(guidUrlWithSlug, { timeout: 10000 });
    const status = response.status();
    reporter.log(`HTTP Status: ${status}`);

    if (status === 200) {
      reporter.success('GUID URL with slug works (HTTP 200)');

      // Verify page loaded
      await page.waitForLoadState('networkidle');
      const title = await page.title();
      reporter.log(`Page title: ${title}`);

      // Take screenshot
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, `guid-direct-${entity.slug}.png`),
        fullPage: false
      });
      reporter.log('Screenshot captured');
    } else {
      reporter.error(`GUID URL returned unexpected status: ${status}`);
    }
  } catch (error) {
    reporter.error(`GUID URL navigation failed: ${error.message}`);
  }

  // Test without slug
  const guidUrlNoSlug = `${BASE_URL}/entities/${entity.guid}`;
  reporter.log(`Testing without slug: ${guidUrlNoSlug}`);

  try {
    const response = await page.goto(guidUrlNoSlug, { timeout: 5000 });
    const status = response.status();

    if (status === 200) {
      reporter.success('GUID-only URL works (HTTP 200)');
    } else if (status === 301 || status === 302) {
      reporter.success(`GUID-only URL redirects to proper URL (HTTP ${status})`);
      const finalUrl = page.url();
      reporter.log(`Redirected to: ${finalUrl}`);
    } else {
      reporter.warn(`GUID-only URL returned status: ${status}`);
    }
  } catch (error) {
    reporter.warn(`GUID-only URL: ${error.message}`);
  }
}

async function testBioConsistency(page, entity, reporter) {
  reporter.log(`\n=== Testing Bio Consistency: ${entity.name} ===`);

  // Get bio from grid view (if visible)
  await page.goto(`${BASE_URL}/entities`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  // Try to find bio summary near the entity name
  const links = await page.locator('a').all();
  let entityContainer = null;

  for (const link of links) {
    const text = await link.textContent();
    if (text && text.trim() === entity.name) {
      // Get parent container
      entityContainer = link.locator('xpath=ancestor::*[contains(@class, "card") or contains(@class, "item") or contains(@class, "entity")][1]');
      break;
    }
  }

  let gridBio = '';
  if (entityContainer && await entityContainer.count() > 0) {
    const containerText = await entityContainer.textContent();
    reporter.log(`Container text preview: ${containerText.substring(0, 100)}...`);

    // Look for bio indicators in container
    if (containerText.toLowerCase().includes('biography') ||
        containerText.toLowerCase().includes('bio')) {
      gridBio = containerText;
      reporter.success('Bio content found in grid view');
    }
  }

  // Navigate to detail view
  await page.goto(`${BASE_URL}/entities/${entity.guid}/${entity.slug}`);
  await page.waitForLoadState('networkidle', { timeout: 10000 });

  const detailContent = await page.content();

  // Look for bio in detail view
  if (detailContent.toLowerCase().includes('biography') ||
      detailContent.toLowerCase().includes('bio')) {
    reporter.success('Bio content found in detail view');

    // Try to extract bio text
    const bodyText = await page.locator('main, article, .content').first().textContent().catch(() => '');
    reporter.log(`Detail content preview: ${bodyText.substring(0, 150)}...`);
  } else {
    reporter.warn('No bio content found in detail view');
  }
}

async function runAllTests() {
  const reporter = new TestReporter();
  let browser;

  try {
    // Create screenshots directory
    await fs.mkdir(SCREENSHOT_DIR, { recursive: true });

    reporter.log('=== Starting E2E Tests for Bio Summary & GUID URLs ===');
    reporter.log(`Base URL: ${BASE_URL}`);
    reporter.log(`Test Time: ${new Date().toISOString()}`);

    // Launch browser
    reporter.log('\nLaunching browser...');
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Test 1: Inspect entities page
    const guidLinks = await testEntityPage(page, reporter);

    // Test 2: Test specific entities
    for (const entity of TEST_ENTITIES) {
      await testSpecificEntity(page, entity, reporter);
      await testDirectGuidNavigation(page, entity, reporter);
      await testBioConsistency(page, entity, reporter);
    }

    // Generate report
    reporter.log('\n=== Generating Final Report ===');
    const report = await reporter.generateReport();

    console.log('\n╔════════════════════════════════════════╗');
    console.log('║         TEST SUMMARY                   ║');
    console.log('╠════════════════════════════════════════╣');
    console.log(`║ Duration:   ${report.summary.duration.padEnd(26)}║`);
    console.log(`║ Passed:     ${String(report.summary.passed).padEnd(26)}║`);
    console.log(`║ Failed:     ${String(report.summary.failed).padEnd(26)}║`);
    console.log(`║ Warnings:   ${String(report.summary.warnings).padEnd(26)}║`);
    console.log('╚════════════════════════════════════════╝');

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
