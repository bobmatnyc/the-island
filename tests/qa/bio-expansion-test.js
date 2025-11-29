const { chromium } = require('playwright');

async function testBioExpansion() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  console.log('Testing bio expansion functionality...\n');

  // Test Jeffrey Epstein
  console.log('=== Jeffrey Epstein ===');
  await page.goto('http://localhost:5173/entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein');
  await page.waitForLoadState('networkidle');

  // Find and click "View full biography" link
  const bioLinks = await page.locator('a, button').all();
  let bioLink = null;

  for (const link of bioLinks) {
    const text = await link.textContent();
    if (text && /view full biography/i.test(text)) {
      bioLink = link;
      console.log('Found "View full biography" link');
      break;
    }
  }

  if (bioLink) {
    // Take before screenshot
    await page.screenshot({ path: 'tests/qa/screenshots/bio-before-expand.png' });
    console.log('Screenshot: Before expansion');

    // Click the link
    await bioLink.click();
    await page.waitForTimeout(1000); // Wait for animation

    // Take after screenshot
    await page.screenshot({ path: 'tests/qa/screenshots/bio-after-expand.png' });
    console.log('Screenshot: After expansion');

    // Check if biography content appeared
    const pageContent = await page.content();
    const hasBioContent = pageContent.toLowerCase().includes('biography');
    console.log('Bio content visible:', hasBioContent);

    // Look for bio modal or expanded section
    const modals = await page.locator('[role="dialog"], .modal, .biography-modal').all();
    console.log('Modal elements found:', modals.length);

    const bioSections = await page.locator('.biography-content, .bio-full, .biography-text').all();
    console.log('Biography sections found:', bioSections.length);

    if (bioSections.length > 0) {
      const bioText = await bioSections[0].textContent();
      console.log('Biography text length:', bioText.length);
      console.log('Biography preview:', bioText.substring(0, 200) + '...');
    }
  } else {
    console.log('ERROR: "View full biography" link not found');
  }

  console.log('\n=== Ghislaine Maxwell ===');
  await page.goto('http://localhost:5173/entities/2b3bdb1f-adb2-5050-b437-e16a1fb476e8/ghislaine-maxwell');
  await page.waitForLoadState('networkidle');

  // Repeat for Ghislaine Maxwell
  const bioLinks2 = await page.locator('a, button').all();
  let bioLink2 = null;

  for (const link of bioLinks2) {
    const text = await link.textContent();
    if (text && /view full biography/i.test(text)) {
      bioLink2 = link;
      console.log('Found "View full biography" link');
      break;
    }
  }

  if (bioLink2) {
    await page.screenshot({ path: 'tests/qa/screenshots/bio-maxwell-before-expand.png' });
    console.log('Screenshot: Before expansion');

    await bioLink2.click();
    await page.waitForTimeout(1000);

    await page.screenshot({ path: 'tests/qa/screenshots/bio-maxwell-after-expand.png' });
    console.log('Screenshot: After expansion');

    const bioSections = await page.locator('.biography-content, .bio-full, .biography-text').all();
    console.log('Biography sections found:', bioSections.length);

    if (bioSections.length > 0) {
      const bioText = await bioSections[0].textContent();
      console.log('Biography text length:', bioText.length);
      console.log('Biography preview:', bioText.substring(0, 200) + '...');
    }
  }

  console.log('\nTest complete. Check screenshots in tests/qa/screenshots/');
  await page.waitForTimeout(3000); // Keep browser open to see result

  await browser.close();
}

testBioExpansion().catch(console.error);
