/**
 * Timeline CSS Investigation Script
 * Tests DOM structure, CSS styles, and JavaScript execution
 */

const puppeteer = require('puppeteer');

(async () => {
    console.log('🔍 Starting Timeline CSS Investigation...\n');

    const browser = await puppeteer.launch({
        headless: false,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Enable console logging
    page.on('console', msg => {
        const type = msg.type();
        const text = msg.text();
        const emoji = type === 'error' ? '❌' : type === 'warning' ? '⚠️' : '📝';
        console.log(`${emoji} [Browser Console ${type}]: ${text}`);
    });

    console.log('📍 Navigating to http://localhost:8000...');
    await page.goto('http://localhost:8000', { waitUntil: 'networkidle2' });

    console.log('\n🔘 Clicking Timeline tab...');
    await page.click('[data-tab="timeline"]');

    // Wait for potential loading
    await page.waitForTimeout(2000);

    console.log('\n📊 DOM INSPECTION:');
    console.log('='.repeat(60));

    // Check if timeline container exists
    const containerExists = await page.evaluate(() => {
        return !!document.getElementById('timeline-events');
    });
    console.log(`✓ Container #timeline-events exists: ${containerExists}`);

    // Count timeline events in DOM
    const eventCount = await page.evaluate(() => {
        return document.querySelectorAll('.timeline-event').length;
    });
    console.log(`✓ Timeline events in DOM: ${eventCount}`);

    // Get container HTML (first 500 chars)
    const containerHTML = await page.evaluate(() => {
        const container = document.getElementById('timeline-events');
        return container ? container.innerHTML.substring(0, 500) : 'NOT FOUND';
    });
    console.log(`✓ Container HTML preview:\n${containerHTML.substring(0, 200)}...\n`);

    console.log('\n🎨 CSS STYLES INSPECTION:');
    console.log('='.repeat(60));

    // Check timeline-container styles
    const containerStyles = await page.evaluate(() => {
        const container = document.getElementById('timeline-events');
        if (!container) return null;

        const computed = window.getComputedStyle(container);
        return {
            display: computed.display,
            visibility: computed.visibility,
            opacity: computed.opacity,
            height: computed.height,
            overflow: computed.overflow,
            position: computed.position
        };
    });

    if (containerStyles) {
        console.log('📦 #timeline-events styles:');
        Object.entries(containerStyles).forEach(([key, value]) => {
            console.log(`   ${key}: ${value}`);
        });
    } else {
        console.log('❌ Could not get container styles');
    }

    // Check first timeline-event styles
    const eventStyles = await page.evaluate(() => {
        const event = document.querySelector('.timeline-event');
        if (!event) return null;

        const computed = window.getComputedStyle(event);
        return {
            display: computed.display,
            visibility: computed.visibility,
            opacity: computed.opacity,
            height: computed.height,
            marginBottom: computed.marginBottom,
            position: computed.position
        };
    });

    if (eventStyles) {
        console.log('\n📌 .timeline-event (first) styles:');
        Object.entries(eventStyles).forEach(([key, value]) => {
            console.log(`   ${key}: ${value}`);
        });
    } else {
        console.log('\n⚠️ No .timeline-event elements found in DOM');
    }

    console.log('\n🔍 JAVASCRIPT EXECUTION CHECK:');
    console.log('='.repeat(60));

    const jsCheck = await page.evaluate(() => {
        return {
            loadTimelineExists: typeof loadTimeline === 'function',
            renderTimelineExists: typeof renderTimeline === 'function',
            filteredDataLength: window.filteredTimelineData ? window.filteredTimelineData.length : 'undefined',
            baselineEventsLength: window.baselineEvents ? window.baselineEvents.length : 'undefined'
        };
    });

    console.log(`✓ loadTimeline function exists: ${jsCheck.loadTimelineExists}`);
    console.log(`✓ renderTimeline function exists: ${jsCheck.renderTimelineExists}`);
    console.log(`✓ filteredTimelineData length: ${jsCheck.filteredDataLength}`);
    console.log(`✓ baselineEvents length: ${jsCheck.baselineEventsLength}`);

    console.log('\n📸 SCREENSHOT:');
    console.log('='.repeat(60));
    await page.screenshot({ path: '/tmp/timeline_investigation.png', fullPage: true });
    console.log('✓ Screenshot saved to: /tmp/timeline_investigation.png');

    console.log('\n🔬 VIEWPORT CHECK:');
    console.log('='.repeat(60));
    const viewport = await page.evaluate(() => {
        const view = document.getElementById('timeline-view');
        if (!view) return null;

        const computed = window.getComputedStyle(view);
        return {
            display: computed.display,
            visibility: computed.visibility,
            opacity: computed.opacity,
            position: computed.position,
            zIndex: computed.zIndex
        };
    });

    if (viewport) {
        console.log('#timeline-view styles:');
        Object.entries(viewport).forEach(([key, value]) => {
            console.log(`   ${key}: ${value}`);
        });
    }

    console.log('\n⏱️ Keeping browser open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);

    await browser.close();
    console.log('\n✅ Investigation complete!');
})();
