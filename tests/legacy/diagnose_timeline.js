const { chromium } = require('playwright');

async function diagnoseTimeline() {
    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();

    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
        consoleMessages.push({
            type: msg.type(),
            text: msg.text(),
            location: msg.location()
        });
    });

    // Collect errors
    const errors = [];
    page.on('pageerror', error => {
        errors.push({
            message: error.message,
            stack: error.stack
        });
    });

    try {
        console.log('Navigating to http://localhost:8081/...');
        await page.goto('http://localhost:8081/', { waitUntil: 'networkidle' });

        // Wait for page to load
        await page.waitForTimeout(2000);

        console.log('Taking initial screenshot...');
        await page.screenshot({ path: '/Users/masa/Projects/epstein/screenshot_initial.png', fullPage: true });

        // Try to find and click Timeline tab
        console.log('Looking for Timeline tab...');
        const timelineSelectors = [
            'button:has-text("Timeline")',
            'a:has-text("Timeline")',
            '[data-view="timeline"]',
            '.view-tab:has-text("Timeline")',
            '#timeline-tab'
        ];

        let clicked = false;
        for (const selector of timelineSelectors) {
            try {
                const element = await page.locator(selector).first();
                if (await element.isVisible({ timeout: 1000 })) {
                    console.log(`Found Timeline tab with selector: ${selector}`);
                    await element.click();
                    clicked = true;
                    break;
                }
            } catch (e) {
                // Try next selector
            }
        }

        if (!clicked) {
            console.log('Could not find Timeline tab button. Available buttons:');
            const buttons = await page.locator('button').all();
            for (const btn of buttons) {
                const text = await btn.textContent();
                console.log(`  - Button: "${text}"`);
            }
        }

        // Wait for any animations/transitions
        await page.waitForTimeout(1000);

        console.log('Taking timeline screenshot...');
        await page.screenshot({ path: '/Users/masa/Projects/epstein/screenshot_timeline.png', fullPage: true });

        // Extract comprehensive diagnostics
        console.log('Extracting diagnostics...');
        const diagnostics = await page.evaluate(() => {
            const getElementInfo = (selector) => {
                const el = document.querySelector(selector);
                if (!el) return { exists: false };

                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);

                return {
                    exists: true,
                    visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none' && styles.visibility !== 'hidden',
                    rect: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height,
                        bottom: rect.bottom,
                        right: rect.right
                    },
                    styles: {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: styles.opacity,
                        position: styles.position,
                        zIndex: styles.zIndex,
                        overflow: styles.overflow,
                        height: styles.height,
                        maxHeight: styles.maxHeight,
                        minHeight: styles.minHeight
                    },
                    innerHTML_length: el.innerHTML.length,
                    childCount: el.children.length,
                    classList: Array.from(el.classList)
                };
            };

            return {
                timelineView: getElementInfo('#timeline-view'),
                timelineEvents: getElementInfo('#timeline-events'),
                timelineContainer: getElementInfo('.timeline-container'),
                mainContent: getElementInfo('#main-content'),
                currentView: document.querySelector('.view.active')?.id || 'none',
                allViews: Array.from(document.querySelectorAll('.view')).map(v => ({
                    id: v.id,
                    active: v.classList.contains('active'),
                    display: window.getComputedStyle(v).display
                })),
                timelineEventCount: document.querySelectorAll('.timeline-event').length,
                timelineItemCount: document.querySelectorAll('.timeline-item').length,
                bodyHeight: document.body.scrollHeight,
                viewportHeight: window.innerHeight
            };
        });

        console.log('\n=== DIAGNOSTICS ===');
        console.log(JSON.stringify(diagnostics, null, 2));

        console.log('\n=== CONSOLE MESSAGES ===');
        consoleMessages.forEach(msg => {
            console.log(`[${msg.type}] ${msg.text}`);
        });

        console.log('\n=== ERRORS ===');
        if (errors.length > 0) {
            errors.forEach(err => {
                console.log(`ERROR: ${err.message}`);
                console.log(err.stack);
            });
        } else {
            console.log('No JavaScript errors detected');
        }

        // Get HTML structure of timeline area
        const timelineHTML = await page.evaluate(() => {
            const view = document.getElementById('timeline-view');
            if (!view) return 'Timeline view not found';

            // Get simplified HTML structure
            const getStructure = (el, depth = 0) => {
                if (depth > 3) return '...';
                const indent = '  '.repeat(depth);
                let result = `${indent}<${el.tagName.toLowerCase()}`;
                if (el.id) result += ` id="${el.id}"`;
                if (el.className) result += ` class="${el.className}"`;
                result += '>\n';

                for (let child of el.children) {
                    result += getStructure(child, depth + 1);
                }

                return result;
            };

            return getStructure(view);
        });

        console.log('\n=== TIMELINE HTML STRUCTURE ===');
        console.log(timelineHTML);

        // Save diagnostics to file
        const fs = require('fs');
        fs.writeFileSync('/Users/masa/Projects/epstein/timeline_diagnostics.json',
            JSON.stringify({ diagnostics, consoleMessages, errors, timelineHTML }, null, 2));

        console.log('\n✅ Diagnostics complete!');
        console.log('📸 Screenshots saved: screenshot_initial.png, screenshot_timeline.png');
        console.log('📄 Full diagnostics saved: timeline_diagnostics.json');

        // Keep browser open for manual inspection
        console.log('\nBrowser will remain open for 30 seconds for manual inspection...');
        await page.waitForTimeout(30000);

    } catch (error) {
        console.error('Error during diagnosis:', error);
        throw error;
    } finally {
        await browser.close();
    }
}

diagnoseTimeline().catch(console.error);
