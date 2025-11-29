// Timeline Diagnostic Test using Puppeteer
// Run with: node test_timeline_puppeteer.js

const puppeteer = require('puppeteer');

(async () => {
    console.log('🚀 Starting Timeline Diagnostic Test...\n');

    const browser = await puppeteer.launch({
        headless: false,  // Show browser for debugging
        devtools: true,   // Open DevTools automatically
        args: ['--window-size=1920,1080']
    });

    const page = await browser.newPage();

    // Collect console messages
    const consoleMessages = [];
    page.on('console', msg => {
        const text = msg.text();
        consoleMessages.push({
            type: msg.type(),
            text: text
        });
        console.log(`[${msg.type().toUpperCase()}]`, text);
    });

    // Collect errors
    const errors = [];
    page.on('pageerror', error => {
        errors.push(error.message);
        console.error('❌ PAGE ERROR:', error.message);
    });

    try {
        console.log('📍 Navigating to http://localhost:8081/...\n');
        await page.goto('http://localhost:8081/', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });

        console.log('✅ Page loaded successfully\n');

        // Wait a bit for initial JS to execute
        await page.waitForTimeout(2000);

        console.log('📊 Test 1: Check initial DOM state');
        const initialCheck = await page.evaluate(() => {
            return {
                timelineViewExists: !!document.getElementById('timeline-view'),
                timelineEventsExists: !!document.getElementById('timeline-events'),
                timelineViewDisplay: document.getElementById('timeline-view') ?
                    getComputedStyle(document.getElementById('timeline-view')).display : 'N/A',
                loadTimelineExists: typeof loadTimeline !== 'undefined',
                baselineEventsLength: typeof baselineEvents !== 'undefined' ? baselineEvents.length : 'undefined',
                timelineDataLength: typeof timelineData !== 'undefined' ? timelineData.length : 'undefined'
            };
        });
        console.log('Initial state:', JSON.stringify(initialCheck, null, 2));

        console.log('\n📍 Test 2: Click Timeline tab');
        // Find and click the Timeline tab
        const timelineTabClicked = await page.evaluate(() => {
            const tabs = Array.from(document.querySelectorAll('.tab-btn'));
            const timelineTab = tabs.find(tab => tab.textContent.includes('Timeline'));
            if (timelineTab) {
                timelineTab.click();
                return true;
            }
            return false;
        });

        if (!timelineTabClicked) {
            console.error('❌ Could not find Timeline tab button!');
        } else {
            console.log('✅ Timeline tab clicked');

            // Wait for tab to switch
            await page.waitForTimeout(1000);

            console.log('\n📊 Test 3: Check state after tab click');
            const afterClickCheck = await page.evaluate(() => {
                return {
                    timelineViewDisplay: document.getElementById('timeline-view') ?
                        getComputedStyle(document.getElementById('timeline-view')).display : 'N/A',
                    timelineEventsHTML: document.getElementById('timeline-events') ?
                        document.getElementById('timeline-events').innerHTML.substring(0, 500) : 'N/A',
                    timelineEventsChildren: document.getElementById('timeline-events') ?
                        document.getElementById('timeline-events').children.length : 0,
                    timelineDataLength: typeof timelineData !== 'undefined' ? timelineData.length : 'undefined',
                    filteredTimelineDataLength: typeof filteredTimelineData !== 'undefined' ?
                        filteredTimelineData.length : 'undefined'
                };
            });
            console.log('After click state:', JSON.stringify(afterClickCheck, null, 2));

            // Wait a bit more for potential async loading
            await page.waitForTimeout(2000);

            console.log('\n📊 Test 4: Final state check');
            const finalCheck = await page.evaluate(() => {
                const container = document.getElementById('timeline-events');
                return {
                    containerExists: !!container,
                    containerHTML: container ? container.innerHTML.substring(0, 300) : 'N/A',
                    containerChildrenCount: container ? container.children.length : 0,
                    timelineDataLength: typeof timelineData !== 'undefined' ? timelineData.length : 'undefined',
                    filteredTimelineDataLength: typeof filteredTimelineData !== 'undefined' ?
                        filteredTimelineData.length : 'undefined'
                };
            });
            console.log('Final state:', JSON.stringify(finalCheck, null, 2));
        }

        console.log('\n📋 Summary Report:');
        console.log('================');
        console.log(`Total console messages: ${consoleMessages.length}`);
        console.log(`Errors: ${errors.length}`);

        if (errors.length > 0) {
            console.log('\n❌ Errors found:');
            errors.forEach(err => console.log(`  - ${err}`));
        }

        console.log('\n🔍 Console Messages (relevant):');
        const relevantMessages = consoleMessages.filter(msg =>
            msg.text.includes('Timeline') ||
            msg.text.includes('timeline') ||
            msg.text.includes('loadTimeline') ||
            msg.text.includes('events')
        );
        relevantMessages.forEach(msg => {
            console.log(`  [${msg.type}] ${msg.text}`);
        });

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        console.error(error.stack);
    } finally {
        console.log('\n⏳ Keeping browser open for 30 seconds for manual inspection...');
        await page.waitForTimeout(30000);
        await browser.close();
        console.log('✅ Test complete');
    }
})();
