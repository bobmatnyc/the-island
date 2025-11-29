// Timeline Diagnostic Test Script
// Run this in browser console after loading http://localhost:8081/

console.log('=== TIMELINE DIAGNOSTIC TEST ===');

// Test 1: Check if timeline-view element exists
console.log('\n1. DOM Element Check:');
const timelineView = document.getElementById('timeline-view');
console.log('timeline-view exists:', !!timelineView);
if (timelineView) {
    console.log('timeline-view display:', getComputedStyle(timelineView).display);
    console.log('timeline-view visibility:', getComputedStyle(timelineView).visibility);
    console.log('timeline-view innerHTML length:', timelineView.innerHTML.length);
    console.log('timeline-view classes:', timelineView.className);
}

// Test 2: Check if loadTimeline function exists
console.log('\n2. Function Check:');
console.log('loadTimeline exists:', typeof loadTimeline !== 'undefined');
console.log('window.timelineEvents exists:', typeof window.timelineEvents !== 'undefined');
if (typeof window.timelineEvents !== 'undefined') {
    console.log('window.timelineEvents length:', window.timelineEvents?.length || 0);
}

// Test 3: Check timeline tab button and event listeners
console.log('\n3. Tab Button Check:');
const timelineTab = document.querySelector('[onclick*="timeline"]');
console.log('Timeline tab button exists:', !!timelineTab);
if (timelineTab) {
    console.log('Timeline tab onclick:', timelineTab.getAttribute('onclick'));
}

// Test 4: Try to manually trigger timeline load
console.log('\n4. Manual Timeline Load Test:');
try {
    if (typeof loadTimeline === 'function') {
        console.log('Calling loadTimeline()...');
        loadTimeline();
        setTimeout(() => {
            console.log('After loadTimeline - events loaded:', window.timelineEvents?.length || 0);
            console.log('timeline-view innerHTML length:', document.getElementById('timeline-view')?.innerHTML.length || 0);
        }, 1000);
    } else {
        console.error('loadTimeline function not defined!');
    }
} catch (error) {
    console.error('Error calling loadTimeline:', error);
}

// Test 5: Check API endpoint directly
console.log('\n5. API Test:');
fetch('/api/timeline')
    .then(response => {
        console.log('API Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('API returned events:', data.events?.length || 0);
        console.log('Sample event:', data.events?.[0]);
    })
    .catch(error => {
        console.error('API Error:', error);
    });

// Test 6: Check for JavaScript errors
console.log('\n6. Error Listener Check:');
window.addEventListener('error', function(event) {
    console.error('JavaScript Error Detected:', {
        message: event.message,
        source: event.filename,
        line: event.lineno,
        column: event.colno,
        error: event.error
    });
});

console.log('\n=== DIAGNOSTIC TEST COMPLETE ===');
console.log('Check the output above for issues.');
