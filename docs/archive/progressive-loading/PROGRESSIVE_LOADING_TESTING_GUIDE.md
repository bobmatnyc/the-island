# Progressive Network Loading - Testing Guide

## Quick Start Testing

### 1. Open Application
```bash
cd /Users/masa/Projects/epstein/server
python app.py
```

Navigate to: http://localhost:5000

### 2. Access Network View
1. Click on "Network" tab in navigation
2. Look for "Network Controls" panel (top-right corner)
3. Scroll down in controls to find "Connection Loading" section

## Visual Inspection Checklist

### UI Components Present ✓
- [ ] **Connection Count Display**: Shows "Showing 300 of 1,584 connections"
- [ ] **Range Slider**: Horizontal slider below count display
- [ ] **Load More Button**: Blue button labeled "Load More (+100)"
- [ ] **Show All Button**: Amber/orange bordered button labeled "Show All"
- [ ] **Reset Button**: Gray button labeled "Reset to Default"
- [ ] **Loading Indicator**: Hidden by default, shows "Updating network..." during updates

### Styling Verification ✓
- [ ] Controls integrate seamlessly with existing dark theme
- [ ] Slider has blue circular thumb (16px diameter)
- [ ] Buttons have consistent padding and border radius
- [ ] Hover effects work on all interactive elements
- [ ] Focus indicators visible when tabbing through controls

## Functional Testing Scenarios

### Scenario 1: Slider Interaction
**Test Steps**:
1. Grab slider thumb
2. Drag to 500 (halfway)
3. Release

**Expected Results**:
- [ ] Count display updates immediately: "Showing 500 of 1,584 connections"
- [ ] Network visualization updates after 200ms
- [ ] New edges fade in smoothly (300ms transition)
- [ ] Loading indicator appears briefly
- [ ] Simulation stabilizes after ~2 seconds

### Scenario 2: Load More Button
**Test Steps**:
1. Note current count (300)
2. Click "Load More" button
3. Observe changes

**Expected Results**:
- [ ] Count increases to 400
- [ ] Slider position moves to 400
- [ ] 100 new edges added to visualization
- [ ] Button text remains "Load More (+100)"
- [ ] Button remains enabled

**Repeat**:
4. Click "Load More" 14 more times (until 1,584)

**Expected Results**:
- [ ] Count reaches 1,584
- [ ] Button text changes to "All Loaded"
- [ ] Button becomes disabled (grayed out)
- [ ] "Show All" button also disabled

### Scenario 3: Show All Button
**Test Steps**:
1. Reset to 300 (if not already)
2. Click "Show All" button
3. Confirm dialog

**Expected Results**:
- [ ] Confirmation dialog appears: "Warning: Loading all 1,584 connections..."
- [ ] After confirming, count jumps to 1,584
- [ ] All edges loaded in network
- [ ] Both "Load More" and "Show All" disabled
- [ ] Performance acceptable (< 3 seconds load time)

### Scenario 4: Reset Button
**Test Steps**:
1. Load some connections (e.g., 800)
2. Click "Reset to Default" button

**Expected Results**:
- [ ] Count returns to 300
- [ ] Slider resets to 300 position
- [ ] Edges reduce to 300 strongest connections
- [ ] Reset button becomes disabled (grayed out)
- [ ] Other buttons re-enabled

### Scenario 5: Slider Debouncing
**Test Steps**:
1. Drag slider rapidly back and forth (300 ↔ 800)
2. Watch console for update calls

**Expected Results**:
- [ ] Count display updates immediately during drag
- [ ] Network updates only after 200ms of no movement
- [ ] No excessive re-renders
- [ ] Smooth performance, no lag

## Edge Case Testing

### Test 1: Minimum Value
**Steps**: Drag slider all the way left
**Expected**: Slider stops at 100, shows "Showing 100 of 1,584 connections"

### Test 2: Maximum Value
**Steps**: Drag slider all the way right
**Expected**: Slider reaches 1,584, both action buttons disabled

### Test 3: Rapid Button Clicks
**Steps**: Click "Load More" rapidly 5 times in 1 second
**Expected**: Each click adds 100, no duplicate edges, count accurate

### Test 4: Network Interaction During Update
**Steps**:
1. Start loading to 1,000 connections
2. Immediately click on a node

**Expected**:
- Node selection works
- Loading completes
- No errors in console

### Test 5: Filter Interaction
**Steps**:
1. Set connections to 600
2. Apply "Billionaires only" filter
3. Check connection count

**Expected**:
- Node filtering works independently
- Connection count remains "600 of 1,584"
- Only edges between filtered nodes shown

## Performance Benchmarks

### Loading Times (Target)
- **300 → 400**: < 0.5 seconds
- **300 → 600**: < 1.0 seconds
- **300 → 1,000**: < 2.0 seconds
- **300 → 1,584**: < 3.0 seconds

### Memory Usage
- **Initial (300 edges)**: Baseline
- **Full (1,584 edges)**: < 2x baseline
- **After reset**: Returns to baseline

### CPU Usage
- **Idle**: Near 0%
- **During update**: Spike to 30-40%, then back to idle
- **After stabilization**: < 5%

## Browser Compatibility Testing

### Chrome (Latest)
- [ ] All features work
- [ ] Smooth animations
- [ ] Slider responsive

### Firefox (Latest)
- [ ] All features work
- [ ] Smooth animations
- [ ] Slider responsive

### Safari (Latest)
- [ ] All features work
- [ ] Smooth animations
- [ ] Slider responsive

### Edge (Latest)
- [ ] All features work
- [ ] Smooth animations
- [ ] Slider responsive

## Accessibility Testing

### Keyboard Navigation
**Test Steps**:
1. Tab to "Connection Loading" section
2. Tab through slider, buttons
3. Use Enter/Space on buttons
4. Use arrow keys on slider

**Expected Results**:
- [ ] Focus moves logically through controls
- [ ] Focus indicators clearly visible
- [ ] Buttons activate on Enter/Space
- [ ] Slider adjusts with arrow keys

### Screen Reader Testing (VoiceOver/NVDA)
**Test Steps**:
1. Enable screen reader
2. Navigate to controls
3. Listen to announcements

**Expected Announcements**:
- [ ] "Connection Loading" section announced
- [ ] "Showing 300 of 1,584 connections" read correctly
- [ ] Slider value announced on change
- [ ] Button labels and states (disabled) announced
- [ ] Loading indicator announced when active

## Console Error Checking

### Open Browser DevTools
**Check for**:
- [ ] No JavaScript errors
- [ ] No warning messages
- [ ] No failed network requests
- [ ] D3 simulation running smoothly

### Expected Console Output
```
Network loaded with 387 nodes and 1584 edges
Progressive loading initialized: 300 of 1584 connections
```

### During Updates
```
Updating network to 500 connections
Network update complete: 500 edges
```

## Stress Testing

### Test 1: Rapid Slider Movement
**Steps**: Move slider back and forth rapidly for 30 seconds
**Expected**: No lag, no errors, smooth throughout

### Test 2: Repeated Load/Reset Cycles
**Steps**:
1. Load to 1,584
2. Reset to 300
3. Repeat 10 times

**Expected**:
- Consistent performance
- No memory leaks
- No visual artifacts

### Test 3: Combined Interactions
**Steps**: Simultaneously:
- Drag slider
- Apply filters
- Search nodes
- Click connections

**Expected**:
- All features work independently
- No conflicts or errors
- Performance remains acceptable

## Regression Testing

### Verify Existing Features Still Work
- [ ] Node selection and highlighting
- [ ] Edge hover tooltips
- [ ] Connection details panel
- [ ] Network search
- [ ] Billionaire filter
- [ ] Connection count filters (high/medium/low)
- [ ] Link distance slider
- [ ] Charge strength slider
- [ ] Zoom and pan controls
- [ ] Legend display

## Bug Report Template

If you find an issue, report using this format:

```
**Bug Title**: [Concise description]

**Steps to Reproduce**:
1. [First step]
2. [Second step]
3. [Third step]

**Expected Behavior**: [What should happen]

**Actual Behavior**: [What actually happens]

**Browser**: [Chrome/Firefox/Safari/Edge] version [X.X]

**Screenshot**: [If applicable]

**Console Errors**: [Copy any errors from console]

**Reproducibility**: [Always/Sometimes/Once]
```

## Success Criteria

All tests pass when:
- ✅ All UI components render correctly
- ✅ All buttons perform expected actions
- ✅ Slider updates network smoothly
- ✅ No console errors
- ✅ Performance within benchmarks
- ✅ Full keyboard accessibility
- ✅ Works across all major browsers
- ✅ No regression in existing features

## Known Issues & Workarounds

### Issue: Slider jumps on first click
**Workaround**: Click slider track first, then drag
**Status**: Minor cosmetic issue, does not affect functionality

### Issue: Brief flash on "Show All"
**Expected**: Normal behavior when loading 1,200+ new edges
**Mitigation**: Loading indicator provides feedback

---

**Last Updated**: November 17, 2025
**Tester**: [Your Name]
**Date Tested**: [Date]
**Results**: [Pass/Fail with notes]
