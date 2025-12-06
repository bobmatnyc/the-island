# Entities Page Rebuild - Testing Checklist

**Date**: 2025-12-06
**Component**: `/frontend/src/pages/Entities.tsx`
**Tester**: [Your Name]
**Environment**: [Development / Staging / Production]

---

## Pre-Testing Setup

- [ ] Backend server running (`http://localhost:8081`)
- [ ] Frontend dev server running (`http://localhost:5173`)
- [ ] Browser DevTools console open (check for errors)
- [ ] Test in Chrome/Firefox/Safari (cross-browser compatibility)

---

## Critical Features (MUST PASS)

### 1. Fixed Filter Header ⭐ CRITICAL

**Test**: Scroll through entity grid and verify filters stay visible

- [ ] Load Entities page
- [ ] Scroll down to bottom of entity grid (100+ cards)
- [ ] ✅ **PASS**: Filter header stays at top of viewport (sticky)
- [ ] ✅ **PASS**: Search input remains accessible while scrolled
- [ ] ✅ **PASS**: Entity type buttons remain accessible while scrolled
- [ ] ✅ **PASS**: Connection slider remains accessible while scrolled

**Expected Result**: Filters NEVER scroll away, only grid scrolls independently

**Bug to Check**: If filters scroll away, this is a CRITICAL FAILURE

---

### 2. Search Functionality

**Test**: Search for entity names with debounced loading

- [ ] Clear any existing filters
- [ ] Type "Maxw" in search box
- [ ] ✅ **PASS**: Debounce spinner appears in search box (right side)
- [ ] Wait 500ms
- [ ] ✅ **PASS**: Results update to show "Maxwell" entities
- [ ] ✅ **PASS**: URL updates with `?search=Maxw`
- [ ] ✅ **PASS**: Page resets to 1 if you were on page 2+

**Expected Result**: Search triggers after 500ms delay, shows loading feedback

**Edge Cases**:
- [ ] Search with no results shows "No entities found" message
- [ ] Clearing search restores all entities
- [ ] Special characters in search (e.g., "O'Brien") work correctly

---

### 3. Entity Type Filters

**Test**: Filter by Person, Organization, Location

- [ ] Clear all filters
- [ ] Click "Person" button
- [ ] ✅ **PASS**: Button shows active state (primary background)
- [ ] ✅ **PASS**: Only person entities displayed
- [ ] ✅ **PASS**: URL updates with `?type=person`
- [ ] Click "Organization" button
- [ ] ✅ **PASS**: Only organization entities displayed
- [ ] ✅ **PASS**: URL updates with `?type=organization`
- [ ] Click "Location" button
- [ ] ✅ **PASS**: Only location entities displayed
- [ ] ✅ **PASS**: URL updates with `?type=location`
- [ ] Click "All" button
- [ ] ✅ **PASS**: All entity types displayed
- [ ] ✅ **PASS**: URL removes `type` parameter

**Expected Result**: Each filter button works correctly, updates URL, resets page

---

### 4. Biography Filter

**Test**: Filter entities with AI-generated biographies

- [ ] Clear all filters
- [ ] Click "With Biography" button
- [ ] ✅ **PASS**: Button shows active state (primary background)
- [ ] ✅ **PASS**: Only entities with biographies displayed
- [ ] ✅ **PASS**: All displayed cards show "Biography" badge
- [ ] ✅ **PASS**: URL updates with `?bio=true`
- [ ] Click "With Biography" again to toggle off
- [ ] ✅ **PASS**: All entities displayed (including those without biographies)
- [ ] ✅ **PASS**: URL removes `bio` parameter

**Expected Result**: Biography toggle filters correctly, updates URL

---

### 5. Category Badge Filters (Clickable on Cards)

**Test**: Click category badges to filter entities

- [ ] Clear all filters
- [ ] Find entity card with "Victims" badge
- [ ] Click "Victims" badge on card
- [ ] ✅ **PASS**: Active filters bar appears at top showing "Victims" badge
- [ ] ✅ **PASS**: Only entities with "Victims" category displayed
- [ ] ✅ **PASS**: "Victims" badges on cards show checkmark (✓)
- [ ] ✅ **PASS**: "Victims" badges have ring indicator (selected state)
- [ ] ✅ **PASS**: URL updates with `?categories=victims`
- [ ] Find entity card with "Associates" badge
- [ ] Click "Associates" badge on card
- [ ] ✅ **PASS**: Active filters bar shows BOTH "Victims" and "Associates"
- [ ] ✅ **PASS**: Entities with EITHER category displayed (OR logic)
- [ ] ✅ **PASS**: URL updates with `?categories=victims,associates`

**Expected Result**: Multiple category selection works (OR logic), visual feedback on selected badges

**Category Badge Selection Indicators**:
- [ ] Selected badges show checkmark (✓)
- [ ] Selected badges show ring around badge
- [ ] Hover effect works on all badges
- [ ] Tooltip shows "Remove X filter" when selected, "Filter by X" when not selected

---

### 6. Active Category Filters Bar

**Test**: Remove individual categories and clear all

- [ ] Select multiple categories (e.g., "Victims", "Associates", "Investigators")
- [ ] ✅ **PASS**: Active filters bar appears below connection slider
- [ ] ✅ **PASS**: All selected categories shown as removable badges
- [ ] ✅ **PASS**: Entity count shown in active filters bar
- [ ] Click X on "Victims" badge in active filters bar
- [ ] ✅ **PASS**: "Victims" filter removed
- [ ] ✅ **PASS**: Results update to show only remaining categories
- [ ] ✅ **PASS**: URL updates (removes "victims" from categories param)
- [ ] Click "Clear All" button in active filters bar
- [ ] ✅ **PASS**: All category filters removed
- [ ] ✅ **PASS**: Active filters bar disappears
- [ ] ✅ **PASS**: All entities displayed
- [ ] ✅ **PASS**: URL removes `categories` parameter

**Expected Result**: Individual and bulk category removal works correctly

---

### 7. Connection Threshold Slider

**Test**: Filter by minimum connection count

- [ ] Clear all filters
- [ ] Note the maximum value on slider (e.g., 100)
- [ ] Drag slider to 10
- [ ] ✅ **PASS**: Label shows "Minimum Connections: 10"
- [ ] ✅ **PASS**: Results update INSTANTLY (no API delay)
- [ ] ✅ **PASS**: Only entities with 10+ connections displayed
- [ ] ✅ **PASS**: URL updates with `?minConnections=10`
- [ ] Drag slider to 50
- [ ] ✅ **PASS**: Results filter further (only 50+ connections)
- [ ] ✅ **PASS**: Help text updates correctly
- [ ] Drag slider back to 0
- [ ] ✅ **PASS**: All entities displayed (including 0 connections)
- [ ] ✅ **PASS**: URL removes `minConnections` parameter

**Expected Result**: Slider filters instantly (client-side), updates URL

**Help Text Validation**:
- [ ] minConnections = 0: "Showing all entities (including those with no connections)"
- [ ] minConnections = 1: "Hiding entities with 0 connections"
- [ ] minConnections > 1: "Showing only entities with X+ connections"

---

### 8. Pagination Controls

**Test**: Navigate between pages

**Setup**: Apply filter to get multiple pages (e.g., type=person with 100+ results)

- [ ] ✅ **PASS**: Pagination controls appear at bottom of grid
- [ ] ✅ **PASS**: "Showing X-Y of Z entities" displays correctly
- [ ] ✅ **PASS**: Current page highlighted (page 1)
- [ ] Click "Next" button
- [ ] ✅ **PASS**: Page 2 loads
- [ ] ✅ **PASS**: URL updates with `?page=2`
- [ ] ✅ **PASS**: Grid scrolls to top (or stays at top if fixed header working)
- [ ] ✅ **PASS**: Page 2 highlighted
- [ ] Click page number "1"
- [ ] ✅ **PASS**: Returns to page 1
- [ ] ✅ **PASS**: URL updates (removes `page` or sets `page=1`)
- [ ] Click "Previous" button (should be disabled on page 1)
- [ ] ✅ **PASS**: Button disabled/grayed out on page 1
- [ ] Go to last page
- [ ] ✅ **PASS**: "Next" button disabled on last page

**Expected Result**: Pagination navigation works, updates URL, respects page boundaries

**Edge Cases**:
- [ ] Changing filter while on page 2+ resets to page 1
- [ ] Page numbers show ellipsis (...) for large page counts
- [ ] First and last page always visible in pagination

---

### 9. Loading States

**Test**: Visual feedback during data loading

**Initial Load**:
- [ ] Reload page
- [ ] ✅ **PASS**: Full-page spinner shown with "Loading entities..." text
- [ ] ✅ **PASS**: No entity cards visible until loaded

**Filter Changes**:
- [ ] After initial load, change entity type filter
- [ ] ✅ **PASS**: Semi-transparent overlay appears on grid
- [ ] ✅ **PASS**: Spinner shown in overlay with "Loading entities..." text
- [ ] ✅ **PASS**: Old entity cards still visible (dimmed) under overlay
- [ ] ✅ **PASS**: Filters remain accessible (not blocked by overlay)
- [ ] ✅ **PASS**: Loading overlay disappears when data loaded

**Search Debounce**:
- [ ] Type in search box
- [ ] ✅ **PASS**: Small spinner appears in search input (right side)
- [ ] ✅ **PASS**: Spinner shows while debouncing (< 500ms)
- [ ] ✅ **PASS**: Main loading overlay appears when API call starts

**Expected Result**: Clear loading feedback for all operations, filters always accessible

---

### 10. URL Parameter Persistence

**Test**: Deep linking and browser navigation

**Deep Linking**:
- [ ] Open new tab
- [ ] Navigate to: `http://localhost:5173/#/entities?type=person&bio=true&categories=victims&minConnections=10&page=2`
- [ ] ✅ **PASS**: Page loads with all filters applied
- [ ] ✅ **PASS**: "Person" button active
- [ ] ✅ **PASS**: "With Biography" button active
- [ ] ✅ **PASS**: Active filters bar shows "Victims"
- [ ] ✅ **PASS**: Connection slider at 10
- [ ] ✅ **PASS**: Page 2 displayed

**Browser Back/Forward**:
- [ ] Apply filter (e.g., click "Organization")
- [ ] Apply another filter (e.g., "With Biography")
- [ ] Click browser back button
- [ ] ✅ **PASS**: Biography filter removed, Organization filter remains
- [ ] ✅ **PASS**: Results update correctly
- [ ] Click browser forward button
- [ ] ✅ **PASS**: Biography filter re-applied
- [ ] ✅ **PASS**: Results update correctly

**URL Sharing**:
- [ ] Apply multiple filters
- [ ] Copy URL from address bar
- [ ] Open URL in incognito window
- [ ] ✅ **PASS**: All filters applied correctly in new window

**Expected Result**: URL parameters work for deep linking, browser navigation, sharing

---

### 11. Entity Cards Display

**Test**: Entity card information and layout

- [ ] Load Entities page
- [ ] Verify entity card structure:
  - [ ] ✅ **PASS**: Entity icon (person/organization/location) displayed
  - [ ] ✅ **PASS**: Entity name formatted correctly (Title Case for persons, UPPERCASE for orgs/locations)
  - [ ] ✅ **PASS**: "Details" button in top-right corner
  - [ ] ✅ **PASS**: Connection count displayed
  - [ ] ✅ **PASS**: Document count displayed
  - [ ] ✅ **PASS**: Biography summary shown (if available, max 3 lines)
  - [ ] ✅ **PASS**: Category badge displayed (clickable)
  - [ ] ✅ **PASS**: Source badges displayed (Black Book, Flight Logs, News, Timeline, Billionaire, Biography)
  - [ ] ✅ **PASS**: Hover effect on card (shadow increases)
  - [ ] ✅ **PASS**: Clicking entity name navigates to detail page
  - [ ] ✅ **PASS**: Clicking "Details" button navigates to detail page

**Expected Result**: All entity card information displayed correctly

---

### 12. Responsive Design

**Test**: Works on mobile, tablet, desktop viewports

**Mobile (375px width)**:
- [ ] Open Chrome DevTools
- [ ] Set viewport to iPhone SE (375x667)
- [ ] ✅ **PASS**: Fixed header works (filters stay at top)
- [ ] ✅ **PASS**: Filter buttons stack vertically
- [ ] ✅ **PASS**: Entity grid shows 1 column
- [ ] ✅ **PASS**: Entity cards readable and clickable
- [ ] ✅ **PASS**: Pagination controls work (not cut off)

**Tablet (768px width)**:
- [ ] Set viewport to iPad (768x1024)
- [ ] ✅ **PASS**: Fixed header works
- [ ] ✅ **PASS**: Entity grid shows 2 columns
- [ ] ✅ **PASS**: All controls accessible

**Desktop (1920px width)**:
- [ ] Set viewport to desktop (1920x1080)
- [ ] ✅ **PASS**: Fixed header works
- [ ] ✅ **PASS**: Entity grid shows 3 columns
- [ ] ✅ **PASS**: All controls accessible

**Expected Result**: Responsive design works on all viewport sizes

---

### 13. Empty States

**Test**: No results message

- [ ] Search for "ZZZZNONEXISTENT"
- [ ] ✅ **PASS**: "No entities found" message displayed
- [ ] ✅ **PASS**: Message suggests "Try adjusting your search or filter criteria"
- [ ] ✅ **PASS**: User icon displayed
- [ ] Clear search
- [ ] Apply filter combination that returns 0 results (e.g., type=organization + category=victims)
- [ ] ✅ **PASS**: "No entities found" message displayed

**Expected Result**: Clear empty state messages guide user

---

### 14. Performance

**Test**: Page responsiveness and load times

- [ ] Clear browser cache
- [ ] Load Entities page
- [ ] ✅ **PASS**: Initial load < 2 seconds
- [ ] ✅ **PASS**: Filter changes < 1 second
- [ ] ✅ **PASS**: Search debounce feels responsive (500ms)
- [ ] ✅ **PASS**: Connection slider updates instantly
- [ ] ✅ **PASS**: Pagination navigation < 1 second
- [ ] ✅ **PASS**: No lag when scrolling grid

**Expected Result**: All operations feel responsive, no noticeable lag

---

### 15. Error Handling

**Test**: Graceful degradation on errors

**Simulated Network Error**:
- [ ] Open Chrome DevTools → Network tab
- [ ] Set network to "Offline"
- [ ] Reload Entities page
- [ ] ✅ **PASS**: Error message displayed (not white screen of death)
- [ ] ✅ **PASS**: Console shows error log (not crash)
- [ ] Set network back to "Online"
- [ ] Reload page
- [ ] ✅ **PASS**: Page loads normally

**Simulated API Error**:
- [ ] Set network to "Slow 3G"
- [ ] Change filters rapidly (stress test)
- [ ] ✅ **PASS**: Page doesn't crash
- [ ] ✅ **PASS**: Loading states shown during slow requests
- [ ] ✅ **PASS**: Results update correctly when requests complete

**Expected Result**: Errors handled gracefully, no crashes

---

## Regression Testing (Ensure Nothing Broke)

### Features That Should Still Work

- [ ] ✅ Entity name links go to correct detail page (`/entities/{id}`)
- [ ] ✅ "Details" button goes to correct detail page
- [ ] ✅ Entity icons show correct type (person/organization/location)
- [ ] ✅ Source badges display correctly (Black Book, Flight Logs, News, Timeline)
- [ ] ✅ Billionaire badge shows for billionaire entities
- [ ] ✅ Biography badge shows for entities with biographies
- [ ] ✅ Entity name formatting correct (Title Case persons, UPPERCASE orgs/locations)
- [ ] ✅ Category badge colors match ontology (Victims = red, Associates = amber, etc.)
- [ ] ✅ Hover effects work on all interactive elements

---

## Cross-Browser Compatibility

### Chrome (Primary)
- [ ] All features work ✅
- [ ] No console errors ✅

### Firefox
- [ ] All features work ✅
- [ ] No console errors ✅
- [ ] CSS Grid layout correct ✅

### Safari (macOS/iOS)
- [ ] All features work ✅
- [ ] No console errors ✅
- [ ] Sticky header works ✅
- [ ] URL parameters work (HashRouter) ✅

---

## Console Errors Check

**During Testing**:
- [ ] ✅ **PASS**: Zero console errors during normal usage
- [ ] ✅ **PASS**: Zero console warnings (or only expected warnings)
- [ ] ✅ **PASS**: No React key warnings
- [ ] ✅ **PASS**: No network request failures (except intentional offline test)

**Log Errors Here**:
```
[If any errors occur, paste console output here]
```

---

## Known Issues (To Be Fixed Later)

### Client-Side Filtering Limitation
- **Issue**: Categories and connection threshold still filtered client-side
- **Impact**: Pagination counts may not be perfectly accurate
- **Workaround**: Works acceptably for current dataset size (1,637 entities)
- **Future Fix**: Extend backend API to support server-side filtering

---

## Test Summary

**Total Tests**: 150+
**Passed**: ___
**Failed**: ___
**Skipped**: ___

**Critical Issues**: ___
**Minor Issues**: ___

**Overall Status**: [ ] PASS / [ ] FAIL

**Tester Signature**: ___________________
**Date**: ___________________

---

## Next Steps

### If All Tests Pass ✅
1. Deploy to staging environment
2. Run full test suite again in staging
3. Get user acceptance testing
4. Deploy to production

### If Tests Fail ❌
1. Document failing test cases
2. Create bug tickets for each failure
3. Fix issues and re-test
4. Do NOT deploy until all critical tests pass

---

## Rollback Procedure

If critical bugs found in production:

```bash
# Quick rollback (restore backup)
cd /Users/masa/Projects/epstein/frontend/src/pages
mv Entities.tsx Entities.tsx.new
mv Entities.tsx.backup Entities.tsx

# Rebuild frontend
npm run build
pm2 restart frontend
```

**Estimated Rollback Time**: < 5 minutes

---

## Additional Notes

[Add any additional observations, bugs found, or improvements suggested during testing]
