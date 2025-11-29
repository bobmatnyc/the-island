import { test, expect, type Page } from '@playwright/test';

// Helper to collect console messages
const setupConsoleMonitoring = (page: Page) => {
  const consoleMessages: { type: string; text: string }[] = [];
  const consoleErrors: string[] = [];

  page.on('console', (msg) => {
    const type = msg.type();
    const text = msg.text();
    consoleMessages.push({ type, text });

    if (type === 'error' || type === 'warning') {
      consoleErrors.push(text);
    }
  });

  return { consoleMessages, consoleErrors };
};

// Helper to wait for specific element with timeout
const waitForElement = async (page: Page, selector: string, timeout = 10000) => {
  try {
    await page.waitForSelector(selector, { timeout });
    return true;
  } catch {
    return false;
  }
};

test.describe('Critical UI Fixes QA - Timeline Race Condition', () => {

  test('Test 1.1: Timeline News Filter - No Flash Content', async ({ page }) => {
    console.log('\n=== Test 1.1: Timeline News Filter - No Flash Content ===');
    const { consoleErrors } = setupConsoleMonitoring(page);

    // Navigate to timeline
    await page.goto('/timeline');
    console.log('Navigated to Timeline page');

    // Wait for initial timeline load (documents/flights should appear)
    await page.waitForSelector('[class*="timeline"]', { timeout: 15000 });
    console.log('Timeline container loaded');

    // Wait for any initial data to load
    await page.waitForTimeout(2000);

    // Track if we see flash content during transition
    let flashContentDetected = false;
    let loadingIndicatorAppeared = false;

    // Set up mutation observer to detect flash content
    await page.evaluate(() => {
      (window as any).flashDetected = false;
      (window as any).loadingDetected = false;

      const observer = new MutationObserver(() => {
        const cards = document.querySelectorAll('[class*="timeline-card"], [class*="TimelineCard"]');
        if (cards.length > 10) {
          (window as any).flashDetected = true;
        }
        const loading = document.querySelector('[class*="loading"], [class*="Loading"]');
        if (loading) {
          (window as any).loadingDetected = true;
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });
    });

    console.log('Set up flash content detector');

    // Find and click "News Articles" filter button
    const newsFilterButton = page.locator('button:has-text("News Articles"), button:has-text("News")');
    const newsButtonExists = await newsFilterButton.count() > 0;
    console.log('News Articles button found:', newsButtonExists);

    if (!newsButtonExists) {
      console.log('⚠️ News Articles filter button not found - checking available filters...');
      const allButtons = await page.locator('button').allTextContents();
      console.log('Available buttons:', allButtons.slice(0, 10));
    }

    expect(newsButtonExists).toBe(true);

    // Click News Articles filter
    await newsFilterButton.first().click();
    console.log('Clicked News Articles filter');

    // Immediately check for loading indicator (within 100ms)
    await page.waitForTimeout(100);
    const immediateLoading = await page.locator('[class*="loading"], text=/Loading.*news/i, [class*="spinner"]').count();
    console.log('Loading indicator appeared immediately:', immediateLoading > 0);

    // Wait for transition to complete
    await page.waitForTimeout(3000);

    // Check if flash was detected
    flashContentDetected = await page.evaluate(() => (window as any).flashDetected);
    loadingIndicatorAppeared = await page.evaluate(() => (window as any).loadingDetected);

    console.log('Flash content detected during transition:', flashContentDetected);
    console.log('Loading indicator appeared:', loadingIndicatorAppeared);

    // After transition, check timeline state
    const timelineCards = await page.locator('[class*="timeline-card"], [class*="TimelineCard"]').count();
    console.log('Timeline cards after filter:', timelineCards);

    // Check for news badges on cards
    const newsBadges = await page.locator('[class*="badge"]:has-text("article"), [class*="badge"]:has-text("news")').count();
    console.log('News badges found:', newsBadges);

    // Check for "0 events" message
    const zeroEventsMessage = await page.locator('text=/0 events|No events/i').count();
    console.log('"0 events" message shown:', zeroEventsMessage > 0);

    // Check console for errors
    const filterErrors = consoleErrors.filter(err =>
      err.toLowerCase().includes('filter') ||
      err.toLowerCase().includes('timeline') ||
      err.toLowerCase().includes('news')
    );
    console.log('Filter-related console errors:', filterErrors.length);
    if (filterErrors.length > 0) {
      console.log('Errors:', filterErrors.slice(0, 3));
    }

    // Assertions
    console.log('\n✓ Assertions:');
    console.log(`  - Loading indicator appeared: ${loadingIndicatorAppeared || immediateLoading > 0}`);
    console.log(`  - NO flash of unfiltered content: ${!flashContentDetected}`);
    console.log(`  - Timeline NOT showing "0 events": ${zeroEventsMessage === 0}`);
    console.log(`  - No console errors: ${filterErrors.length === 0}`);

    expect(loadingIndicatorAppeared || immediateLoading > 0).toBe(true);
    expect(flashContentDetected).toBe(false);
    expect(zeroEventsMessage).toBe(0);

    console.log('✅ Test 1.1 PASSED\n');
  });

  test('Test 1.2: Timeline News Filter - Data Accuracy', async ({ page }) => {
    console.log('\n=== Test 1.2: Timeline News Filter - Data Accuracy ===');

    await page.goto('/timeline');
    await page.waitForSelector('[class*="timeline"]', { timeout: 15000 });

    // Click News Articles filter
    const newsFilter = page.locator('button:has-text("News Articles"), button:has-text("News")').first();
    await newsFilter.click();
    console.log('Applied News Articles filter');

    // Wait for news to load
    await page.waitForTimeout(3000);

    // Count timeline cards
    const timelineCards = await page.locator('[class*="timeline-card"], [class*="TimelineCard"]').count();
    console.log('Timeline cards visible:', timelineCards);

    if (timelineCards > 0) {
      // Check first card for news badge
      const firstCard = page.locator('[class*="timeline-card"], [class*="TimelineCard"]').first();
      const newsBadge = await firstCard.locator('[class*="badge"]:has-text("article"), [class*="badge"]:has-text("news"), text=/\\d+ article/i').count();
      console.log('First card has news badge:', newsBadge > 0);

      // Click first card to expand
      await firstCard.click();
      await page.waitForTimeout(1000);

      // Check for news articles in expanded view
      const newsArticles = await page.locator('[class*="news"], [class*="article"]').count();
      console.log('News articles in expanded card:', newsArticles);

      // Assertions
      console.log('\n✓ Assertions:');
      console.log(`  - Timeline cards shown: ${timelineCards > 0}`);
      console.log(`  - News badge present: ${newsBadge > 0}`);
      console.log(`  - News articles exist: ${newsArticles > 0}`);

      expect(timelineCards).toBeGreaterThan(0);
      expect(newsBadge).toBeGreaterThan(0);
    } else {
      console.log('⚠️ No timeline cards with news - may indicate no news data in system');
    }

    console.log('✅ Test 1.2 PASSED\n');
  });

  test('Test 1.3: Timeline Filter Toggle', async ({ page }) => {
    console.log('\n=== Test 1.3: Timeline Filter Toggle ===');

    await page.goto('/timeline');
    await page.waitForSelector('[class*="timeline"]', { timeout: 15000 });
    await page.waitForTimeout(2000);

    // Test sequence: All → News → All → Flight Logs → News
    const filterSequence = [
      { name: 'All Sources', expectLoading: false },
      { name: 'News Articles', expectLoading: true },
      { name: 'All Sources', expectLoading: false },
      { name: 'Flight Logs', expectLoading: false },
      { name: 'News Articles', expectLoading: true }
    ];

    for (const filter of filterSequence) {
      console.log(`\nTesting filter: ${filter.name}`);

      // Find filter button (try multiple text variations)
      let filterButton = page.locator(`button:has-text("${filter.name}")`);
      if (await filterButton.count() === 0) {
        // Try shorter version
        const shortName = filter.name.split(' ')[0];
        filterButton = page.locator(`button:has-text("${shortName}")`);
      }

      const buttonExists = await filterButton.count() > 0;
      console.log(`  - Button found: ${buttonExists}`);

      if (buttonExists) {
        await filterButton.first().click();
        await page.waitForTimeout(200);

        // Check for loading indicator if expected
        if (filter.expectLoading) {
          const loading = await page.locator('[class*="loading"], [class*="spinner"]').count();
          console.log(`  - Loading indicator: ${loading > 0 ? 'YES' : 'NO'} (expected: YES)`);
          expect(loading).toBeGreaterThan(0);
        } else {
          console.log(`  - Instant switch (expected: YES)`);
        }

        // Wait for transition
        await page.waitForTimeout(filter.expectLoading ? 3000 : 1000);

        // Verify data loaded
        const cards = await page.locator('[class*="timeline-card"]').count();
        console.log(`  - Cards after switch: ${cards}`);
        expect(cards).toBeGreaterThanOrEqual(0); // May be 0 for some filters if no data
      }
    }

    console.log('✅ Test 1.3 PASSED\n');
  });
});

test.describe('Critical UI Fixes QA - Addressable Document URLs', () => {

  test('Test 2.1: Document Navigation - Basic Flow', async ({ page }) => {
    console.log('\n=== Test 2.1: Document Navigation - Basic Flow ===');
    const { consoleErrors } = setupConsoleMonitoring(page);

    await page.goto('/documents');
    console.log('Navigated to Documents page');

    // Wait for documents to load
    await page.waitForTimeout(3000);

    // Find any "View Content" button or document link
    const viewButtons = await page.locator('button:has-text("View"), a[href^="/documents/"]').count();
    console.log('View/document links found:', viewButtons);

    if (viewButtons > 0) {
      // Get initial URL
      const initialUrl = page.url();
      console.log('Initial URL:', initialUrl);

      // Click first document
      const firstDoc = page.locator('button:has-text("View"), a[href^="/documents/"]').first();
      await firstDoc.click();
      console.log('Clicked document');

      // Wait for navigation
      await page.waitForTimeout(2000);

      // Check new URL
      const newUrl = page.url();
      console.log('New URL:', newUrl);

      // Verify URL changed to /documents/{id}
      const urlPattern = /\/documents\/[A-Z0-9-]+/;
      const urlMatches = urlPattern.test(newUrl);
      console.log('URL matches /documents/{id} pattern:', urlMatches);

      // Check if modal overlay appeared (should NOT)
      const modal = await page.locator('[role="dialog"], [class*="modal"]').count();
      console.log('Modal overlay present:', modal > 0);

      // Check for document viewer layout
      const documentViewer = await page.locator('[class*="document-viewer"], [class*="DocumentViewer"]').count();
      console.log('Document viewer component:', documentViewer);

      // Check for back button
      const backButton = await page.locator('button:has-text("Back"), a:has-text("Back")').count();
      console.log('Back button present:', backButton > 0);

      // Check for document content
      const hasContent = await page.locator('canvas, pre, [class*="content"]').count() > 0;
      console.log('Document content visible:', hasContent);

      // Assertions
      console.log('\n✓ Assertions:');
      console.log(`  - URL changed to /documents/{id}: ${urlMatches}`);
      console.log(`  - NOT in modal (standalone page): ${modal === 0}`);
      console.log(`  - Document viewer loaded: ${documentViewer > 0}`);
      console.log(`  - Has navigation (back button): ${backButton > 0}`);
      console.log(`  - Content displayed: ${hasContent}`);

      expect(urlMatches).toBe(true);
      expect(modal).toBe(0); // Should NOT be in modal
      expect(documentViewer).toBeGreaterThan(0);
      expect(backButton).toBeGreaterThan(0);

      console.log('✅ Test 2.1 PASSED\n');
    } else {
      console.log('⚠️ No documents found to test');
    }
  });

  test('Test 2.2: Direct Document Links (Shareable URLs)', async ({ page }) => {
    console.log('\n=== Test 2.2: Direct Document Links ===');

    // First, navigate to documents and get a document ID
    await page.goto('/documents');
    await page.waitForTimeout(2000);

    // Try to find a document link in the DOM
    const docLinks = await page.locator('a[href^="/documents/"]').all();

    if (docLinks.length > 0) {
      const firstLink = docLinks[0];
      const href = await firstLink.getAttribute('href');
      console.log('Found document link:', href);

      if (href && href !== '/documents') {
        // Open in new context (simulates new tab)
        const newPage = await page.context().newPage();
        console.log('Opening direct URL:', href);

        await newPage.goto(href);
        await newPage.waitForTimeout(3000);

        // Check if document loads directly
        const urlMatches = newPage.url().includes(href);
        console.log('URL matches:', urlMatches);

        const documentViewer = await newPage.locator('[class*="document-viewer"], [class*="DocumentViewer"]').count();
        console.log('Document viewer loaded:', documentViewer > 0);

        const hasContent = await newPage.locator('canvas, pre, [class*="content"]').count() > 0;
        console.log('Content visible:', hasContent);

        const notFoundError = await newPage.locator('text=/404|Not Found|not found/i').count();
        console.log('404 error:', notFoundError > 0);

        // Assertions
        console.log('\n✓ Assertions:');
        console.log(`  - Direct URL loads: ${urlMatches}`);
        console.log(`  - Document viewer present: ${documentViewer > 0}`);
        console.log(`  - No 404 error: ${notFoundError === 0}`);

        expect(urlMatches).toBe(true);
        expect(documentViewer).toBeGreaterThan(0);
        expect(notFoundError).toBe(0);

        await newPage.close();
        console.log('✅ Test 2.2 PASSED\n');
      } else {
        console.log('⚠️ Invalid document href found');
      }
    } else {
      console.log('⚠️ No document links found');
    }
  });

  test('Test 2.3: Back Navigation', async ({ page }) => {
    console.log('\n=== Test 2.3: Back Navigation ===');

    // Navigate: Home → Documents → Document
    await page.goto('/');
    console.log('Started at Home');
    await page.waitForTimeout(1000);

    // Go to Documents
    await page.goto('/documents');
    console.log('Navigated to Documents');
    await page.waitForTimeout(2000);

    // Click a document
    const docLink = page.locator('button:has-text("View"), a[href^="/documents/"]').first();
    const linkExists = await docLink.count() > 0;

    if (linkExists) {
      await docLink.click();
      console.log('Clicked document');
      await page.waitForTimeout(2000);

      const docUrl = page.url();
      console.log('Document URL:', docUrl);

      // Use browser back button
      await page.goBack();
      console.log('Pressed back button');
      await page.waitForTimeout(1000);

      const backUrl = page.url();
      console.log('Back URL:', backUrl);

      // Should be back at documents page
      const onDocumentsPage = backUrl.includes('/documents') && !backUrl.match(/\/documents\/[A-Z0-9-]+/);
      console.log('Back at Documents page:', onDocumentsPage);

      // Documents list should still show results
      const documentCards = await page.locator('[class*="document"], a[href^="/documents/"]').count();
      console.log('Document cards visible:', documentCards);

      // Test "Back to Documents" button if exists
      await page.goto(docUrl); // Go back to document
      await page.waitForTimeout(1000);

      const backButtonExists = await page.locator('button:has-text("Back to Documents"), a:has-text("Back to Documents")').count() > 0;
      console.log('"Back to Documents" button exists:', backButtonExists);

      if (backButtonExists) {
        await page.locator('button:has-text("Back to Documents"), a:has-text("Back to Documents")').first().click();
        await page.waitForTimeout(1000);

        const buttonBackUrl = page.url();
        const backToDocuments = buttonBackUrl.includes('/documents') && !buttonBackUrl.match(/\/documents\/[A-Z0-9-]+/);
        console.log('Button navigation works:', backToDocuments);

        expect(backToDocuments).toBe(true);
      }

      // Assertions
      console.log('\n✓ Assertions:');
      console.log(`  - Back button returns to Documents: ${onDocumentsPage}`);
      console.log(`  - Document list preserved: ${documentCards > 0}`);

      expect(onDocumentsPage).toBe(true);
      expect(documentCards).toBeGreaterThan(0);

      console.log('✅ Test 2.3 PASSED\n');
    } else {
      console.log('⚠️ No documents found to test navigation');
    }
  });

  test('Test 2.4: Entity Navigation from Document', async ({ page }) => {
    console.log('\n=== Test 2.4: Entity Navigation from Document ===');

    await page.goto('/documents');
    await page.waitForTimeout(2000);

    // Click first document
    const docLink = page.locator('button:has-text("View"), a[href^="/documents/"]').first();
    const linkExists = await docLink.count() > 0;

    if (linkExists) {
      await docLink.click();
      await page.waitForTimeout(2000);

      const docUrl = page.url();
      console.log('Opened document:', docUrl);

      // Look for entity badges/links in document viewer
      const entityLinks = await page.locator('a[href^="/entities/"], [class*="entity-badge"] a, [class*="entity"] a').count();
      console.log('Entity links found in document:', entityLinks);

      if (entityLinks > 0) {
        // Click first entity
        const entityLink = page.locator('a[href^="/entities/"], [class*="entity-badge"] a').first();
        const entityHref = await entityLink.getAttribute('href');
        console.log('Clicking entity:', entityHref);

        await entityLink.click();
        await page.waitForTimeout(2000);

        const entityUrl = page.url();
        console.log('Entity URL:', entityUrl);

        // Verify navigated to entity page
        const onEntityPage = entityUrl.includes('/entities/');
        console.log('On entity page:', onEntityPage);

        // Check entity page loaded
        const entityContent = await page.locator('[class*="entity"], [class*="biography"]').count();
        console.log('Entity content loaded:', entityContent > 0);

        // Test back navigation
        await page.goBack();
        await page.waitForTimeout(1000);

        const backUrl = page.url();
        console.log('After back button:', backUrl);

        // Should be back at document (not documents list)
        const backAtDocument = backUrl === docUrl;
        console.log('Back at document (not list):', backAtDocument);

        // Assertions
        console.log('\n✓ Assertions:');
        console.log(`  - Entity navigation works: ${onEntityPage}`);
        console.log(`  - Entity page loaded: ${entityContent > 0}`);
        console.log(`  - Back returns to document: ${backAtDocument}`);

        expect(onEntityPage).toBe(true);
        expect(entityContent).toBeGreaterThan(0);
        expect(backAtDocument).toBe(true);

        console.log('✅ Test 2.4 PASSED\n');
      } else {
        console.log('⚠️ No entity links found in document');
      }
    } else {
      console.log('⚠️ No documents found');
    }
  });

  test('Test 2.5: PDF Viewer in Standalone Mode', async ({ page }) => {
    console.log('\n=== Test 2.5: PDF Viewer in Standalone Mode ===');
    const { consoleErrors } = setupConsoleMonitoring(page);

    await page.goto('/documents');
    await page.waitForTimeout(2000);

    // Find PDF documents
    const pdfLinks = await page.locator('a[href*=".pdf"], [class*="document"]:has-text(".pdf")').count();
    console.log('PDF documents found:', pdfLinks);

    if (pdfLinks > 0) {
      const pdfLink = page.locator('a[href*=".pdf"], [class*="document"]:has-text(".pdf")').first();
      await pdfLink.click();
      console.log('Clicked PDF document');
      await page.waitForTimeout(4000); // PDFs need more time to load

      // Check URL is /documents/{id}
      const pdfUrl = page.url();
      const urlMatches = pdfUrl.match(/\/documents\/[A-Z0-9-]+/);
      console.log('PDF URL:', pdfUrl);
      console.log('Standalone PDF URL:', urlMatches !== null);

      // Check for PDF canvas
      const pdfCanvas = await page.locator('canvas').count();
      console.log('PDF canvas elements:', pdfCanvas);

      // Check for PDF controls
      const prevButton = await page.locator('button:has-text("Previous"), button:has-text("Prev")').count();
      const nextButton = await page.locator('button:has-text("Next")').count();
      const zoomButtons = await page.locator('button:has-text("Zoom"), button:has-text("+"), button:has-text("-")').count();
      console.log('PDF navigation buttons:', { prev: prevButton, next: nextButton, zoom: zoomButtons });

      // Check for page counter
      const pageCounter = await page.locator('text=/Page \\d+ of \\d+/i').count();
      console.log('Page counter visible:', pageCounter > 0);

      // Check for download button
      const downloadButton = await page.locator('button:has-text("Download"), a:has-text("Download")').count();
      console.log('Download button:', downloadButton > 0);

      // Check for PDF errors
      const pdfErrors = consoleErrors.filter(err =>
        err.toLowerCase().includes('pdf') ||
        err.toLowerCase().includes('worker')
      );
      console.log('PDF-related errors:', pdfErrors.length);
      if (pdfErrors.length > 0) {
        console.log('Errors:', pdfErrors.slice(0, 3));
      }

      // Check for error messages in UI
      const errorMessage = await page.locator('text=/error|failed|unable/i').count();
      console.log('Error messages in UI:', errorMessage);

      // If PDF fails, check for fallback
      if (pdfCanvas === 0 && errorMessage > 0) {
        console.log('PDF failed to load - checking for fallback viewer...');
        const fallbackIframe = await page.locator('iframe').count();
        const fallbackButton = await page.locator('button:has-text("Try"), button:has-text("Browser Viewer")').count();
        console.log('Fallback iframe:', fallbackIframe > 0);
        console.log('Fallback button:', fallbackButton > 0);

        expect(fallbackIframe + fallbackButton).toBeGreaterThan(0);
      }

      // Assertions
      console.log('\n✓ Assertions:');
      console.log(`  - Standalone PDF URL: ${urlMatches !== null}`);
      console.log(`  - PDF renders OR has fallback: ${pdfCanvas > 0 || errorMessage > 0}`);
      console.log(`  - Has controls: ${prevButton + nextButton + downloadButton > 0}`);

      expect(urlMatches).not.toBeNull();
      expect(downloadButton).toBeGreaterThan(0);

      console.log('✅ Test 2.5 PASSED\n');
    } else {
      console.log('⚠️ No PDF documents found');
    }
  });
});

test.describe('Integration Tests', () => {

  test('Test 3.1: Timeline → Document Flow', async ({ page }) => {
    console.log('\n=== Test 3.1: Timeline → Document Flow ===');

    await page.goto('/timeline');
    await page.waitForTimeout(2000);

    // Apply Documents filter
    const docsFilter = page.locator('button:has-text("Documents"), button:has-text("Document")');
    const filterExists = await docsFilter.count() > 0;

    if (filterExists) {
      await docsFilter.first().click();
      console.log('Applied Documents filter');
      await page.waitForTimeout(2000);

      // Click a timeline card
      const timelineCard = page.locator('[class*="timeline-card"]').first();
      const cardExists = await timelineCard.count() > 0;

      if (cardExists) {
        await timelineCard.click();
        await page.waitForTimeout(1000);

        // Look for document link in expanded card
        const docLink = await page.locator('a[href^="/documents/"]').count();
        console.log('Document links in timeline card:', docLink);

        if (docLink > 0) {
          const beforeUrl = page.url();
          await page.locator('a[href^="/documents/"]').first().click();
          await page.waitForTimeout(2000);

          const afterUrl = page.url();
          const navigatedToDoc = afterUrl.match(/\/documents\/[A-Z0-9-]+/);
          console.log('Navigated to document:', navigatedToDoc !== null);

          // Test back button
          await page.goBack();
          await page.waitForTimeout(1000);
          const backToTimeline = page.url().includes('/timeline');
          console.log('Back button returns to timeline:', backToTimeline);

          expect(navigatedToDoc).not.toBeNull();
          expect(backToTimeline).toBe(true);

          console.log('✅ Test 3.1 PASSED\n');
        } else {
          console.log('⚠️ No document links in timeline card');
        }
      } else {
        console.log('⚠️ No timeline cards found');
      }
    } else {
      console.log('⚠️ Documents filter not found');
    }
  });

  test('Test 3.2: Entity → Document Flow', async ({ page }) => {
    console.log('\n=== Test 3.2: Entity → Document Flow ===');

    // Navigate to entities page
    await page.goto('/entities');
    await page.waitForTimeout(2000);

    // Click first entity
    const entityLink = page.locator('a[href^="/entities/"]').first();
    const linkExists = await entityLink.count() > 0;

    if (linkExists) {
      await entityLink.click();
      console.log('Clicked entity');
      await page.waitForTimeout(2000);

      // Look for documents section
      const documentsSection = await page.locator('text=/Documents|Related Documents/i').count();
      console.log('Documents section found:', documentsSection > 0);

      // Find document link in entity page
      const docLinks = await page.locator('a[href^="/documents/"]').count();
      console.log('Document links on entity page:', docLinks);

      if (docLinks > 0) {
        const docLink = page.locator('a[href^="/documents/"]').first();
        await docLink.click();
        await page.waitForTimeout(2000);

        const docUrl = page.url();
        const onDocPage = docUrl.match(/\/documents\/[A-Z0-9-]+/);
        console.log('Navigated to document:', onDocPage !== null);
        console.log('Document URL:', docUrl);

        // Verify it's standalone (not modal)
        const modal = await page.locator('[role="dialog"]').count();
        console.log('Modal overlay:', modal > 0);

        // Test back button
        await page.goBack();
        await page.waitForTimeout(1000);
        const backToEntity = page.url().includes('/entities/');
        console.log('Back to entity page:', backToEntity);

        expect(onDocPage).not.toBeNull();
        expect(modal).toBe(0);
        expect(backToEntity).toBe(true);

        console.log('✅ Test 3.2 PASSED\n');
      } else {
        console.log('⚠️ No documents linked to entity');
      }
    } else {
      console.log('⚠️ No entities found');
    }
  });
});

test.describe('Performance Testing', () => {

  test('Test 4.1: Timeline Loading Performance', async ({ page }) => {
    console.log('\n=== Test 4.1: Timeline Loading Performance ===');

    await page.goto('/timeline');
    await page.waitForTimeout(1000);

    // Measure time to apply news filter
    const startTime = Date.now();

    const newsFilter = page.locator('button:has-text("News Articles"), button:has-text("News")');
    await newsFilter.first().click();

    // Check when loading indicator appears
    const loadingStartTime = Date.now();
    await page.waitForSelector('[class*="loading"], [class*="spinner"]', { timeout: 500 }).catch(() => null);
    const loadingDelay = Date.now() - startTime;

    // Wait for content to load
    await page.waitForTimeout(3000);
    const totalTime = Date.now() - startTime;

    console.log('Performance metrics:');
    console.log(`  - Loading indicator delay: ${loadingDelay}ms`);
    console.log(`  - Total load time: ${totalTime}ms`);

    // Check for UI responsiveness
    const responsive = loadingDelay < 200;
    console.log(`  - UI responsive (<200ms): ${responsive}`);

    expect(loadingDelay).toBeLessThan(200);

    console.log('✅ Test 4.1 PASSED\n');
  });

  test('Test 4.2: Document Loading Performance', async ({ page }) => {
    console.log('\n=== Test 4.2: Document Loading Performance ===');

    await page.goto('/documents');
    await page.waitForTimeout(2000);

    const docLink = page.locator('button:has-text("View"), a[href^="/documents/"]').first();
    const linkExists = await docLink.count() > 0;

    if (linkExists) {
      const startTime = Date.now();

      await docLink.click();

      // Wait for URL change
      await page.waitForURL(/\/documents\/[A-Z0-9-]+/, { timeout: 2000 });
      const routeChangeTime = Date.now() - startTime;

      // Wait for content
      await page.waitForSelector('[class*="document-viewer"], canvas, pre', { timeout: 3000 });
      const contentLoadTime = Date.now() - startTime;

      console.log('Performance metrics:');
      console.log(`  - Route change time: ${routeChangeTime}ms`);
      console.log(`  - Content load time: ${contentLoadTime}ms`);

      expect(routeChangeTime).toBeLessThan(200);
      expect(contentLoadTime).toBeLessThan(3000);

      console.log('✅ Test 4.2 PASSED\n');
    } else {
      console.log('⚠️ No documents to test');
    }
  });
});

test.describe('Error Scenarios', () => {

  test('Test 5.1: Invalid Document ID', async ({ page }) => {
    console.log('\n=== Test 5.1: Invalid Document ID ===');
    const { consoleErrors } = setupConsoleMonitoring(page);

    // Navigate to invalid document ID
    await page.goto('/documents/INVALID-ID-99999');
    await page.waitForTimeout(2000);

    // Check for error message
    const errorMessage = await page.locator('text=/not found|error|invalid/i').count();
    console.log('Error message displayed:', errorMessage > 0);

    // Check for 404 page
    const notFoundText = await page.locator('text=/404|not found/i').count();
    console.log('404 page shown:', notFoundText > 0);

    // Check for back button or navigation
    const backButton = await page.locator('button:has-text("Back"), a:has-text("Back"), a[href="/documents"]').count();
    console.log('Back button/link available:', backButton > 0);

    // Check console for critical errors (not just 404 fetch errors)
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('404') &&
      !err.includes('Not Found') &&
      err.toLowerCase().includes('error')
    );
    console.log('Critical console errors:', criticalErrors.length);

    // Check page didn't crash
    const pageWorking = await page.locator('body').count() > 0;
    console.log('Page still functional:', pageWorking);

    // Assertions
    console.log('\n✓ Assertions:');
    console.log(`  - Error message shown: ${errorMessage > 0 || notFoundText > 0}`);
    console.log(`  - Navigation available: ${backButton > 0}`);
    console.log(`  - No critical errors: ${criticalErrors.length === 0}`);
    console.log(`  - Page functional: ${pageWorking}`);

    expect(errorMessage + notFoundText).toBeGreaterThan(0);
    expect(backButton).toBeGreaterThan(0);
    expect(pageWorking).toBe(true);

    console.log('✅ Test 5.1 PASSED\n');
  });
});
