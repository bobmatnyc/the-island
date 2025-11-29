const { chromium } = require('playwright');

async function inspectBioDOM() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  console.log('Inspecting bio section DOM structure...\n');

  await page.goto('http://localhost:5173/entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein');
  await page.waitForLoadState('networkidle');

  // Get all text content
  console.log('=== All visible text containing "bio" ===');
  const allText = await page.content();
  const bioMatches = allText.match(/bio[a-z]*/gi);
  if (bioMatches) {
    console.log('Found words:', [...new Set(bioMatches)]);
  }

  // Get all links
  console.log('\n=== All links on page ===');
  const links = await page.locator('a').all();
  for (let i = 0; i < Math.min(20, links.length); i++) {
    const text = await links[i].textContent();
    const href = await links[i].getAttribute('href');
    if (text.trim()) {
      console.log(`${i + 1}. "${text.trim()}" -> ${href}`);
    }
  }

  // Get all buttons
  console.log('\n=== All buttons on page ===');
  const buttons = await page.locator('button').all();
  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].textContent();
    if (text.trim()) {
      console.log(`${i + 1}. "${text.trim()}"`);
    }
  }

  // Look for bio-related elements
  console.log('\n=== Elements with "bio" in class or id ===');
  const bioElements = await page.locator('[class*="bio"], [id*="bio"]').all();
  for (const elem of bioElements) {
    const tagName = await elem.evaluate(el => el.tagName);
    const className = await elem.getAttribute('class');
    const id = await elem.getAttribute('id');
    const text = await elem.textContent();
    console.log(`<${tagName.toLowerCase()} class="${className}" id="${id}">`);
    console.log(`  Text: ${text?.substring(0, 100)}...`);
  }

  // Take screenshot
  await page.screenshot({ path: 'tests/qa/screenshots/bio-dom-inspect.png', fullPage: true });
  console.log('\nScreenshot saved to: tests/qa/screenshots/bio-dom-inspect.png');

  await browser.close();
}

inspectBioDOM().catch(console.error);
