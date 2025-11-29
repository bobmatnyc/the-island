# Bug Report: Bio Card Click Not Working

**Priority:** Medium
**Status:** Confirmed
**Discovered:** November 24, 2025
**Affected Feature:** Biography Display
**Browser Tested:** Chromium (Playwright)

## Summary

The Bio card on entity detail pages displays "View full biography" text but clicking the card does nothing. No modal opens, no navigation occurs, and no biography content is displayed.

## Steps to Reproduce

1. Navigate to entity detail page: `/entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein`
2. Locate the "Bio" card (shows "Bio" heading with "View full biography" subtext)
3. Click anywhere on the Bio card
4. **Expected:** Biography modal or expanded content should appear
5. **Actual:** Nothing happens, page remains unchanged

## Evidence

### Visual Proof
- Screenshot before click: `screenshots/bio-card-before-click.png`
- Screenshot after click: `screenshots/bio-card-after-click.png`
- Screenshots are identical - no change occurred

### Technical Details
```
Current URL before click: /entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein
Current URL after click:  /entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein

Modals found: 0
Biography content found: None
Long text blocks found: 0
```

## Affected Entities

Tested and confirmed on:
- Jeffrey Epstein (GUID: 43886eef-f28a-549d-8ae0-8409c2be68c4)
- Ghislaine Maxwell (GUID: 2b3bdb1f-adb2-5050-b437-e16a1fb476e8)

Likely affects **all entities with biographies** (at least 8 entities known to have bio data).

## Expected Behavior

When clicking the Bio card, one of these should happen:
1. **Modal opens** displaying full biography text
2. **Section expands** inline showing biography content
3. **Navigate** to dedicated biography page

## Actual Behavior

Nothing happens - the click has no effect.

## Investigation Findings

### DOM Structure
```html
<div class="bio-card">
  <icon> Bio
  View full biography
  <arrow-icon>
</div>
```

The card structure suggests it should be clickable (has arrow indicating navigation), but:
- No `<a>` tag found with bio link
- No `<button>` element for bio expansion
- No click handler appears to be attached to the Bio card div

### Console Errors
No JavaScript errors detected in browser console during click attempt.

## Impact Assessment

**User Impact:** High
- Users cannot access full biography content
- Feature is advertised ("View full biography") but non-functional
- Misleading UI - arrow suggests clickability but nothing happens

**Feature Completeness:** Partial
- ✅ Bio section is displayed on detail pages
- ✅ "View full biography" text is shown
- ❌ Click functionality is broken/missing
- ❌ No way to view full biography content

## Root Cause Hypothesis

1. **Missing click handler:** Bio card lacks onClick event handler
2. **Missing route:** No biography modal/page component implemented
3. **Incomplete feature:** UI was implemented but click functionality not yet added

## Recommended Fix

1. Add click handler to Bio card that either:
   - Opens a modal with full biography content
   - Navigates to a biography-specific page
   - Expands the bio inline on the current page

2. Fetch and display actual biography content (currently stored in database)

3. If biography is not ready, consider:
   - Hiding the "View full biography" text
   - Making the card non-clickable (remove arrow)
   - Displaying a "Coming Soon" message

## Workaround

Currently **no workaround available** for users to view full biography content through the UI.

## Test Coverage

This bug was discovered during E2E testing of:
- Bio summary display consistency
- GUID-based URL navigation

The Bio card appears correctly but functionality was not implemented.

## Related Files

Test files:
- `tests/qa/bio-card-click-test.js` - Reproduces the bug
- `tests/qa/bio-dom-inspect.js` - DOM structure inspection
- `tests/qa/screenshots/bio-card-*.png` - Visual evidence

## Next Steps

1. Implement click handler for Bio card
2. Create biography modal or expansion component
3. Fetch and display full biography content
4. Add E2E test to verify bio expansion works
5. Test with all entities that have biographies

---

**Tested by:** Web QA Agent
**Report Date:** November 24, 2025
