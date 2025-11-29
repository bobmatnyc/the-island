/**
 * Browser Console Verification Script for News Article Cards
 *
 * USAGE:
 * 1. Open http://localhost:5173/entities/jeffrey_epstein in browser
 * 2. Open Developer Tools Console (F12 or ⌘⌥I on Mac)
 * 3. Copy and paste this entire script into the console
 * 4. Press Enter to run
 *
 * This will verify:
 * - Article cards are present in DOM
 * - Cards have proper content
 * - Badge displays correctly
 * - No rendering errors
 */

(function verifyNewsCards() {
  console.log('\n=== NEWS ARTICLE CARDS VERIFICATION ===\n');

  // 1. Check for debug output in recent console logs
  console.log('1️⃣  DEBUG OUTPUT CHECK');
  console.log('   Look for debug messages above showing:');
  console.log('   - isArray: true');
  console.log('   - length: 100');
  console.log('   - firstArticle: {...}');
  console.log('');

  // 2. Count article cards
  console.log('2️⃣  DOM INSPECTION');

  const selectors = [
    'article',
    '.article-card',
    '[class*="article"]',
    '[class*="news-card"]',
    '.card'
  ];

  let articleCards = [];
  let usedSelector = '';

  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
      articleCards = Array.from(elements);
      usedSelector = selector;
      break;
    }
  }

  console.log(`   Selector used: ${usedSelector}`);
  console.log(`   Cards found: ${articleCards.length}`);

  if (articleCards.length >= 10) {
    console.log('   ✅ PASS: Found 10+ article cards');
  } else if (articleCards.length > 0) {
    console.log(`   ⚠️  WARN: Found only ${articleCards.length} cards (expected 10+)`);
  } else {
    console.log('   ❌ FAIL: No article cards found');
  }
  console.log('');

  // 3. Inspect card content
  if (articleCards.length > 0) {
    console.log('3️⃣  CARD CONTENT INSPECTION (First 3 cards)');

    articleCards.slice(0, 3).forEach((card, i) => {
      const title = card.querySelector('h3, h4, [class*="title"], a');
      const publication = card.querySelector('[class*="publication"], [class*="source"]');
      const date = card.querySelector('time, [class*="date"]');
      const excerpt = card.querySelector('p, [class*="excerpt"]');
      const badge = card.querySelector('[class*="badge"], [class*="score"]');

      console.log(`   Card ${i + 1}:`);
      console.log(`     Title: ${title ? '✅ ' + title.textContent.substring(0, 60) + '...' : '❌ Not found'}`);
      console.log(`     Publication: ${publication ? '✅ ' + publication.textContent : '⚠️  Not found'}`);
      console.log(`     Date: ${date ? '✅ ' + date.textContent : '⚠️  Not found'}`);
      console.log(`     Excerpt: ${excerpt ? '✅ Present' : '⚠️  Not found'}`);
      console.log(`     Badge: ${badge ? '✅ Present' : '⚠️  Not found'}`);
      console.log(`     Total text: ${card.textContent.length} chars`);
      console.log('');
    });
  }

  // 4. Check for badge
  console.log('4️⃣  BADGE VERIFICATION');

  const allElements = document.querySelectorAll('span, div, [class*="badge"]');
  let badgeFound = false;
  let badgeText = '';

  for (const el of allElements) {
    if (el.textContent.match(/\d+\s+articles?/i)) {
      badgeFound = true;
      badgeText = el.textContent;
      console.log(`   ✅ Badge found: "${badgeText}"`);
      console.log(`   Badge visible: ${el.offsetParent !== null ? '✅ Yes' : '❌ No'}`);
      break;
    }
  }

  if (!badgeFound) {
    console.log('   ❌ Badge not found');
  }
  console.log('');

  // 5. Check for errors
  console.log('5️⃣  ERROR CHECK');
  console.log('   Check console above for:');
  console.log('   - ❌ Red error messages');
  console.log('   - ⚠️  Yellow warning messages');
  console.log('   - No React rendering errors');
  console.log('');

  // 6. Page structure
  console.log('6️⃣  PAGE STRUCTURE');

  const headings = document.querySelectorAll('h1, h2, h3');
  console.log(`   Total headings: ${headings.length}`);

  const newsHeadings = Array.from(headings).filter(h =>
    h.textContent.toLowerCase().includes('news') ||
    h.textContent.toLowerCase().includes('article')
  );

  if (newsHeadings.length > 0) {
    console.log(`   News-related sections: ${newsHeadings.length}`);
    newsHeadings.forEach(h => {
      console.log(`     - ${h.tagName}: ${h.textContent}`);
    });
  }
  console.log('');

  // 7. Summary
  console.log('=== VERIFICATION SUMMARY ===');

  const checks = {
    'Article cards in DOM': articleCards.length >= 10,
    'Cards have content': articleCards.length > 0 && articleCards[0].textContent.length > 50,
    'Badge displays': badgeFound,
    'Cards are clickable': articleCards.length > 0 && articleCards[0].querySelector('a') !== null
  };

  let passCount = 0;
  for (const [check, passed] of Object.entries(checks)) {
    console.log(`   ${passed ? '✅' : '❌'} ${check}`);
    if (passed) passCount++;
  }

  console.log('');
  console.log(`   Results: ${passCount}/${Object.keys(checks).length} checks passed`);

  if (passCount === Object.keys(checks).length) {
    console.log('   🎉 ALL CHECKS PASSED!');
  } else {
    console.log('   ⚠️  Some checks failed - review above');
  }

  console.log('');
  console.log('=== ADDITIONAL COMMANDS ===');
  console.log('   Get card count:');
  console.log('     document.querySelectorAll("article").length');
  console.log('');
  console.log('   Inspect first card:');
  console.log('     document.querySelector("article")');
  console.log('');
  console.log('   Get all article titles:');
  console.log('     Array.from(document.querySelectorAll("article")).map(a => a.querySelector("h3, h4")?.textContent)');
  console.log('');

  // Return summary for scripting
  return {
    passed: passCount === Object.keys(checks).length,
    cardCount: articleCards.length,
    badgeFound,
    checks
  };
})();
