# Timeline Navigation Testing Guide

## Quick Start

1. **Open Application**: http://localhost:5000
2. **Switch to Flights Tab**: Click "Flights" in navigation
3. **Wait for Timeline**: Timeline should initialize automatically
4. **Hard Refresh**: Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows) to clear cache

## Visual Verification

### What to Look For

**Timeline Controls** (below the slider):
```
[← Previous] [📅 Latest] [Next →]
```

**Initial State** (after loading):
- Timeline starts at **Sep 2002** (last month)
- **Previous** button: Enabled (opacity 1.0)
- **Next** button: **Disabled** (opacity 0.5, greyed out)
- **Latest** button: Always enabled

### Button State Changes

| Position | Previous Button | Next Button | Latest Button |
|----------|----------------|-------------|---------------|
| First month (Jan 1998) | **Disabled** (0.5 opacity) | Enabled (1.0 opacity) | Enabled |
| Middle month (any) | Enabled | Enabled | Enabled |
| Last month (Sep 2002) | Enabled | **Disabled** (0.5 opacity) | Enabled |

## Manual Testing Steps

### Test 1: Previous Button Navigation

**Steps**:
1. Ensure you're at Sep 2002 (last month)
2. Click **Previous** button
3. Observe changes

**Expected Results**:
- ✅ Slider moves one step backward
- ✅ Month label changes to "Aug 2002"
- ✅ Flight count updates
- ✅ Map shows Aug 2002 flights
- ✅ **Next** button becomes enabled (opacity 1.0)
- ✅ Console shows: `[Timeline Nav] Previous button clicked`

**Repeat**: Click Previous 47 more times to reach Jan 1998

**Expected at Jan 1998**:
- ✅ **Previous** button becomes disabled (opacity 0.5)
- ✅ Clicking shows toast: "Already at first month"
- ✅ Console shows: `[Timeline Nav] Already at first month`

---

### Test 2: Next Button Navigation

**Steps**:
1. Navigate to Jan 1998 (first month)
2. Click **Next** button
3. Observe changes

**Expected Results**:
- ✅ Slider moves one step forward
- ✅ Month label changes to "Feb 1998"
- ✅ Flight count updates
- ✅ Map shows Feb 1998 flights
- ✅ **Previous** button becomes enabled
- ✅ Console shows: `[Timeline Nav] Next button clicked`

**Repeat**: Click Next 47 more times to reach Sep 2002

**Expected at Sep 2002**:
- ✅ **Next** button becomes disabled (opacity 0.5)
- ✅ Clicking shows toast: "Already at last month"
- ✅ Console shows: `[Timeline Nav] Already at last month`

---

### Test 3: Latest Button

**Steps**:
1. Navigate to any middle month (e.g., Jan 2000)
2. Note current month in timeline header
3. Click **Latest** button
4. Observe changes

**Expected Results**:
- ✅ Slider jumps immediately to Sep 2002
- ✅ Month label changes to "Sep 2002"
- ✅ Map shows Sep 2002 flights
- ✅ **Next** button becomes disabled
- ✅ **Previous** button becomes enabled
- ✅ Toast shows: "Jumped to Sep 2002"
- ✅ Console shows: `[Timeline Nav] Jumping to latest month`

**Edge Case**: Click Latest while already at Sep 2002
- ✅ Toast shows: "Already showing latest month"
- ✅ No slider movement
- ✅ Console shows: `[Timeline Nav] Already at latest month`

---

### Test 4: Slider Drag Integration

**Steps**:
1. Manually drag the slider to a middle position
2. Observe button states

**Expected Results**:
- ✅ Both **Previous** and **Next** enabled (opacity 1.0)
- ✅ Month display updates
- ✅ Map updates

**Drag to Start**:
- ✅ **Previous** becomes disabled
- ✅ **Next** becomes enabled

**Drag to End**:
- ✅ **Previous** becomes enabled
- ✅ **Next** becomes disabled

---

## Console Testing

### Open Browser Console
Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)

### Quick Console Test

```javascript
// Verify timeline is initialized
console.log('Months available:', window.flightMonths?.length); // Should be 49
console.log('Current month index:', window.currentMonthIndex); // Should be 48 (last)
console.log('Current month:', window.flightMonths?.[window.currentMonthIndex]?.label); // Should be "Sep 2002"

// Test Previous button
console.log('\n--- Testing Previous ---');
previousMonth();
// Should move to index 47, log activity, update map

// Test Next button
console.log('\n--- Testing Next ---');
nextMonth();
// Should move back to index 48, log activity

// Test Latest button
console.log('\n--- Testing Latest ---');
previousMonth(); // Move to index 47 first
resetTimelineFilter(); // Jump back to 48
// Should show success toast

// Check button states
const btns = document.querySelectorAll('.timeline-nav-btn');
console.log('\n--- Button States ---');
btns.forEach(btn => {
    const text = btn.textContent.trim();
    if (text.includes('Previous') || text.includes('Next')) {
        console.log(text, '- Disabled:', btn.disabled, '- Opacity:', btn.style.opacity);
    }
});
```

### Expected Console Output

```
[Timeline Nav] Previous button clicked
[Timeline Nav] Current index: 48
[Timeline Nav] Moving to index 47 (Aug 2002)

[Timeline Nav] Next button clicked
[Timeline Nav] Current index: 47, Max: 48
[Timeline Nav] Moving to index 48 (Sep 2002)

[Timeline Nav] Latest button clicked
[Timeline Nav] Current index: 47
[Timeline Nav] Jumping to latest month (index 48: Sep 2002)
```

---

## Error Scenarios

### Timeline Not Initialized

**Trigger**: Click buttons before timeline loads

**Expected**:
- ✅ Toast: "Timeline not ready"
- ✅ Console error: "Timeline not initialized"
- ✅ No slider movement

### Slider Element Missing

**Trigger**: Delete slider element from DOM (developer tools)

**Expected**:
- ✅ Toast: "Slider not found"
- ✅ Console error: "Slider element not found"
- ✅ No JavaScript errors/crashes

### No Flight Data

**Trigger**: Load page with empty flight data

**Expected**:
- ✅ Timeline not shown
- ✅ Buttons not present
- ✅ Console warning: "No flight data available for timeline initialization"

---

## Performance Verification

### Smooth Navigation

**Test**: Rapidly click Previous/Next buttons

**Expected**:
- ✅ Each click moves exactly one month
- ✅ No skipped months
- ✅ No lag or delay
- ✅ Map updates smoothly
- ✅ No console errors

### Memory Leaks

**Test**: Navigate through all 49 months multiple times

**Expected**:
- ✅ No memory buildup
- ✅ Consistent performance
- ✅ No browser slowdown

---

## Visual Regression Checklist

### Button Appearance

- ✅ Enabled: Opacity 1.0, pointer cursor
- ✅ Disabled: Opacity 0.5, not-allowed cursor
- ✅ Hover effect on enabled buttons (if styled)
- ✅ Icons render correctly (Lucide chevrons)

### Layout

- ✅ Buttons centered below slider
- ✅ Proper spacing between buttons
- ✅ No layout shift when enabling/disabling
- ✅ Responsive on mobile (buttons stack or wrap)

### Toast Notifications

- ✅ Success toast (green): "Jumped to Sep 2002"
- ✅ Info toast (blue): "Already at first/last month"
- ✅ Error toast (red): "Timeline not ready" (if errors)

---

## Browser Compatibility

Test in these browsers:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

**Known Issues**: None expected (uses standard DOM APIs)

---

## Mobile Testing

### Touch Interactions

**Test**: Tap Previous/Next buttons on mobile

**Expected**:
- ✅ Single tap triggers navigation
- ✅ No double-tap delay
- ✅ Disabled buttons don't respond to taps
- ✅ Toast notifications appear

### Responsive Layout

- ✅ Buttons visible on small screens
- ✅ No horizontal overflow
- ✅ Icons scale appropriately

---

## Automated Testing Script

Save this as `test_timeline_nav.js` and run in console:

```javascript
(async function testTimelineNavigation() {
    console.log('🧪 TIMELINE NAVIGATION AUTOMATED TEST\n');

    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
    let passed = 0, failed = 0;

    function assert(condition, message) {
        if (condition) {
            console.log('✅', message);
            passed++;
        } else {
            console.error('❌', message);
            failed++;
        }
    }

    // Test 1: Initialization
    console.log('--- Test 1: Initialization ---');
    assert(window.flightMonths?.length > 0, 'Flight months loaded');
    assert(window.currentMonthIndex !== undefined, 'Current index defined');
    assert(document.getElementById('flight-timeline-slider'), 'Slider element exists');
    assert(document.getElementById('flight-timeline-slider')?.noUiSlider, 'noUiSlider initialized');

    // Test 2: Initial state (at last month)
    console.log('\n--- Test 2: Initial State ---');
    const lastIndex = window.flightMonths.length - 1;
    assert(window.currentMonthIndex === lastIndex, 'Started at last month');

    // Test 3: Previous navigation
    console.log('\n--- Test 3: Previous Button ---');
    const beforePrev = window.currentMonthIndex;
    previousMonth();
    await sleep(500);
    assert(window.currentMonthIndex === beforePrev - 1, 'Previous moved back one month');

    // Test 4: Next navigation
    console.log('\n--- Test 4: Next Button ---');
    const beforeNext = window.currentMonthIndex;
    nextMonth();
    await sleep(500);
    assert(window.currentMonthIndex === beforeNext + 1, 'Next moved forward one month');

    // Test 5: Latest button
    console.log('\n--- Test 5: Latest Button ---');
    previousMonth(); // Move away from last
    await sleep(500);
    resetTimelineFilter();
    await sleep(500);
    assert(window.currentMonthIndex === lastIndex, 'Latest jumped to last month');

    // Test 6: Boundary conditions
    console.log('\n--- Test 6: Boundary Conditions ---');
    // Go to first month
    while (window.currentMonthIndex > 0) {
        previousMonth();
        await sleep(100);
    }
    assert(window.currentMonthIndex === 0, 'Reached first month');
    const beforeBoundary = window.currentMonthIndex;
    previousMonth(); // Try to go before first
    await sleep(200);
    assert(window.currentMonthIndex === beforeBoundary, 'Cannot go before first month');

    // Test 7: Button states
    console.log('\n--- Test 7: Button States ---');
    const btns = document.querySelectorAll('.timeline-nav-btn');
    const prevBtn = Array.from(btns).find(b => b.textContent.includes('Previous'));
    const nextBtn = Array.from(btns).find(b => b.textContent.includes('Next'));
    assert(prevBtn !== undefined, 'Previous button found');
    assert(nextBtn !== undefined, 'Next button found');
    assert(prevBtn.disabled === true, 'Previous disabled at start');
    assert(nextBtn.disabled === false, 'Next enabled at start');

    // Summary
    console.log('\n' + '='.repeat(50));
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log('='.repeat(50));

    if (failed === 0) {
        console.log('🎉 All tests passed!');
    } else {
        console.error('⚠️  Some tests failed');
    }
})();
```

---

## Troubleshooting

### Buttons Don't Respond

**Solution**:
1. Hard refresh browser (Cmd+Shift+R)
2. Check console for errors
3. Verify cache version: `app.js?v=20251118_timeline_nav_fix`
4. Verify server restarted

### Slider Doesn't Move

**Cause**: noUiSlider not initialized

**Solution**:
1. Check console for initialization errors
2. Verify flight data loaded
3. Check timeline initialization logs

### Button States Don't Update

**Cause**: `updateNavigationButtons()` not called

**Solution**:
1. Check console for function errors
2. Verify buttons have class `.timeline-nav-btn`
3. Verify slider 'update' event fires

### Console Errors

**Common Issues**:
- `previousMonth is not defined` → Cache not cleared
- `Cannot read property 'noUiSlider' of null` → Slider not initialized
- `flightMonths is undefined` → Data not loaded yet

**Solutions**:
- Clear cache and hard refresh
- Wait for data to load before clicking
- Check network tab for data fetch errors

---

**Last Updated**: 2025-11-18
**Cache Version**: `20251118_timeline_nav_fix`
**Status**: Ready for testing
