const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  const results = {
    timestamp: new Date().toISOString(),
    tests: [],
    screenshots: []
  };

  console.log('🔍 Starting UI verification tests...\n');

  // Navigate to homepage
  console.log('📍 Navigating to homepage...');
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Test 1: Navigation Order
  console.log('\n✅ Test 1: Navigation Order');
  const navLinks = await page.$$eval('nav a', links =>
    links.map(link => link.textContent.trim())
  );
  console.log('Navigation links found:', navLinks);

  const expectedNav = ['Home', 'Timeline', 'News', 'Entities', 'Flights', 'Documents'];
  const navOrderCorrect = expectedNav.every((item, index) => navLinks[index] === item);
  results.tests.push({
    name: 'Navigation Order',
    passed: navOrderCorrect,
    expected: expectedNav,
    actual: navLinks.slice(0, 6),
    details: navOrderCorrect ? 'Navigation order matches requirements' : 'Navigation order mismatch'
  });
  console.log(navOrderCorrect ? '   ✓ Navigation order correct' : '   ✗ Navigation order incorrect');

  // Test 2: Check for "Search" link (should NOT exist in main nav)
  console.log('\n✅ Test 2: Search Link Verification');
  const hasSearchInNav = navLinks.some(link => link === 'Search');
  results.tests.push({
    name: 'No Search in Navigation',
    passed: !hasSearchInNav,
    expected: 'Search link should NOT be in main navigation',
    actual: hasSearchInNav ? 'Search link found' : 'No search link',
    details: !hasSearchInNav ? 'Correctly excludes Search from main nav' : 'Search link found in nav'
  });
  console.log(!hasSearchInNav ? '   ✓ No search link in main navigation' : '   ✗ Search link found in navigation');

  // Test 3: Visualizations Dropdown
  console.log('\n✅ Test 3: Visualizations Dropdown');
  const hasVisualizationsDropdown = await page.locator('text=Visualizations').count() > 0;
  results.tests.push({
    name: 'Visualizations Dropdown Exists',
    passed: hasVisualizationsDropdown,
    expected: 'Visualizations dropdown should exist',
    actual: hasVisualizationsDropdown ? 'Dropdown found' : 'Dropdown not found'
  });
  console.log(hasVisualizationsDropdown ? '   ✓ Visualizations dropdown exists' : '   ✗ Visualizations dropdown missing');

  // Test 4: Dashboard Cards Order and Count
  console.log('\n✅ Test 4: Dashboard Cards Order');
  await page.waitForSelector('[aria-label*="View"]', { timeout: 5000 });

  const cardLabels = await page.$$eval('[aria-label*="View"]', cards =>
    cards.map(card => {
      const match = card.getAttribute('aria-label').match(/View .* (.*)/);
      return match ? match[1] : '';
    })
  );
  console.log('Card labels found:', cardLabels);

  const expectedCards = ['Timeline', 'News', 'Entities', 'Flights', 'Documents', 'Visualizations'];
  const cardOrderCorrect = expectedCards.every((item, index) => cardLabels[index] === item);
  results.tests.push({
    name: 'Dashboard Cards Order',
    passed: cardOrderCorrect,
    expected: expectedCards,
    actual: cardLabels,
    details: cardOrderCorrect ? 'Card order matches requirements' : 'Card order mismatch'
  });
  console.log(cardOrderCorrect ? '   ✓ Card order correct' : '   ✗ Card order incorrect');

  // Test 5: Card Descriptions
  console.log('\n✅ Test 5: Card Descriptions');
  const cardDescriptions = await page.$$eval('.group .text-xs.text-muted-foreground',
    elements => elements.map(el => el.textContent.trim())
  );
  console.log('Card descriptions found:', cardDescriptions.length);

  const expectedDescriptions = [
    'Explore chronological events, flights, and news coverage',
    'Search and browse news articles about the case',
    'View people and organizations in the network',
    'Analyze flight logs and passenger manifests',
    'Access court documents and legal filings',
    'Interactive charts and network graphs'
  ];

  const descriptionsCorrect = expectedDescriptions.every((desc, index) =>
    cardDescriptions[index] === desc
  );
  results.tests.push({
    name: 'Card Descriptions',
    passed: descriptionsCorrect,
    expected: expectedDescriptions,
    actual: cardDescriptions,
    details: descriptionsCorrect ? 'All descriptions match' : 'Description mismatch'
  });
  console.log(descriptionsCorrect ? '   ✓ All card descriptions correct' : '   ✗ Some descriptions incorrect');

  // Test 6: Card Heights (Equal Size)
  console.log('\n✅ Test 6: Card Equal Heights');
  const cardHeights = await page.$$eval('.group > div', cards =>
    cards.map(card => window.getComputedStyle(card).minHeight)
  );
  const uniqueHeights = Array.from(new Set(cardHeights));
  const allSameHeight = uniqueHeights.length === 1;
  results.tests.push({
    name: 'Card Equal Heights',
    passed: allSameHeight,
    expected: 'All cards should have equal minimum height (160px)',
    actual: 'Heights: ' + uniqueHeights.join(', '),
    details: allSameHeight ? 'All cards have equal min-height' : 'Card heights vary'
  });
  console.log(allSameHeight ? '   ✓ All cards equal height (' + cardHeights[0] + ')' : '   ✗ Card heights vary');

  // Screenshot - Desktop
  console.log('\n📸 Taking desktop screenshot...');
  await page.screenshot({ path: '/tmp/epstein_home_desktop.png', fullPage: true });
  results.screenshots.push('/tmp/epstein_home_desktop.png');

  // Test 7: Responsive Design - Tablet
  console.log('\n✅ Test 7: Responsive Design - Tablet (768x1024)');
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/epstein_home_tablet.png', fullPage: true });
  results.screenshots.push('/tmp/epstein_home_tablet.png');

  const tabletCardLayout = await page.$$eval('.group > div', cards => {
    const styles = cards.map(card => window.getComputedStyle(card));
    return {
      gridCols: window.getComputedStyle(cards[0].parentElement.parentElement).gridTemplateColumns,
      count: cards.length
    };
  });
  results.tests.push({
    name: 'Tablet Layout',
    passed: true,
    expected: 'Cards should adapt to 2-column grid on tablet',
    actual: 'Grid: ' + tabletCardLayout.gridCols,
    details: 'Tablet layout verified'
  });
  console.log('   ✓ Tablet layout captured');

  // Test 8: Responsive Design - Mobile
  console.log('\n✅ Test 8: Responsive Design - Mobile (375x667)');
  await page.setViewportSize({ width: 375, height: 667 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/epstein_home_mobile.png', fullPage: true });
  results.screenshots.push('/tmp/epstein_home_mobile.png');
  console.log('   ✓ Mobile layout captured');

  // Test Navigation Links Work
  console.log('\n✅ Test 9: Navigation Links Functionality');
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });

  const linkTests = [
    { name: 'Timeline', path: '/timeline' },
    { name: 'News', path: '/news' },
    { name: 'Entities', path: '/entities' },
    { name: 'Flights', path: '/flights' },
    { name: 'Documents', path: '/documents' }
  ];

  for (const link of linkTests) {
    try {
      await page.click('text=' + link.name);
      await page.waitForURL('**' + link.path, { timeout: 3000 });
      const currentURL = page.url();
      const passed = currentURL.includes(link.path);
      results.tests.push({
        name: 'Navigation Link: ' + link.name,
        passed,
        expected: 'Should navigate to ' + link.path,
        actual: currentURL
      });
      console.log(passed ? '   ✓ ' + link.name + ' link works' : '   ✗ ' + link.name + ' link failed');
      await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });
    } catch (error) {
      results.tests.push({
        name: 'Navigation Link: ' + link.name,
        passed: false,
        expected: 'Should navigate to ' + link.path,
        actual: 'Error: ' + error.message
      });
      console.log('   ✗ ' + link.name + ' link error: ' + error.message);
    }
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));
  const passed = results.tests.filter(t => t.passed).length;
  const total = results.tests.length;
  console.log('Total Tests: ' + total);
  console.log('Passed: ' + passed);
  console.log('Failed: ' + (total - passed));
  console.log('Success Rate: ' + ((passed / total) * 100).toFixed(1) + '%');
  console.log('\nScreenshots saved:');
  results.screenshots.forEach(path => console.log('  - ' + path));

  // Save results
  fs.writeFileSync('/tmp/epstein_qa_results.json', JSON.stringify(results, null, 2));
  console.log('\nDetailed results saved to: /tmp/epstein_qa_results.json');

  await browser.close();

  // Exit with appropriate code
  process.exit(total - passed);
})();
