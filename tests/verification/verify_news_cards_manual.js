/**
 * Manual Browser Verification Script for News Article Cards
 *
 * Usage: node verify_news_cards_manual.js
 *
 * This script uses Puppeteer to:
 * 1. Capture console debug output
 * 2. Count article cards in DOM
 * 3. Inspect card content
 * 4. Check for errors
 * 5. Verify badge display
 */

const puppeteer = require('puppeteer');

async function verifyNewsCards() {
  const browser = await puppeteer.launch({
    headless: false, // Show browser for visual verification
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set viewport
  await page.setViewport({ width: 1920, height: 1080 });

  const consoleMessages = [];
  const consoleErrors = [];
  const consoleWarnings = [];

  // Capture console output
  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();

    if (type === 'error') {
      consoleErrors.push(text);
    } else if (type === 'warning') {
      consoleWarnings.push(text);
    } else {
      consoleMessages.push(text);
    }
  });

  console.log('\n=== NAVIGATING TO ENTITY PAGE ===');
  console.log('URL: http://localhost:5173/entities/jeffrey_epstein\n');

  try {
    await page.goto('http://localhost:5173/entities/jeffrey_epstein', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Wait for React to render
    await page.waitForTimeout(3000);

    console.log('=== CONSOLE DEBUG OUTPUT ===');
    const debugLogs = consoleMessages.filter(msg =>
      msg.includes('[EntityDetail]') ||
      msg.includes('Rendering news cards section') ||
      msg.includes('isArray') ||
      msg.includes('length') ||
      msg.includes('firstArticle')
    );

    if (debugLogs.length > 0) {
      debugLogs.forEach(log => console.log(log));
      console.log('✅ Debug output found\n');
    } else {
      console.log('❌ No debug output found');
      console.log('Recent console messages:');
      consoleMessages.slice(-10).forEach(msg => console.log('  ', msg));
      console.log('');
    }

    console.log('=== DOM INSPECTION: Article Cards ===');

    // Try multiple selectors
    const cardCounts = await page.evaluate(() => {
      const selectors = [
        'article',
        '.article-card',
        '[class*="article"]',
        '[class*="news-card"]',
        '[data-testid*="article"]',
        '.news-article',
        '.card'
      ];

      const results = {};
      for (const selector of selectors) {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          results[selector] = elements.length;
        }
      }
      return results;
    });

    console.log('Cards found by selector:');
    Object.entries(cardCounts).forEach(([selector, count]) => {
      console.log(`  ${selector}: ${count}`);
    });

    // Get detailed info about cards
    const cardDetails = await page.evaluate(() => {
      // Try to find news article cards
      const possibleSelectors = [
        'article',
        '.article-card',
        '[class*="news"]'
      ];

      let cards = [];
      for (const selector of possibleSelectors) {
        const elements = Array.from(document.querySelectorAll(selector));
        if (elements.length > 0) {
          cards = elements;
          break;
        }
      }

      if (cards.length === 0) {
        return { found: false, count: 0 };
      }

      // Get info from first 3 cards
      const cardInfo = cards.slice(0, 3).map(card => {
        const titleElement = card.querySelector('h3, h4, [class*="title"], a');
        const publicationElement = card.querySelector('[class*="publication"], [class*="source"]');
        const dateElement = card.querySelector('time, [class*="date"]');
        const excerptElement = card.querySelector('p, [class*="excerpt"], [class*="description"]');

        return {
          title: titleElement?.textContent?.substring(0, 100) || 'Not found',
          publication: publicationElement?.textContent || 'Not found',
          date: dateElement?.textContent || 'Not found',
          hasExcerpt: !!excerptElement,
          textLength: card.textContent?.length || 0
        };
      });

      return { found: true, count: cards.length, cards: cardInfo };
    });

    if (cardDetails.found) {
      console.log(`\n✅ Found ${cardDetails.count} article cards`);
      console.log('\nFirst 3 cards:');
      cardDetails.cards.forEach((card, i) => {
        console.log(`\nCard ${i + 1}:`);
        console.log(`  Title: ${card.title}`);
        console.log(`  Publication: ${card.publication}`);
        console.log(`  Date: ${card.date}`);
        console.log(`  Has excerpt: ${card.hasExcerpt ? '✅' : '❌'}`);
        console.log(`  Text length: ${card.textLength} chars`);
      });
    } else {
      console.log('\n❌ No article cards found in DOM');
    }

    console.log('\n=== BADGE VERIFICATION ===');

    const badgeInfo = await page.evaluate(() => {
      // Look for badge with article count
      const badges = Array.from(document.querySelectorAll('span, div, [class*="badge"]'));
      const articleBadge = badges.find(el =>
        el.textContent.match(/\d+\s+articles?/i)
      );

      if (articleBadge) {
        return {
          found: true,
          text: articleBadge.textContent,
          visible: articleBadge.offsetParent !== null
        };
      }
      return { found: false };
    });

    if (badgeInfo.found) {
      console.log(`✅ Badge found: "${badgeInfo.text}"`);
      console.log(`Badge visible: ${badgeInfo.visible ? '✅' : '❌'}`);
    } else {
      console.log('❌ Badge not found');
    }

    console.log('\n=== ERROR CHECKING ===');
    console.log(`Console errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('❌ Errors:');
      consoleErrors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✅ No console errors');
    }

    console.log(`\nConsole warnings: ${consoleWarnings.length}`);
    if (consoleWarnings.length > 0) {
      console.log('⚠️ Warnings:');
      consoleWarnings.slice(0, 5).forEach(warn => console.log(`  - ${warn}`));
    } else {
      console.log('✅ No console warnings');
    }

    console.log('\n=== PAGE STRUCTURE ===');

    const pageStructure = await page.evaluate(() => {
      const headings = Array.from(document.querySelectorAll('h1, h2, h3'));
      return headings.map(h => `${h.tagName}: ${h.textContent}`).slice(0, 10);
    });

    console.log('Main headings:');
    pageStructure.forEach(h => console.log(`  ${h}`));

    // Take screenshot
    await page.screenshot({
      path: 'news_cards_verification.png',
      fullPage: true
    });
    console.log('\n📸 Screenshot saved: news_cards_verification.png');

    console.log('\n=== VERIFICATION SUMMARY ===');
    console.log(`1. Debug console output: ${debugLogs.length > 0 ? '✅' : '❌'}`);
    console.log(`2. Article cards found: ${cardDetails.found ? `✅ (${cardDetails.count})` : '❌'}`);
    console.log(`3. Cards have content: ${cardDetails.found && cardDetails.cards[0]?.textLength > 50 ? '✅' : '❌'}`);
    console.log(`4. No console errors: ${consoleErrors.length === 0 ? '✅' : '❌'}`);
    console.log(`5. Badge displays: ${badgeInfo.found ? '✅' : '❌'}`);

    const allPassed = debugLogs.length > 0 &&
                      cardDetails.found &&
                      cardDetails.count >= 10 &&
                      consoleErrors.length === 0 &&
                      badgeInfo.found;

    console.log(`\n${allPassed ? '✅ ALL CHECKS PASSED' : '⚠️ SOME CHECKS FAILED'}`);

    // Keep browser open for manual inspection
    console.log('\n⏸️  Browser left open for manual inspection...');
    console.log('Press Ctrl+C when done.');

    // Wait indefinitely
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Error during verification:', error.message);
    await browser.close();
    process.exit(1);
  }
}

verifyNewsCards().catch(console.error);
