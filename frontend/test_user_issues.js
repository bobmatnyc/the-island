import { chromium } from 'playwright';
import { writeFileSync } from 'fs';

async function testUserIssues() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  // Enable console logging
  const consoleMessages = [];
  page.on('console', msg => {
    console.log(`BROWSER [${msg.type()}]:`, msg.text());
    consoleMessages.push({ type: msg.type(), text: msg.text() });
  });

  page.on('pageerror', err => {
    console.error('PAGE ERROR:', err);
    consoleMessages.push({ type: 'error', text: err.toString() });
  });

  const results = {
    issue1: {},
    issue2: {},
    consoleMessages: []
  };

  try {
    // ISSUE 1: Dashboard Timeline Count
    console.log('\n=== TESTING ISSUE 1: Dashboard Timeline Count ===');
    await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });

    // Wait for React to render stats
    await page.waitForSelector('text=Epstein Archive Dashboard', { timeout: 10000 });
    await page.waitForTimeout(2000); // Give time for API call to complete

    // Take screenshot
    await page.screenshot({ path: 'dashboard_screenshot.png', fullPage: true });
    console.log('✓ Dashboard screenshot saved');

    // Get all stat cards - they are Link components with specific structure
    const statCards = await page.locator('a.rounded-lg.border').all();
    console.log(`Found ${statCards.length} stat cards (Link elements)`);

    const allStatValues = [];
    for (const card of statCards) {
      const valueEl = await card.locator('div.text-2xl').first();
      const titleEl = await card.locator('p.text-sm').first();

      const value = await valueEl.textContent();
      const title = await titleEl.textContent();

      console.log(`Card: "${title}" = "${value}"`);

      allStatValues.push({
        title: title?.trim(),
        value: value?.trim(),
        isTBD: value?.trim() === 'TBD'
      });

      if (title && title.includes('Timeline Events')) {
        results.issue1.timelineCard = {
          title: title.trim(),
          value: value.trim(),
          isTBD: value.trim() === 'TBD',
          expectedValue: '98',
          issue: value.trim() === 'TBD' ? 'CONFIRMED: Shows TBD instead of 98' : 'WORKING: Shows correct value'
        };
      }
    }

    results.issue1.allCards = allStatValues;
    results.issue1.summary = `Found ${statCards.length} stat cards. Timeline Events shows: ${results.issue1.timelineCard?.value || 'NOT FOUND'}`;

    // ISSUE 2: Chat Sidebar Missing
    console.log('\n=== TESTING ISSUE 2: Chat Sidebar ===');
    await page.goto('http://localhost:5173/chat', { waitUntil: 'networkidle' });
    await page.waitForSelector('text=Document Search', { timeout: 10000 });
    await page.waitForTimeout(2000); // Give time for any animations

    // Take screenshot
    await page.screenshot({ path: 'chat_screenshot.png', fullPage: true });
    console.log('✓ Chat screenshot saved');

    // Check sidebar with data-testid
    const sidebar = page.locator('[data-testid="chat-sidebar"]');
    const sidebarExists = await sidebar.count() > 0;
    console.log(`Sidebar element exists: ${sidebarExists}`);

    // Check if sidebar is visible (not hidden by transform)
    let sidebarVisible = false;
    let sidebarStyles = null;

    if (sidebarExists) {
      sidebarVisible = await sidebar.isVisible();
      console.log(`Sidebar is visible: ${sidebarVisible}`);

      // Get computed styles
      const sidebarElement = await sidebar.elementHandle();
      if (sidebarElement) {
        sidebarStyles = await page.evaluate(el => {
          const styles = window.getComputedStyle(el);
          return {
            display: styles.display,
            visibility: styles.visibility,
            width: styles.width,
            transform: styles.transform,
            opacity: styles.opacity,
            position: styles.position,
            left: styles.left
          };
        }, sidebarElement);
        console.log('Sidebar styles:', JSON.stringify(sidebarStyles, null, 2));
      }
    }

    // Check for specific elements
    const searchHistoryText = page.locator('[data-testid="sidebar-title"]');
    const searchHistoryVisible = await searchHistoryText.isVisible().catch(() => false);
    const searchHistoryContent = await searchHistoryText.textContent().catch(() => null);

    const newChatButton = page.locator('[data-testid="new-chat-button"]');
    const newChatVisible = await newChatButton.isVisible().catch(() => false);
    const newChatContent = await newChatButton.textContent().catch(() => null);

    console.log(`Search History text visible: ${searchHistoryVisible} (content: "${searchHistoryContent}")`);
    console.log(`New Chat button visible: ${newChatVisible} (content: "${newChatContent}")`);

    // Check viewport width to determine if we're in mobile vs desktop
    const viewportWidth = page.viewportSize()?.width || 0;
    const isMobile = viewportWidth < 768; // md breakpoint in Tailwind

    // Check if sidebar toggle button exists (mobile only)
    const toggleButton = page.locator('[data-testid="sidebar-toggle"]');
    const toggleVisible = await toggleButton.isVisible().catch(() => false);

    results.issue2 = {
      sidebarExists,
      sidebarVisible,
      sidebarStyles,
      searchHistoryVisible,
      searchHistoryContent,
      newChatVisible,
      newChatContent,
      viewportWidth,
      isMobile,
      toggleButtonVisible: toggleVisible,
      issue: !sidebarVisible ? 'CONFIRMED: Sidebar exists but is NOT VISIBLE' : 'WORKING: Sidebar is visible',
      expectedBehavior: `On desktop (${viewportWidth}px), sidebar should be visible by default`,
      actualBehavior: sidebarVisible ? 'Sidebar is visible' : 'Sidebar is hidden/transformed off-screen'
    };

    // Filter console messages for errors
    const errorMessages = consoleMessages.filter(msg =>
      msg.type === 'error' || msg.text.toLowerCase().includes('error')
    );

    results.consoleMessages = {
      total: consoleMessages.length,
      errors: errorMessages,
      hasErrors: errorMessages.length > 0
    };

    console.log('\n=== RESULTS ===');
    console.log(JSON.stringify(results, null, 2));

    // Write results to file
    writeFileSync('test_results.json', JSON.stringify(results, null, 2));
    console.log('\n✓ Results saved to test_results.json');
    console.log('✓ Screenshots saved: dashboard_screenshot.png, chat_screenshot.png');

    // Summary
    console.log('\n=== SUMMARY ===');
    console.log('Issue 1 (Dashboard Timeline Count):');
    console.log(`  ${results.issue1.timelineCard?.issue || 'Could not verify'}`);
    console.log('\nIssue 2 (Chat Sidebar):');
    console.log(`  ${results.issue2.issue}`);
    console.log(`  Expected: ${results.issue2.expectedBehavior}`);
    console.log(`  Actual: ${results.issue2.actualBehavior}`);

  } catch (error) {
    console.error('Test error:', error);
    results.testError = error.toString();
  } finally {
    console.log('\nClosing browser in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
  }
}

testUserIssues();
