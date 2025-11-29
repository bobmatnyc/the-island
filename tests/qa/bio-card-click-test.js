const { chromium } = require('playwright');

async function testBioCardClick() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  console.log('Testing Bio card click functionality...\n');

  await page.goto('http://localhost:5173/entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein');
  await page.waitForLoadState('networkidle');

  // Take before screenshot
  await page.screenshot({ path: 'tests/qa/screenshots/bio-card-before-click.png', fullPage: true });
  console.log('Screenshot: Before clicking Bio card');

  // Find the Bio card - it should be a clickable container
  // Look for a div or section that contains both "Bio" and "View full biography"
  const bioCard = await page.locator('div, section, article').filter({
    hasText: /Bio.*View full biography/s
  }).first();

  const bioCardExists = await bioCard.count() > 0;
  console.log('Bio card found:', bioCardExists);

  if (bioCardExists) {
    const bioCardText = await bioCard.textContent();
    console.log('Bio card text:', bioCardText.trim());

    // Click on the Bio card
    console.log('\nClicking Bio card...');
    await bioCard.click();
    await page.waitForTimeout(2000); // Wait for navigation or modal

    // Take after screenshot
    await page.screenshot({ path: 'tests/qa/screenshots/bio-card-after-click.png', fullPage: true });
    console.log('Screenshot: After clicking Bio card');

    // Check what happened
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);

    // Look for biography content
    const pageContent = await page.content();

    // Check for modal
    const modals = await page.locator('[role="dialog"], .modal, [class*="modal"]').all();
    console.log('Modals found:', modals.length);

    // Check for biography text
    const bioWords = pageContent.toLowerCase().match(/biography/g);
    console.log('Occurrences of "biography":', bioWords?.length || 0);

    // Look for long text blocks (full biography should be long)
    const textBlocks = await page.locator('p, div[class*="bio"], div[class*="content"]').all();
    console.log('Text blocks found:', textBlocks.length);

    let foundLongText = false;
    for (const block of textBlocks) {
      const text = await block.textContent();
      if (text && text.length > 500) {
        console.log(`\nFound long text block (${text.length} chars):`);
        console.log(text.substring(0, 300) + '...\n');
        foundLongText = true;
        break;
      }
    }

    if (!foundLongText) {
      console.log('No long biography text found');
    }
  }

  console.log('\nTest complete. Browser will stay open for 5 seconds...');
  await page.waitForTimeout(5000);

  await browser.close();
}

testBioCardClick().catch(console.error);
