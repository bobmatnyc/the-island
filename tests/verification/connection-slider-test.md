# Connection Slider Global Max - Manual Test Plan

## Test Date: 2025-12-06
## Tester: [Your Name]
## File Modified: `frontend/src/pages/Entities.tsx`

---

## Pre-Test Setup

### 1. Start Development Server
```bash
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

### 2. Open Browser Console
- Open DevTools (F12 or Cmd+Option+I)
- Go to Console tab
- Clear console

---

## Test Case 1: Global Max Fetch on Mount

**Objective**: Verify global max connection count is fetched once on initial page load

### Steps:
1. Navigate to http://localhost:5173/entities
2. Check browser console

### Expected Results:
- [ ] Console shows: `Global max connections: {number}`
- [ ] Number should be ~1,431 (or current max in dataset)
- [ ] Only one log entry (not repeated on subsequent actions)

### Actual Results:
```
Console output:
[Record output here]
```

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 2: Slider Max Stability Across Pages

**Objective**: Verify slider max value stays constant when navigating between pages

### Steps:
1. Navigate to Entities page
2. Note the slider max label (right side of slider)
3. Click "Next" to go to page 2
4. Note the slider max label
5. Click "Next" to go to page 3
6. Note the slider max label
7. Click "Previous" to go back to page 2

### Expected Results:
- [ ] Slider max label shows same value on all pages
- [ ] No jumping or scale changes
- [ ] Value remains constant: {record value}

### Actual Results:
| Page | Slider Max Value | Changed? |
|------|------------------|----------|
| 1    |                  | N/A      |
| 2    |                  |          |
| 3    |                  |          |
| 2    |                  |          |

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 3: Smooth Slider Movement (Increase)

**Objective**: Verify slider moves smoothly when increasing minimum connections

### Steps:
1. Navigate to Entities page
2. Set slider to 0
3. Slowly drag slider to the right
4. Observe movement and scale

### Expected Results:
- [ ] Slider moves smoothly without jumping
- [ ] Scale remains consistent
- [ ] Entity count decreases as threshold increases
- [ ] No console errors

### Actual Results:
**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 4: Smooth Slider Movement (Decrease)

**Objective**: Verify slider moves smoothly when DECREASING minimum connections (the main bug fix)

### Steps:
1. Navigate to Entities page
2. Set slider to maximum (far right)
3. Slowly drag slider to the left
4. Observe movement and scale
5. Navigate to page 2
6. Drag slider left again
7. Navigate to page 3
8. Drag slider left again

### Expected Results:
- [ ] Slider moves smoothly without jumping on page 1
- [ ] Slider moves smoothly without jumping on page 2
- [ ] Slider moves smoothly without jumping on page 3
- [ ] Scale remains consistent across all pages
- [ ] Entity count increases as threshold decreases
- [ ] No console errors

### Actual Results:
**Status**: ✅ Pass / ❌ Fail
**Notes**: [This is the critical test - previously failed]

---

## Test Case 5: Info Tooltip

**Objective**: Verify info icon tooltip displays correctly

### Steps:
1. Navigate to Entities page
2. Locate the ℹ️ icon next to "Minimum Connections"
3. Hover over the icon

### Expected Results:
- [ ] Tooltip appears with text: "Connections represent co-appearances in flight logs. Not all entities appear in the flight network."
- [ ] Tooltip is readable and properly positioned
- [ ] Icon has cursor-help style (question mark cursor)

### Actual Results:
**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 6: Filtering Correctness (minConnections = 0)

**Objective**: Verify filter shows all entities when set to 0

### Steps:
1. Navigate to Entities page
2. Set slider to 0
3. Check entity count
4. Check helper text below slider

### Expected Results:
- [ ] All entities shown (should be total count: ~1,637)
- [ ] Helper text shows: "Showing all entities (including those with no connections)"
- [ ] Entities with 0 connections are visible

### Actual Results:
- Entity count: ______
- Helper text: ______

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 7: Filtering Correctness (minConnections = 100)

**Objective**: Verify filter correctly filters entities with 100+ connections

### Steps:
1. Navigate to Entities page
2. Set slider to 100
3. Check entity count
4. Check helper text below slider
5. Verify entities displayed all have 100+ connections

### Expected Results:
- [ ] Only entities with ≥100 connections shown
- [ ] Entity count reduced significantly
- [ ] Helper text shows: "Showing only entities with 100+ connections"
- [ ] No entities with <100 connections visible

### Actual Results:
- Entity count: ______
- Helper text: ______
- Sample entity connection counts: ______

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 8: Slider Stability with Other Filters

**Objective**: Verify slider max stays constant when applying other filters

### Steps:
1. Navigate to Entities page
2. Note slider max value
3. Apply search filter: "Trump"
4. Note slider max value
5. Change entity type to "Person"
6. Note slider max value
7. Enable "With Biography" filter
8. Note slider max value
9. Click a category badge
10. Note slider max value

### Expected Results:
- [ ] Slider max unchanged after search
- [ ] Slider max unchanged after entity type filter
- [ ] Slider max unchanged after biography filter
- [ ] Slider max unchanged after category filter
- [ ] All values should match: {record value}

### Actual Results:
| Filter Applied       | Slider Max Value | Changed? |
|----------------------|------------------|----------|
| Initial              |                  | N/A      |
| Search: "Trump"      |                  |          |
| Type: Person         |                  |          |
| With Biography       |                  |          |
| Category: Victims    |                  |          |

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 9: Performance Check

**Objective**: Verify no performance degradation from initial max fetch

### Steps:
1. Open Network tab in DevTools
2. Navigate to Entities page
3. Note initial API calls
4. Apply various filters
5. Navigate between pages
6. Check for additional API calls related to max connections

### Expected Results:
- [ ] One API call for max fetch on initial load (2000 entities)
- [ ] No additional max-related API calls on filter changes
- [ ] No additional max-related API calls on page navigation
- [ ] Page remains responsive

### Actual Results:
- Initial max fetch: ✅ / ❌
- Additional calls: ______
- Performance impact: ______

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Test Case 10: Pagination Works with Connection Filter

**Objective**: Verify pagination continues to work correctly with connection filter

### Steps:
1. Navigate to Entities page
2. Set minConnections to 50
3. Note entity count
4. Navigate to page 2
5. Check entities displayed
6. Navigate to page 3
7. Navigate back to page 1

### Expected Results:
- [ ] Pagination shows correct total pages for filtered results
- [ ] Page navigation works smoothly
- [ ] All entities on each page have ≥50 connections
- [ ] No errors in console

### Actual Results:
**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Regression Tests

### No Regressions in Other Features

**Objective**: Ensure other features still work as expected

#### Search Filter
- [ ] Search works correctly
- [ ] Debounce indicator appears
- [ ] Results update after 500ms

#### Entity Type Filter
- [ ] All/Person/Organization/Location filters work
- [ ] Entity counts update correctly

#### Biography Filter
- [ ] "With Biography" filter works
- [ ] Only entities with biographies shown when enabled

#### Category Filters
- [ ] Category badges are clickable
- [ ] Active filters bar appears
- [ ] Remove individual category works
- [ ] Clear all filters works

#### Entity Cards
- [ ] Entity names display correctly
- [ ] Entity icons show proper type
- [ ] Connection counts visible
- [ ] Document counts visible
- [ ] Biography summaries display
- [ ] Category badges show
- [ ] Source badges show

**Status**: ✅ Pass / ❌ Fail
**Notes**:

---

## Browser Compatibility Tests

### Test in Multiple Browsers

- [ ] Chrome/Chromium: _______
- [ ] Firefox: _______
- [ ] Safari: _______
- [ ] Edge: _______

**Notes**:

---

## Summary

### Overall Test Results
- **Total Tests**: 10 + Regressions
- **Passed**: ___
- **Failed**: ___
- **Blocked**: ___

### Critical Issues Found
[List any critical issues]

### Recommendations
[Any recommendations for improvements]

### Sign-off
- [ ] All tests passed
- [ ] Ready for deployment
- [ ] Issues logged for follow-up

**Tester**: _______________
**Date**: _______________
**Signature**: _______________

---

## Notes for Developers

### Known Issues Before Fix
1. Slider max changed per page (e.g., Page 1: 1431, Page 2: 777, Page 3: 272)
2. Decreasing slider was difficult due to jumping scale
3. No explanation of what "connections" meant

### Fix Implementation
1. Added `globalMaxConnections` state
2. Fetch global max once on mount
3. Removed dynamic max calculation
4. Updated slider and label to use global max
5. Added info tooltip for clarity

### Rollback Instructions
See `docs/implementation-summaries/connection-slider-global-max-fix.md` for detailed rollback steps.
