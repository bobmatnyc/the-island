# Multi-Select Category Filters - Manual Verification Guide

## Overview
This guide helps verify the multi-select category filter implementation on the Entities page.

## Prerequisites
- Frontend server running on http://localhost:5173
- Browser with developer tools open

## Verification Steps

### 1. Basic Multi-Select Functionality

**Test**: Select multiple categories
1. Navigate to `/entities`
2. Wait for entity cards to load
3. Click on a category badge (e.g., "Frequent Travelers") in any entity card
4. Observe:
   - ✅ Filter bar appears at the top
   - ✅ Category badge appears in filter bar with X icon
   - ✅ Entity count updates
   - ✅ URL updates: `?categories=frequent_travelers`
5. Click on a DIFFERENT category badge (e.g., "Associates")
6. Observe:
   - ✅ Second category appears in filter bar
   - ✅ Both badges visible with X icons
   - ✅ Entity count increases (OR logic)
   - ✅ URL updates: `?categories=frequent_travelers,associates`

**Expected Result**: Multiple categories can be selected and all show in filter bar.

---

### 2. Individual Badge Removal

**Test**: Remove one category from multiple selections
1. With 2+ categories selected (from step 1)
2. Click the X icon on the FIRST category badge in filter bar
3. Observe:
   - ✅ First category removed from filter bar
   - ✅ Second category remains
   - ✅ Entity count updates (fewer entities)
   - ✅ URL updates: `?categories=associates`

**Expected Result**: Individual categories can be removed independently.

---

### 3. Clear All Functionality

**Test**: Remove all filters at once
1. Select 2+ categories
2. Click "Clear All" button in filter bar
3. Observe:
   - ✅ Filter bar disappears completely
   - ✅ All entities shown again
   - ✅ URL parameter removed: no `?categories=...`

**Expected Result**: All filters removed with single click.

---

### 4. Toggle Behavior

**Test**: Click selected badge to deselect
1. Click a category badge (e.g., "Social Contacts")
2. Filter activates (filter bar appears)
3. Click the SAME category badge again in an entity card
4. Observe:
   - ✅ Category removed from filter
   - ✅ Filter bar disappears (if last category)
   - ✅ URL parameter removed

**Expected Result**: Badges toggle on/off when clicked.

---

### 5. Visual Selection Indicator

**Test**: Selected badges show visual feedback
1. Click a category badge (e.g., "Public Figures")
2. Scroll through entity cards
3. Observe badges for "Public Figures" in cards:
   - ✅ Checkmark (✓) appears next to label
   - ✅ Thicker border (2px vs 1px)
   - ✅ "ring-2 ring-offset-2" styling visible
   - ✅ Tooltip changes to "Remove..." instead of "Filter by..."

**Expected Result**: Selected badges are visually distinct from unselected.

---

### 6. URL Parameter Support

**Test**: Navigate with categories in URL
1. Navigate directly to: `/entities?categories=victims,co-conspirators,frequent_travelers`
2. Observe:
   - ✅ Filter bar appears automatically
   - ✅ All 3 categories shown as badges
   - ✅ Each badge has X icon
   - ✅ Entities filtered correctly
   - ✅ Entity count reflects filtered results

**Expected Result**: URL parameters initialize filter state correctly.

---

### 7. OR Logic Filtering

**Test**: Verify OR operation (not AND)
1. Select "Frequent Travelers" only
2. Note entity count (e.g., 50 entities)
3. Add "Social Contacts" to filter
4. Note new entity count (e.g., 120 entities)
5. Observe:
   - ✅ Entity count INCREASES or stays same (never decreases)
   - ✅ Entities with EITHER category are shown
   - ✅ Entities with BOTH categories appear once

**Expected Result**: Entities match if they have ANY selected category.

---

### 8. Entity Count Display

**Test**: Filter bar shows accurate count
1. Select any category
2. Check filter bar text
3. Observe:
   - ✅ Shows: "({count} entity)" or "({count} entities)"
   - ✅ Count is singular when count = 1
   - ✅ Count is plural when count ≠ 1
   - ✅ Count matches results below

**Expected Result**: Accurate entity count with correct pluralization.

---

### 9. Persistence Across Navigation

**Test**: Filter state persists in browser history
1. Select 2 categories
2. Navigate to a different page (e.g., Documents)
3. Click browser Back button
4. Observe:
   - ✅ Filter bar still shows selected categories
   - ✅ URL parameters preserved
   - ✅ Filtered entities still displayed

**Expected Result**: Filters preserved in browser history.

---

### 10. Mobile Responsiveness

**Test**: Filters work on mobile viewport
1. Open browser dev tools, switch to mobile view (375px width)
2. Select 3+ categories
3. Observe:
   - ✅ Filter badges wrap properly
   - ✅ "Clear All" button remains accessible
   - ✅ Touch targets are large enough (min 44x44px)
   - ✅ No horizontal scroll

**Expected Result**: Filters responsive and usable on mobile.

---

## Browser Console Verification

### Check Console Logs
1. Open browser console (F12)
2. Click a category badge
3. Look for:
   ```
   🟢 BADGE CLICKED - TOGGLING: frequent_travelers
   ```

**Expected**: Console log confirms toggle action.

### Check Network Tab
1. Open Network tab
2. Select/deselect categories
3. Observe:
   - ✅ No additional API calls triggered by filter changes
   - ✅ Filtering happens client-side only

**Expected**: No network requests for filter operations.

---

## Edge Cases

### Empty Filter State
1. Start with no filters
2. Observe:
   - ✅ No filter bar visible
   - ✅ All entities shown
   - ✅ No URL parameters

### Single Category
1. Select exactly one category
2. Observe:
   - ✅ Filter bar shows with one badge
   - ✅ "Clear All" still available
   - ✅ Singular "entity" text if count = 1

### All Categories Selected
1. Try selecting many different categories
2. Observe:
   - ✅ All show in filter bar (wraps if needed)
   - ✅ Performance remains smooth
   - ✅ "Clear All" works for all

---

## Accessibility Testing

### Keyboard Navigation
1. Tab through entity cards
2. Press Enter on category badge (when focused)
3. Observe:
   - ✅ Filter activates via keyboard
   - ✅ Focus moves logically
   - ✅ Focus ring visible

### Screen Reader Testing
1. Enable screen reader (NVDA/JAWS/VoiceOver)
2. Navigate to category badges
3. Verify:
   - ✅ Badge purpose announced
   - ✅ "Remove" vs "Filter by" state clear
   - ✅ Entity count announced

---

## Common Issues & Solutions

### Issue: Filter bar doesn't appear
**Check**:
- Are there entities with biographies loaded?
- Does at least one entity have the selected category?
- Check browser console for errors

### Issue: Multiple clicks don't add categories
**Check**:
- Are you clicking different categories?
- Same category toggles (removes if already selected)
- Check URL to see current state

### Issue: URL doesn't update
**Check**:
- React Router properly configured?
- Browser supports pushState?
- Check searchParams state in React DevTools

---

## Success Criteria Checklist

- ✅ Can select multiple categories simultaneously
- ✅ Filter bar shows all selected categories
- ✅ Each badge in filter bar has X for removal
- ✅ "Clear All" button removes all filters
- ✅ Selected badges in cards show checkmark
- ✅ URL parameter format: `?categories=cat1,cat2,cat3`
- ✅ OR logic: entities match ANY selected category
- ✅ Toggle behavior: click to deselect
- ✅ No TypeScript errors
- ✅ Build succeeds
- ✅ Responsive on mobile
- ✅ Keyboard accessible

---

## Automated Test Execution

Run the Playwright test suite:

```bash
cd /Users/masa/Projects/epstein
npx playwright test tests/qa/entity-multi-select-category-filters.spec.ts --headed
```

**Expected**: All tests pass ✓

---

## Rollback Instructions

If issues are found, revert to single-select:

```bash
git diff frontend/src/pages/Entities.tsx
git checkout frontend/src/pages/Entities.tsx
```

Then review commit: `git show HEAD` to see changes.
