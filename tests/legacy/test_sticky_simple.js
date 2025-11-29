/**
 * Simple Sticky Header Visual Test
 * Paste this into browser console for instant validation
 */

(function() {
  // Get active view
  const activeView = document.querySelector('.view.active');
  if (!activeView) {
    console.log('❌ No active view found. Click a tab first.');
    return;
  }

  const viewName = activeView.id.replace('-view', '').toUpperCase();
  console.log(`\n🔍 Testing ${viewName} View Layout\n${'='.repeat(50)}`);

  // Get elements
  const header = activeView.querySelector('.sticky-page-header');
  const filterBar = activeView.querySelector('.sticky-filter-bar');
  const content = activeView.querySelector('.page-content');

  if (!header || !filterBar || !content) {
    console.log('❌ Missing required elements');
    return;
  }

  // Get measurements
  const headerHeight = header.offsetHeight;
  const filterTop = parseInt(getComputedStyle(filterBar).top);
  const contentPadding = parseInt(getComputedStyle(content).paddingTop);

  // Check viewport
  const isMobile = window.innerWidth <= 768;
  const expectedTop = isMobile ? 280 : 185;

  // Display results
  console.log(`\n📱 Viewport: ${window.innerWidth}px (${isMobile ? 'MOBILE' : 'DESKTOP'})\n`);

  console.log(`📐 Measurements:`);
  console.log(`  Header height:    ${headerHeight}px`);
  console.log(`  Filter bar top:   ${filterTop}px ${filterTop >= expectedTop - 20 ? '✅' : '❌'} (expected: ${expectedTop}px)`);
  console.log(`  Content padding:  ${contentPadding}px ${contentPadding > 0 ? '✅' : '❌'}`);

  // Check visibility
  const filterRect = filterBar.getBoundingClientRect();
  const headerRect = header.getBoundingClientRect();
  const noOverlap = filterRect.top >= headerRect.bottom - 5;

  console.log(`\n✨ Layout Checks:`);
  console.log(`  Filter below header: ${noOverlap ? '✅' : '❌'}`);
  console.log(`  Content has padding: ${contentPadding > 0 ? '✅' : '❌'}`);
  console.log(`  Sticky positioning:  ${getComputedStyle(filterBar).position === 'sticky' ? '✅' : '❌'}`);

  // Find content container
  const contentContainer = activeView.querySelector('#timeline-events, #entities-list, #documents-list, .entities-grid, .documents-grid');
  if (contentContainer) {
    const contentRect = contentContainer.getBoundingClientRect();
    const isVisible = contentRect.top < window.innerHeight && contentRect.top > filterRect.bottom;
    console.log(`  Content visible:     ${isVisible ? '✅' : '❌'} (top: ${Math.round(contentRect.top)}px)`);
  }

  // Overall result
  const isValid = noOverlap && contentPadding > 0 && Math.abs(filterTop - expectedTop) < 20;
  console.log(`\n${isValid ? '🎉 LAYOUT VALID!' : '⚠️  LAYOUT NEEDS ATTENTION'}`);

  if (!isValid) {
    console.log('\n💡 Troubleshooting:');
    if (!noOverlap) console.log('  - Headers are overlapping');
    if (contentPadding === 0) console.log('  - Content needs padding-top');
    if (Math.abs(filterTop - expectedTop) >= 20) console.log(`  - Filter bar top should be ~${expectedTop}px`);
  }

  console.log(`\n${'='.repeat(50)}\n`);

  return {
    view: viewName,
    valid: isValid,
    measurements: {
      headerHeight,
      filterTop,
      contentPadding,
      expected: expectedTop
    },
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight,
      mobile: isMobile
    }
  };
})();
