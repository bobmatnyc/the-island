import { test, expect } from '@playwright/test';

test.describe('News Article Cards Rendering Verification', () => {
  test('should render news article cards with debug output', async ({ page }) => {
    const consoleMessages: string[] = [];
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    // Capture all console output
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

    // Navigate to Jeffrey Epstein entity page
    console.log('\n=== Navigating to Entity Page ===');
    await page.goto('http://localhost:5173/entities/jeffrey_epstein', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // Wait for page to be fully loaded
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000); // Allow React to render

    console.log('\n=== CONSOLE DEBUG OUTPUT ===');
    const debugLogs = consoleMessages.filter(msg =>
      msg.includes('[EntityDetail]') ||
      msg.includes('Rendering news cards section')
    );

    if (debugLogs.length > 0) {
      debugLogs.forEach(log => console.log(log));
    } else {
      console.log('⚠️ No debug logs found. Checking all console output...');
      consoleMessages.slice(-20).forEach(msg => console.log(msg));
    }

    // Check for specific debug output
    const hasDebugOutput = debugLogs.some(log =>
      log.includes('isArray') ||
      log.includes('length') ||
      log.includes('firstArticle')
    );

    console.log(`\nDebug output present: ${hasDebugOutput ? '✅' : '❌'}`);

    console.log('\n=== DOM INSPECTION: Article Cards ===');

    // Try multiple selectors to find article cards
    const selectors = [
      'article',
      '.article-card',
      '[class*="article"]',
      '[class*="news-card"]',
      '[data-testid*="article"]'
    ];

    let articleCards = [];
    let usedSelector = '';

    for (const selector of selectors) {
      const elements = await page.$$(selector);
      if (elements.length > 0) {
        articleCards = elements;
        usedSelector = selector;
        break;
      }
    }

    console.log(`Article cards found: ${articleCards.length}`);
    console.log(`Using selector: ${usedSelector || 'none'}`);

    // If no cards found, inspect the page structure
    if (articleCards.length === 0) {
      console.log('\n⚠️ No article cards found. Inspecting page structure...');

      // Get all section headings
      const headings = await page.$$('h2, h3');
      console.log(`\nSection headings (${headings.length}):`);
      for (const heading of headings) {
        const text = await heading.textContent();
        console.log(`  - ${text}`);
      }

      // Look for any news-related sections
      const newsSection = await page.$('text=/news|articles/i');
      if (newsSection) {
        const sectionHTML = await newsSection.evaluate(el => el.outerHTML);
        console.log('\nNews section HTML:', sectionHTML.substring(0, 500));
      }

      // Check for badge
      const badge = await page.$('text=/\\d+\\s+articles?/i');
      if (badge) {
        const badgeText = await badge.textContent();
        console.log(`\nBadge found: "${badgeText}"`);
      }
    }

    // If cards found, inspect their content
    if (articleCards.length > 0) {
      console.log('\n=== ARTICLE CARD CONTENT (First 3 Cards) ===');

      for (let i = 0; i < Math.min(3, articleCards.length); i++) {
        const card = articleCards[i];

        // Get text content
        const cardText = await card.textContent();

        // Try to find specific elements
        const title = await card.$('h3, h4, [class*="title"]');
        const publication = await card.$('[class*="publication"], [class*="source"]');
        const date = await card.$('time, [class*="date"]');

        const titleText = title ? await title.textContent() : 'Not found';
        const publicationText = publication ? await publication.textContent() : 'Not found';
        const dateText = date ? await date.textContent() : 'Not found';

        console.log(`\nCard ${i + 1}:`);
        console.log(`  Title: ${titleText?.substring(0, 80)}...`);
        console.log(`  Publication: ${publicationText}`);
        console.log(`  Date: ${dateText}`);
        console.log(`  Has content: ${cardText && cardText.length > 50 ? '✅' : '❌'}`);
      }
    }

    console.log('\n=== BADGE VERIFICATION ===');

    // Look for the articles count badge
    const badgeSelectors = [
      'text=/\\d+\\s+articles?/i',
      '[class*="badge"]',
      '.badge',
      'span[class*="count"]'
    ];

    let badgeFound = false;
    let badgeText = '';

    for (const selector of badgeSelectors) {
      try {
        const badge = await page.$(selector);
        if (badge) {
          const text = await badge.textContent();
          if (text && text.match(/\d+\s+articles?/i)) {
            badgeText = text;
            badgeFound = true;
            break;
          }
        }
      } catch (e) {
        // Continue to next selector
      }
    }

    console.log(`Badge found: ${badgeFound ? '✅' : '❌'}`);
    if (badgeFound) {
      console.log(`Badge text: "${badgeText}"`);
    }

    console.log('\n=== ERROR CHECKING ===');
    console.log(`Console errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log('❌ Errors found:');
      consoleErrors.forEach(err => console.log(`  - ${err}`));
    } else {
      console.log('✅ No console errors');
    }

    console.log(`\nConsole warnings: ${consoleWarnings.length}`);
    if (consoleWarnings.length > 0) {
      console.log('⚠️ Warnings found:');
      consoleWarnings.forEach(warn => console.log(`  - ${warn}`));
    } else {
      console.log('✅ No console warnings');
    }

    console.log('\n=== USER INTERACTION TEST ===');

    if (articleCards.length > 0) {
      // Try to click first article card
      try {
        const firstCard = articleCards[0];
        const isClickable = await firstCard.evaluate(el => {
          const link = el.querySelector('a');
          return link !== null;
        });

        console.log(`First card is clickable: ${isClickable ? '✅' : '❌'}`);

        if (isClickable) {
          // Just verify it's clickable, don't actually navigate
          const link = await firstCard.$('a');
          const href = await link?.getAttribute('href');
          console.log(`First card link: ${href}`);
        }
      } catch (e) {
        console.log('❌ Error testing card interaction:', e.message);
      }
    }

    // Look for "View All" button
    const viewAllButton = await page.$('text=/view all.*articles?/i');
    if (viewAllButton) {
      const buttonText = await viewAllButton.textContent();
      console.log(`View All button found: ✅ ("${buttonText}")`);
    } else {
      console.log('View All button: ❌ Not found');
    }

    console.log('\n=== VERIFICATION SUMMARY ===');
    console.log(`1. Debug console output: ${hasDebugOutput ? '✅' : '❌'}`);
    console.log(`2. Article cards in DOM: ${articleCards.length} ${articleCards.length >= 10 ? '✅' : articleCards.length > 0 ? '⚠️' : '❌'}`);
    console.log(`3. Cards have content: ${articleCards.length > 0 ? '✅' : '❌'}`);
    console.log(`4. No console errors: ${consoleErrors.length === 0 ? '✅' : '❌'}`);
    console.log(`5. Badge displays correctly: ${badgeFound ? '✅' : '❌'}`);

    // Take screenshot for visual verification
    await page.screenshot({
      path: '/Users/masa/Projects/epstein/news_cards_verification.png',
      fullPage: true
    });
    console.log('\n📸 Screenshot saved: news_cards_verification.png');

    // Assertions
    expect(consoleErrors.length, 'Should have no console errors').toBe(0);
    expect(articleCards.length, 'Should have at least some article cards').toBeGreaterThan(0);
  });
});
