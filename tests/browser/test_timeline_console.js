/**
 * Browser Console Test for Timeline Page
 *
 * Open http://localhost:8081 in browser
 * Click Timeline tab
 * Paste this script in browser console to diagnose
 */

console.log('=== TIMELINE DIAGNOSTIC TEST ===');

// 1. Check if timeline data is loaded
console.log('1. Timeline data exists:', typeof timelineData !== 'undefined' ? `Yes (${timelineData?.length || 0} events)` : 'No');

// 2. Check if loadTimeline function exists
console.log('2. loadTimeline function exists:', typeof loadTimeline === 'function');

// 3. Check if DOM elements exist
console.log('3. Timeline container exists:', document.getElementById('timeline-events') !== null);
console.log('4. Timeline stats exist:', document.getElementById('timeline-stats') !== null);

// 5. Check current tab
const activeView = document.querySelector('.view.active');
console.log('5. Active view:', activeView?.id || 'None');

// 6. Manually trigger timeline load
if (typeof loadTimeline === 'function') {
    console.log('6. Manually calling loadTimeline()...');
    loadTimeline().then(() => {
        console.log('✅ loadTimeline() completed');
        console.log('   - timelineData length:', timelineData?.length);
        console.log('   - filteredTimelineData length:', filteredTimelineData?.length);
        console.log('   - Timeline container HTML length:', document.getElementById('timeline-events')?.innerHTML?.length);
    }).catch(err => {
        console.error('❌ loadTimeline() failed:', err);
    });
} else {
    console.error('❌ loadTimeline function not found!');
}

console.log('=== END DIAGNOSTIC ===');
