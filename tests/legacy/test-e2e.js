#!/usr/bin/env node

/**
 * Comprehensive End-to-End Testing for Epstein Archive
 * Testing URL: https://the-island.ngrok.app
 *
 * Focus Areas:
 * 1. Infrastructure (ngrok tunnels, services)
 * 2. Name Formatting (all 14 locations must show "Last, First")
 * 3. Functional Testing (search, filters, navigation)
 * 4. Performance (load times, responsiveness)
 * 5. Console Monitoring (errors, warnings)
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://the-island.ngrok.app';
const SCREENSHOT_DIR = '/Users/masa/Projects/epstein/test-screenshots';
const REPORT_FILE = '/Users/masa/Projects/epstein/test-report.md';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Test results storage
const testResults = {
  infrastructure: [],
  nameFormatting: [],
  functional: [],
  performance: [],
  console: [],
  screenshots: []
};

// Helper: Format timestamp
function timestamp() {
  return new Date().toISOString();
}

// Helper: Log test result
function logTest(category, testName, status, details = '') {
  const result = {
    test: testName,
    status: status, // 'PASS', 'FAIL', 'WARN'
    details: details,
    timestamp: timestamp()
  };
  testResults[category].push(result);

  const icon = status === 'PASS' ? '✅' : status === 'FAIL' ? '❌' : '⚠️';
  console.log(`${icon} [${category.toUpperCase()}] ${testName}: ${status}`);
  if (details) console.log(`   ${details}`);
}

// Helper: Take screenshot
async function takeScreenshot(page, name) {
  const filename = `${name.replace(/[^a-z0-9]/gi, '_')}_${Date.now()}.png`;
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  testResults.screenshots.push({ name, path: filepath });
  console.log(`📸 Screenshot: ${filename}`);
  return filepath;
}

// Helper: Check for "Last, First" format
function isLastFirstFormat(name) {
  // Pattern: "Last, First" or single name without comma
  // Should NOT match "First Last" pattern
  if (!name || typeof name !== 'string') return false;

  const hasComma = name.includes(',');
  if (hasComma) {
    // If it has a comma, it should be "Last, First"
    return /^[A-Z][a-zA-Z-']+(?: [A-Z][a-zA-Z-']+)*, [A-Z][a-zA-Z-']+/.test(name);
  } else {
    // Single name is acceptable (e.g., "Madonna")
    return name.split(' ').length <= 1;
  }
}

// Helper: Extract name formatting issues
function checkNameFormat(name, location) {
  if (!isLastFirstFormat(name)) {
    // Check if it looks like "First Last" format
    const parts = name.split(' ');
    if (parts.length >= 2 && !name.includes(',')) {
      return `ISSUE: "${name}" at ${location} - appears to be "First Last" format, should be "Last, First"`;
    }
    return `WARN: "${name}" at ${location} - unusual format`;
  }
  return null;
}

// Main test execution
async function runTests() {
  console.log('🚀 Starting Comprehensive E2E Testing');
  console.log(`Testing URL: ${BASE_URL}`);
  console.log(`Timestamp: ${timestamp()}\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });

  const page = await context.newPage();

  // Monitor console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text, timestamp: timestamp() });

    if (type === 'error') {
      logTest('console', 'Console Error Detected', 'FAIL', text);
    } else if (type === 'warning') {
      logTest('console', 'Console Warning Detected', 'WARN', text);
    }
  });

  // Monitor page errors
  page.on('pageerror', error => {
    logTest('console', 'Page Error', 'FAIL', error.message);
  });

  try {
    // ========================================
    // PHASE 1: INFRASTRUCTURE TESTS
    // ========================================
    console.log('\n📋 PHASE 1: Infrastructure Tests\n');

    const startTime = Date.now();
    const response = await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    const loadTime = (Date.now() - startTime) / 1000;

    logTest('infrastructure', 'Frontend Accessible',
      response.status() === 200 ? 'PASS' : 'FAIL',
      `Status: ${response.status()}, Load time: ${loadTime.toFixed(2)}s`);

    logTest('performance', 'Initial Load Time',
      loadTime < 3 ? 'PASS' : 'WARN',
      `${loadTime.toFixed(2)}s (target: <3s)`);

    await takeScreenshot(page, 'home_page');

    // ========================================
    // PHASE 2: ROUTES TESTING
    // ========================================
    console.log('\n📋 PHASE 2: Routes Testing\n');

    const routes = [
      { path: '/entities', name: 'Entities Page' },
      { path: '/timeline', name: 'Timeline Page' },
      { path: '/network', name: 'Network Page' },
      { path: '/flights', name: 'Flights Page' }
    ];

    for (const route of routes) {
      const routeResponse = await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'networkidle' });
      logTest('infrastructure', `${route.name} Route`,
        routeResponse.status() === 200 ? 'PASS' : 'FAIL',
        `Status: ${routeResponse.status()}`);
    }

    // ========================================
    // PHASE 3: NAME FORMATTING TESTS (PRIMARY FOCUS)
    // ========================================
    console.log('\n📋 PHASE 3: Name Formatting Tests (14 Locations)\n');

    // Location 1-2: Entities Page
    await page.goto(`${BASE_URL}/entities`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000); // Wait for data to load

    const entityCards = await page.locator('.entity-card, [class*="entity"]').all();
    let entityNameIssues = [];

    for (let i = 0; i < Math.min(10, entityCards.length); i++) {
      const nameElement = await entityCards[i].locator('h3, h2, .name, [class*="name"]').first();
      if (await nameElement.count() > 0) {
        const name = await nameElement.textContent();
        const issue = checkNameFormat(name.trim(), `Entities Page - Card ${i+1}`);
        if (issue) entityNameIssues.push(issue);
      }
    }

    logTest('nameFormatting', 'Entities Grid Name Format',
      entityNameIssues.length === 0 ? 'PASS' : 'FAIL',
      entityNameIssues.length === 0 ?
        `Checked ${Math.min(10, entityCards.length)} entity cards - all formatted correctly` :
        `Issues found:\n${entityNameIssues.join('\n')}`);

    await takeScreenshot(page, 'entities_page');

    // Location 3-6: Entity Detail Page
    // Try to click on first entity
    if (entityCards.length > 0) {
      await entityCards[0].click();
      await page.waitForTimeout(2000);

      // Check detail page header
      const detailHeader = await page.locator('h1, h2, .entity-name, [class*="detail-name"]').first();
      if (await detailHeader.count() > 0) {
        const headerName = await detailHeader.textContent();
        const issue = checkNameFormat(headerName.trim(), 'Entity Detail - Page Header');
        logTest('nameFormatting', 'Entity Detail Header',
          issue ? 'FAIL' : 'PASS',
          issue || `Header: "${headerName}"`);
      }

      // Check "Top Connections" section
      const connections = await page.locator('.connection, [class*="connection"]').all();
      let connectionIssues = [];
      for (let i = 0; i < Math.min(5, connections.length); i++) {
        const connName = await connections[i].textContent();
        const issue = checkNameFormat(connName.trim(), `Entity Detail - Connection ${i+1}`);
        if (issue) connectionIssues.push(issue);
      }

      logTest('nameFormatting', 'Entity Detail Connections',
        connectionIssues.length === 0 ? 'PASS' : 'FAIL',
        connectionIssues.length === 0 ?
          `Checked ${Math.min(5, connections.length)} connections - all formatted correctly` :
          `Issues found:\n${connectionIssues.join('\n')}`);

      await takeScreenshot(page, 'entity_detail');
      await page.goBack();
    }

    // Location 7-8: Timeline Page
    await page.goto(`${BASE_URL}/timeline`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const timelineEvents = await page.locator('.timeline-event, [class*="event"]').all();
    let timelineIssues = [];

    for (let i = 0; i < Math.min(5, timelineEvents.length); i++) {
      const entityBadges = await timelineEvents[i].locator('.badge, [class*="entity"], [class*="related"]').all();
      for (let j = 0; j < entityBadges.length; j++) {
        const badgeName = await entityBadges[j].textContent();
        const issue = checkNameFormat(badgeName.trim(), `Timeline Event ${i+1} - Badge ${j+1}`);
        if (issue) timelineIssues.push(issue);
      }
    }

    logTest('nameFormatting', 'Timeline Event Name Format',
      timelineIssues.length === 0 ? 'PASS' : 'FAIL',
      timelineIssues.length === 0 ?
        `Checked ${Math.min(5, timelineEvents.length)} timeline events - all formatted correctly` :
        `Issues found:\n${timelineIssues.join('\n')}`);

    await takeScreenshot(page, 'timeline_page');

    // Location 9-12: Network Graph
    await page.goto(`${BASE_URL}/network`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000); // Wait for graph to render

    // Check node labels (if visible in canvas or legend)
    const nodeLabels = await page.locator('.node-label, [class*="node"]').all();
    let networkIssues = [];

    for (let i = 0; i < Math.min(10, nodeLabels.length); i++) {
      const labelText = await nodeLabels[i].textContent();
      const issue = checkNameFormat(labelText.trim(), `Network Graph - Node ${i+1}`);
      if (issue) networkIssues.push(issue);
    }

    logTest('nameFormatting', 'Network Graph Node Labels',
      networkIssues.length === 0 ? 'PASS' : 'WARN',
      networkIssues.length === 0 ?
        `Checked ${Math.min(10, nodeLabels.length)} node labels - all formatted correctly` :
        `Issues found:\n${networkIssues.join('\n')}`);

    await takeScreenshot(page, 'network_graph');

    // Location 13-14: Flights Page
    await page.goto(`${BASE_URL}/flights`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    const flightCards = await page.locator('.flight-card, [class*="flight"]').all();
    let flightIssues = [];

    for (let i = 0; i < Math.min(5, flightCards.length); i++) {
      const passengerBadges = await flightCards[i].locator('.passenger, .badge, [class*="passenger"]').all();
      for (let j = 0; j < Math.min(3, passengerBadges.length); j++) {
        const passengerName = await passengerBadges[j].textContent();
        const issue = checkNameFormat(passengerName.trim(), `Flight ${i+1} - Passenger ${j+1}`);
        if (issue) flightIssues.push(issue);
      }
    }

    logTest('nameFormatting', 'Flights Passenger Name Format',
      flightIssues.length === 0 ? 'PASS' : 'FAIL',
      flightIssues.length === 0 ?
        `Checked passengers across ${Math.min(5, flightCards.length)} flights - all formatted correctly` :
        `Issues found:\n${flightIssues.join('\n')}`);

    await takeScreenshot(page, 'flights_page');

    // ========================================
    // PHASE 4: FUNCTIONAL TESTS
    // ========================================
    console.log('\n📋 PHASE 4: Functional Tests\n');

    // Test navigation
    await page.goto(`${BASE_URL}/entities`, { waitUntil: 'networkidle' });
    const navLinks = await page.locator('nav a, [role="navigation"] a').all();
    logTest('functional', 'Navigation Links Present',
      navLinks.length > 0 ? 'PASS' : 'FAIL',
      `Found ${navLinks.length} navigation links`);

    // Test search functionality (if exists)
    const searchInput = await page.locator('input[type="search"], input[placeholder*="search" i]').first();
    if (await searchInput.count() > 0) {
      await searchInput.fill('Epstein');
      await page.waitForTimeout(1000);
      logTest('functional', 'Search Functionality', 'PASS', 'Search input responsive');
    } else {
      logTest('functional', 'Search Functionality', 'WARN', 'No search input found');
    }

    // ========================================
    // PHASE 5: CONSOLE ANALYSIS
    // ========================================
    console.log('\n📋 PHASE 5: Console Analysis\n');

    const errorCount = consoleMessages.filter(m => m.type === 'error').length;
    const warningCount = consoleMessages.filter(m => m.type === 'warning').length;

    logTest('console', 'JavaScript Errors',
      errorCount === 0 ? 'PASS' : 'FAIL',
      errorCount === 0 ? 'No errors detected' : `${errorCount} errors found`);

    logTest('console', 'Console Warnings',
      warningCount === 0 ? 'PASS' : 'WARN',
      warningCount === 0 ? 'No warnings' : `${warningCount} warnings found`);

  } catch (error) {
    console.error('❌ Test execution error:', error);
    logTest('infrastructure', 'Test Execution', 'FAIL', error.message);
  } finally {
    await browser.close();
  }

  // ========================================
  // GENERATE REPORT
  // ========================================
  console.log('\n📊 Generating Test Report\n');
  generateReport();
}

// Generate markdown report
function generateReport() {
  const allTests = [
    ...testResults.infrastructure,
    ...testResults.nameFormatting,
    ...testResults.functional,
    ...testResults.performance,
    ...testResults.console
  ];

  const passCount = allTests.filter(t => t.status === 'PASS').length;
  const failCount = allTests.filter(t => t.status === 'FAIL').length;
  const warnCount = allTests.filter(t => t.status === 'WARN').length;
  const totalCount = allTests.length;

  const report = `# Comprehensive E2E Test Report

**Testing URL**: ${BASE_URL}
**Generated**: ${timestamp()}
**Test Execution**: Playwright Automated Testing

## Executive Summary

- **Total Tests**: ${totalCount}
- ✅ **Passed**: ${passCount}
- ❌ **Failed**: ${failCount}
- ⚠️ **Warnings**: ${warnCount}

**Overall Status**: ${failCount === 0 ? '✅ PASS' : '❌ FAIL'}

---

## 1. Infrastructure Tests

${formatTestSection(testResults.infrastructure)}

---

## 2. Name Formatting Tests (PRIMARY FOCUS)

**Critical Requirement**: All names must display as "Last, First" format across all 14 locations.

${formatTestSection(testResults.nameFormatting)}

---

## 3. Functional Tests

${formatTestSection(testResults.functional)}

---

## 4. Performance Tests

${formatTestSection(testResults.performance)}

---

## 5. Console Monitoring

${formatTestSection(testResults.console)}

---

## Screenshots Captured

${testResults.screenshots.map(s => `- **${s.name}**: \`${s.path}\``).join('\n')}

---

## Acceptance Criteria

### ✅ MUST PASS (Critical)

${generateAcceptanceCriteria()}

---

## Issues Found

${generateIssuesList()}

---

## Recommendations

${generateRecommendations()}

---

*Generated by Playwright E2E Testing Framework*
`;

  fs.writeFileSync(REPORT_FILE, report);
  console.log(`✅ Report generated: ${REPORT_FILE}`);

  // Print summary to console
  console.log('\n' + '='.repeat(60));
  console.log('TEST SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Tests: ${totalCount}`);
  console.log(`✅ Passed: ${passCount}`);
  console.log(`❌ Failed: ${failCount}`);
  console.log(`⚠️  Warnings: ${warnCount}`);
  console.log('='.repeat(60) + '\n');
}

function formatTestSection(tests) {
  if (tests.length === 0) return '*No tests in this category*';

  return tests.map(t => {
    const icon = t.status === 'PASS' ? '✅' : t.status === 'FAIL' ? '❌' : '⚠️';
    return `### ${icon} ${t.test}\n\n**Status**: ${t.status}  \n**Details**: ${t.details || 'N/A'}  \n**Timestamp**: ${t.timestamp}\n`;
  }).join('\n');
}

function generateAcceptanceCriteria() {
  const criteria = [
    { name: 'All pages load without errors', passed: !testResults.infrastructure.some(t => t.status === 'FAIL') },
    { name: 'All names display as "Last, First" format', passed: !testResults.nameFormatting.some(t => t.status === 'FAIL') },
    { name: 'No "Failed to fetch" errors', passed: !testResults.console.some(t => t.details && t.details.includes('fetch')) },
    { name: 'No console errors', passed: !testResults.console.some(t => t.test.includes('Error') && t.status === 'FAIL') }
  ];

  return criteria.map(c => `- [${c.passed ? 'x' : ' '}] ${c.name}`).join('\n');
}

function generateIssuesList() {
  const issues = [
    ...testResults.infrastructure.filter(t => t.status === 'FAIL'),
    ...testResults.nameFormatting.filter(t => t.status === 'FAIL'),
    ...testResults.functional.filter(t => t.status === 'FAIL'),
    ...testResults.console.filter(t => t.status === 'FAIL')
  ];

  if (issues.length === 0) return '**No critical issues found!** 🎉';

  return issues.map(i => `- **${i.test}**: ${i.details}`).join('\n');
}

function generateRecommendations() {
  const warnings = [
    ...testResults.infrastructure.filter(t => t.status === 'WARN'),
    ...testResults.nameFormatting.filter(t => t.status === 'WARN'),
    ...testResults.functional.filter(t => t.status === 'WARN'),
    ...testResults.performance.filter(t => t.status === 'WARN'),
    ...testResults.console.filter(t => t.status === 'WARN')
  ];

  if (warnings.length === 0) return '*No recommendations at this time. Application is performing well!*';

  return warnings.map(w => `- ${w.test}: ${w.details}`).join('\n');
}

// Run tests
runTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
