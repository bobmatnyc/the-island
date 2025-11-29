/**
 * Sticky Header Layout Validator
 * Run this in browser console to verify sticky header positioning
 */

(function validateStickyHeaders() {
  console.log('%c🔍 Sticky Header Layout Validator', 'font-size: 16px; font-weight: bold; color: #4A90E2;');
  console.log('═'.repeat(60));

  const views = ['timeline-view', 'entities-view', 'documents-view'];
  const results = [];

  views.forEach(viewId => {
    const view = document.getElementById(viewId);
    if (!view) {
      console.warn(`⚠️  View not found: ${viewId}`);
      return;
    }

    const header = view.querySelector('.sticky-page-header');
    const filterBar = view.querySelector('.sticky-filter-bar');
    const content = view.querySelector('.page-content');

    if (!header || !filterBar || !content) {
      console.warn(`⚠️  Missing elements in ${viewId}`);
      return;
    }

    const headerRect = header.getBoundingClientRect();
    const filterRect = filterBar.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();

    const headerStyles = window.getComputedStyle(header);
    const filterStyles = window.getComputedStyle(filterBar);
    const contentStyles = window.getComputedStyle(content);

    const headerHeight = headerRect.height;
    const filterTop = parseInt(filterStyles.top);
    const contentPaddingTop = parseInt(contentStyles.paddingTop);

    // Validation checks
    const isFilterBelowHeader = filterTop >= (headerHeight - 20); // Allow 20px tolerance
    const hasContentPadding = contentPaddingTop > 0;
    const noOverlap = filterRect.top >= headerRect.bottom - 5; // Allow 5px tolerance

    const viewResult = {
      view: viewId.replace('-view', '').toUpperCase(),
      headerHeight: Math.round(headerHeight),
      filterTop: filterTop,
      contentPadding: contentPaddingTop,
      isValid: isFilterBelowHeader && hasContentPadding && noOverlap,
      checks: {
        filterBelowHeader: isFilterBelowHeader,
        hasContentPadding: hasContentPadding,
        noOverlap: noOverlap
      }
    };

    results.push(viewResult);

    // Log results for this view
    console.log(`\n${viewResult.isValid ? '✅' : '❌'} ${viewResult.view} View:`);
    console.log(`  Header height: ${viewResult.headerHeight}px`);
    console.log(`  Filter bar top: ${viewResult.filterTop}px ${viewResult.checks.filterBelowHeader ? '✅' : '❌'}`);
    console.log(`  Content padding: ${viewResult.contentPadding}px ${viewResult.checks.hasContentPadding ? '✅' : '❌'}`);
    console.log(`  No overlap: ${viewResult.checks.noOverlap ? '✅' : '❌'}`);

    // Visual position check
    if (view.classList.contains('active')) {
      const eventsEl = view.querySelector('#timeline-events, #entities-list, #documents-list');
      if (eventsEl) {
        const eventsRect = eventsEl.getBoundingClientRect();
        const isVisible = eventsRect.top < window.innerHeight && eventsRect.top > filterRect.bottom;
        console.log(`  Content visible: ${isVisible ? '✅' : '❌'} (top: ${Math.round(eventsRect.top)}px)`);
      }
    }
  });

  // Summary
  console.log('\n' + '═'.repeat(60));
  const allValid = results.every(r => r.isValid);
  console.log(`%c${allValid ? '✅ All views valid!' : '❌ Some views need attention'}`,
    `font-size: 14px; font-weight: bold; color: ${allValid ? '#22C55E' : '#EF4444'};`);

  // Desktop vs Mobile detection
  const isMobile = window.innerWidth <= 768;
  console.log(`\n📱 Viewport: ${window.innerWidth}x${window.innerHeight} (${isMobile ? 'MOBILE' : 'DESKTOP'} mode)`);

  if (isMobile) {
    console.log('Expected filter top: ~280px');
  } else {
    console.log('Expected filter top: ~185px');
  }

  console.log('\n💡 Tips:');
  console.log('  - Switch tabs to test each view');
  console.log('  - Resize window to test responsive behavior');
  console.log('  - Scroll to verify sticky positioning works');
  console.log('  - Check browser DevTools Elements panel for visual inspection');

  return {
    results,
    allValid,
    viewport: { width: window.innerWidth, height: window.innerHeight, isMobile }
  };
})();
