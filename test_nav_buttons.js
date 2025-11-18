// Test script for timeline navigation buttons
// Run this in browser console on http://localhost:5000/#flights

console.log('=== TIMELINE NAVIGATION DIAGNOSTIC ===\n');

// 1. Check global variables
console.log('1. Global Variables:');
console.log('   window.flightMonths:', window.flightMonths ? window.flightMonths.length + ' months' : 'NOT DEFINED');
console.log('   window.currentMonthIndex:', window.currentMonthIndex);
console.log('   window.allFlightRoutes:', window.allFlightRoutes ? window.allFlightRoutes.length + ' routes' : 'NOT DEFINED');

// 2. Check slider element
console.log('\n2. Slider Element:');
const sliderEl = document.getElementById('flight-timeline-slider');
console.log('   Element exists:', !!sliderEl);
console.log('   Has noUiSlider:', sliderEl ? !!sliderEl.noUiSlider : false);
if (sliderEl && sliderEl.noUiSlider) {
    console.log('   Current value:', sliderEl.noUiSlider.get());
}

// 3. Check function existence
console.log('\n3. Function Availability:');
console.log('   previousMonth:', typeof previousMonth);
console.log('   nextMonth:', typeof nextMonth);
console.log('   resetTimelineFilter:', typeof resetTimelineFilter);

// 4. Test previousMonth()
console.log('\n4. Testing previousMonth():');
const currentIndex = window.currentMonthIndex;
console.log('   Current index before:', currentIndex);
try {
    previousMonth();
    console.log('   ✓ Function executed');
    setTimeout(() => {
        console.log('   Current index after:', window.currentMonthIndex);
        console.log('   Changed:', currentIndex !== window.currentMonthIndex);
    }, 100);
} catch (error) {
    console.error('   ✗ Error:', error.message);
}

// 5. Test nextMonth()
console.log('\n5. Testing nextMonth() (after 500ms):');
setTimeout(() => {
    const idx = window.currentMonthIndex;
    console.log('   Current index before:', idx);
    try {
        nextMonth();
        console.log('   ✓ Function executed');
        setTimeout(() => {
            console.log('   Current index after:', window.currentMonthIndex);
            console.log('   Changed:', idx !== window.currentMonthIndex);
        }, 100);
    } catch (error) {
        console.error('   ✗ Error:', error.message);
    }
}, 500);

// 6. Check button elements
console.log('\n6. Button Elements:');
setTimeout(() => {
    const buttons = document.querySelectorAll('.timeline-nav-btn, .timeline-reset-btn');
    console.log('   Found buttons:', buttons.length);
    buttons.forEach((btn, i) => {
        console.log(`   Button ${i}:`, btn.textContent.trim(), 'onclick:', btn.onclick ? 'set' : 'via HTML attribute');
    });
}, 100);

console.log('\n=== DIAGNOSTIC COMPLETE ===');
