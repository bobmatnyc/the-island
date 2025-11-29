# Entity Bio Clickable Cards - Testing Guide

**Feature**: Clickable bio preview cards with navigation to entity detail pages
**Component**: `EntityTooltip.tsx`
**Date**: 2025-11-25
**Status**: ✅ Ready for Testing

## Quick Test

### Fastest Way to Test

1. **Start the application**:
   ```bash
   cd /Users/masa/Projects/epstein
   ./scripts/operations/start_all.sh
   ```

2. **Open browser**: `http://localhost:3000`

3. **Navigate to Timeline page**:
   - Click "Timeline" in the navigation
   - Or go directly to: `http://localhost:3000/timeline`

4. **Find an entity mention** in any timeline card

5. **Hover over the entity name** (underlined text)
   - Bio card should appear
   - Card should have hover effect

6. **Click anywhere on the bio card**
   - Should navigate to entity detail page
   - URL should use GUID format: `/entities/{guid}/{slug}`

**Expected Result**: You're now on the entity detail page with full information.

## Detailed Testing Checklist

### Visual Tests

#### ✅ Hover Behavior
- [ ] Hover over entity name shows bio card
- [ ] Bio card appears within 300ms
- [ ] Card positioning is correct (not cut off)
- [ ] Card is readable (good contrast, proper sizing)

#### ✅ Visual Indicators
- [ ] Cursor changes to pointer when hovering over bio card
- [ ] Card background changes color on hover (subtle highlight)
- [ ] "View full profile →" text visible at bottom
- [ ] Arrow icon (→) appears next to text
- [ ] Transition is smooth (no jarring changes)

#### ✅ Content Display
- [ ] Entity name displayed correctly
- [ ] Occupation/role shown (if available)
- [ ] Bio summary text (2-3 sentences)
- [ ] Badges show correctly (Black Book, Billionaire, etc.)
- [ ] Flight count displayed (if > 0)

### Functional Tests

#### ✅ Navigation
- [ ] Clicking bio card navigates to entity detail page
- [ ] URL uses GUID format: `/entities/{guid}/{slug}`
- [ ] Entity detail page loads successfully
- [ ] Correct entity information shown
- [ ] Back button returns to previous page

#### ✅ Different Entity Types
Test with different entity types to ensure consistency:

**Person**:
- [ ] Test with "Jeffrey Epstein"
- [ ] Test with "Ghislaine Maxwell"
- [ ] Test with "Bill Clinton"

**Organization**:
- [ ] Test with organization entities (if available)
- [ ] Bio card should still be clickable

**Location**:
- [ ] Test with location entities (if available)
- [ ] Navigation should work the same

### Edge Cases

#### ✅ Entities Without Biographies
- [ ] Hover over entity without bio
- [ ] Should show "No biography available" message
- [ ] Card should NOT be clickable (no Link wrapper)

#### ✅ Entities Without GUIDs (Legacy)
- [ ] Some older entities may not have GUIDs
- [ ] Should fall back to ID-based URL: `/entities/{id}`
- [ ] Navigation should still work

#### ✅ Mobile/Touch Devices
- [ ] First tap shows bio card
- [ ] Second tap navigates to entity page
- [ ] Touch targets are adequate (not too small)

### Performance Tests

#### ✅ Speed
- [ ] Bio card appears quickly on first hover (<100ms)
- [ ] Subsequent hovers are instant (cached)
- [ ] Navigation is immediate (no lag)
- [ ] Page transition is smooth

#### ✅ Multiple Hovers
- [ ] Hover over 5+ different entities
- [ ] Each should show bio card correctly
- [ ] No performance degradation
- [ ] No memory leaks (check browser DevTools)

### Browser Compatibility

Test in multiple browsers:

#### Desktop Browsers
- [ ] **Chrome** (version 90+)
  - Hover effect works
  - Click navigation works
  - Cursor changes to pointer

- [ ] **Firefox** (version 88+)
  - Hover effect works
  - Click navigation works
  - Cursor changes to pointer

- [ ] **Safari** (version 14+)
  - Hover effect works
  - Click navigation works
  - Cursor changes to pointer

- [ ] **Edge** (Chromium-based)
  - Hover effect works
  - Click navigation works
  - Cursor changes to pointer

#### Mobile Browsers
- [ ] **iOS Safari**
  - Tap shows bio card
  - Second tap navigates
  - Touch targets adequate

- [ ] **Chrome Android**
  - Tap shows bio card
  - Second tap navigates
  - Touch targets adequate

### Accessibility Tests

#### ✅ Keyboard Navigation
- [ ] Tab to entity mention
- [ ] Enter/Space opens bio card
- [ ] Tab focuses on bio card link
- [ ] Enter navigates to entity page
- [ ] Esc closes bio card

#### ✅ Screen Reader Support
- [ ] Screen reader announces entity name
- [ ] Announces "link to entity detail page"
- [ ] Reads bio summary text
- [ ] Announces "View full profile link"

#### ✅ Focus States
- [ ] Focus outline visible when tabbing
- [ ] Focus outline has good contrast
- [ ] Focus moves logically (sequential)

## Common Testing Locations

### Where to Find Entity Tooltips

1. **Timeline Page** (`/timeline`)
   - Entity mentions in timeline cards
   - Most common place to test

2. **Document Viewer** (`/documents/{id}`)
   - Entity mentions in document text
   - Test entity detection feature

3. **News Articles** (`/news`)
   - Entity mentions in article cards
   - Test with multiple entities per article

4. **Network Graph** (`/network`)
   - Entity nodes (if tooltips enabled)
   - Test graph visualization interaction

## Test Data Recommendations

### High-Quality Test Entities

These entities have rich biography data and are good for testing:

1. **Jeffrey Epstein**
   - GUID: `43886eef-f28a-549d-8ae0-8409c2be68c4`
   - Has: Biography, occupation, badges
   - Best for comprehensive testing

2. **Ghislaine Maxwell**
   - GUID: `b8fa3f5b-2d18-5c4a-9e7f-1a2b3c4d5e6f` (example)
   - Has: Biography, black book badge
   - Good for female entity testing

3. **Bill Clinton**
   - GUID: (check database)
   - Has: Biography, billionaire badge
   - Good for political figure testing

4. **Shelley Lewis**
   - GUID: `58486cdd-8c38-5e26-a03c-02a5c58aa818`
   - Example from user's request
   - Test specific case mentioned

### Minimal Biography Entities

Test with entities that have minimal data:

- Lesser-known individuals
- Entities with only name (no bio)
- Entities with bio but no badges

## Issue Reporting

If you find any issues, report with this template:

```markdown
### Issue: [Brief Description]

**Component**: EntityTooltip (Bio Card)
**Severity**: [Critical/High/Medium/Low]

**Steps to Reproduce**:
1. Navigate to [page]
2. Hover over [entity name]
3. Click on bio card
4. Observe [issue]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Browser**: [Chrome/Firefox/Safari/Edge] [version]
**OS**: [macOS/Windows/Linux] [version]
**Device**: [Desktop/Mobile] [device model if mobile]

**Screenshots**: [Attach if relevant]

**Console Errors**: [Paste any errors from browser console]
```

## Debugging Tips

### If Bio Card Doesn't Appear
1. Check browser console for errors
2. Verify entity data exists: `console.log(entity)`
3. Check HoverCard is rendering: Inspect element
4. Verify hover delay (300ms) hasn't expired

### If Navigation Doesn't Work
1. Check if Link component rendered: Inspect element
2. Verify GUID exists: Check entity object
3. Check `getEntityUrl()` output: `console.log(getEntityUrl(entity))`
4. Verify React Router is working: Test other navigation

### If Visual Indicators Missing
1. Check CSS classes applied: Inspect element
2. Verify Tailwind classes: `hover:bg-accent`, `cursor-pointer`
3. Check browser supports hover effects (not mobile)
4. Verify color contrast (may be too subtle)

### If Performance is Slow
1. Check network tab: Is API call slow?
2. Check for cache: Second hover should be instant
3. Check memory usage: DevTools > Memory
4. Clear cache and reload: Hard refresh (Cmd+Shift+R)

## Automated Testing (Future)

### Test Cases to Automate

```typescript
describe('EntityTooltip', () => {
  it('should display bio card on hover', async () => {
    // Test hover trigger
  });

  it('should navigate on click', async () => {
    // Test navigation
  });

  it('should use GUID-based URL', async () => {
    // Test URL format
  });

  it('should show visual indicators', async () => {
    // Test hover effects
  });

  it('should handle entities without GUIDs', async () => {
    // Test fallback
  });
});
```

### Tools for Automation
- **Playwright**: End-to-end testing
- **React Testing Library**: Component testing
- **Jest**: Unit testing
- **Cypress**: Integration testing

## Success Criteria

### Feature Passes If:

✅ **Functionality**:
- Bio cards appear on hover
- Cards are clickable
- Navigation works to correct entity pages
- URLs use GUID format

✅ **Visual**:
- Hover effects visible
- Cursor changes to pointer
- "View full profile →" text shown
- Smooth transitions

✅ **Performance**:
- Bio cards appear quickly (<100ms first load)
- Subsequent hovers are instant (cached)
- No memory leaks or performance degradation

✅ **Compatibility**:
- Works in Chrome, Firefox, Safari, Edge
- Works on mobile (iOS/Android)
- Keyboard navigation functional
- Screen reader compatible

✅ **Edge Cases**:
- Handles entities without bios gracefully
- Falls back to ID-based URLs if no GUID
- No errors in console

### Feature Fails If:

❌ **Critical Issues**:
- Bio cards don't appear at all
- Clicking does nothing (no navigation)
- Navigation goes to wrong page
- Crashes or errors occur

❌ **Major Issues**:
- Visual indicators missing (cursor, hover effect)
- Performance is noticeably slow (>500ms)
- Doesn't work in major browsers (Chrome/Firefox)
- Keyboard navigation broken

❌ **Minor Issues**:
- Hover effect too subtle
- Text hard to read (poor contrast)
- Cursor doesn't change on hover
- Works in desktop but not mobile

## Post-Testing

After completing tests:

1. **Update this document** with any findings
2. **Report issues** using template above
3. **Document workarounds** for known issues
4. **Update success criteria** if needed
5. **Create follow-up tasks** for improvements

## Contact

For questions or issues:
- Check implementation doc: `docs/implementation-summaries/ENTITY_BIO_CLICKABLE_CARDS.md`
- Check visual comparison: `docs/implementation-summaries/ENTITY_BIO_VISUAL_COMPARISON.md`
- Review component code: `frontend/src/components/entity/EntityTooltip.tsx`

---

**Testing Status**: 🟡 Ready for Manual Testing
**Last Updated**: 2025-11-25
**Next Review**: After user acceptance testing
