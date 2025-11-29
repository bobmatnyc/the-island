const { chromium } = require('playwright');

(async () => {
    console.log('Launching browser to test http://localhost:8081/...\n');

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();

    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        consoleMessages.push({ type, text });

        // Print errors and warnings immediately
        if (type === 'error' || type === 'warning') {
            console.log(`[${type.toUpperCase()}] ${text}`);
        }
    });

    // Collect page errors
    const pageErrors = [];
    page.on('pageerror', error => {
        pageErrors.push(error.message);
        console.error(`[PAGE ERROR] ${error.message}`);
        console.error(error.stack);
    });

    // Collect network failures
    const failedRequests = [];
    page.on('requestfailed', request => {
        failedRequests.push({
            url: request.url(),
            failure: request.failure().errorText
        });
        console.error(`[NETWORK ERROR] ${request.url()}: ${request.failure().errorText}`);
    });

    try {
        // Navigate to page with timeout
        await page.goto('http://localhost:8081/', {
            waitUntil: 'networkidle',
            timeout: 10000
        });

        // Wait a bit for JavaScript to execute
        await page.waitForTimeout(2000);

        // Check if page content is visible
        const bodyContent = await page.evaluate(() => {
            return {
                hasContent: document.body.children.length > 0,
                bodyChildren: document.body.children.length,
                bodyText: document.body.innerText.substring(0, 200),
                bodyHTML: document.body.innerHTML.substring(0, 500)
            };
        });

        console.log('\n--- Page Content Check ---');
        console.log(`Has content: ${bodyContent.hasContent}`);
        console.log(`Body children: ${bodyContent.bodyChildren}`);
        console.log(`Body text (first 200 chars): ${bodyContent.bodyText}`);

        // Check for specific elements
        const elements = await page.evaluate(() => {
            return {
                header: !!document.querySelector('.header'),
                tabs: document.querySelectorAll('.tab').length,
                activeView: !!document.querySelector('.view.active'),
                overviewView: !!document.getElementById('overview-view')
            };
        });

        console.log('\n--- Element Check ---');
        console.log(`Header: ${elements.header}`);
        console.log(`Tabs: ${elements.tabs}`);
        console.log(`Active view: ${elements.activeView}`);
        console.log(`Overview view: ${elements.overviewView}`);

        // Take screenshot
        await page.screenshot({ path: '/Users/masa/Projects/epstein/screenshot.png', fullPage: true });
        console.log('\n✓ Screenshot saved to screenshot.png');

        // Summary
        console.log('\n--- Summary ---');
        console.log(`Console messages: ${consoleMessages.length}`);
        console.log(`Page errors: ${pageErrors.length}`);
        console.log(`Failed requests: ${failedRequests.length}`);

        if (pageErrors.length > 0) {
            console.log('\n--- PAGE ERRORS ---');
            pageErrors.forEach((err, i) => {
                console.log(`${i + 1}. ${err}`);
            });
        }

        if (failedRequests.length > 0) {
            console.log('\n--- FAILED REQUESTS ---');
            failedRequests.forEach((req, i) => {
                console.log(`${i + 1}. ${req.url}`);
                console.log(`   Error: ${req.failure}`);
            });
        }

        // Print all console messages
        console.log('\n--- ALL CONSOLE MESSAGES ---');
        consoleMessages.forEach(msg => {
            console.log(`[${msg.type}] ${msg.text}`);
        });

    } catch (error) {
        console.error('\n✗ Error during page load:');
        console.error(error.message);
        console.error(error.stack);
    } finally {
        await browser.close();
    }
})();
