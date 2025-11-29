# Entity Bio Clickable Cards Implementation

**Date**: 2025-11-25
**Component**: `EntityTooltip.tsx`
**Feature**: Clickable bio preview cards with navigation to full entity detail pages

## Summary

Updated the EntityTooltip component to make bio cards fully clickable, allowing users to navigate directly from hover previews to full entity detail pages. This improves discoverability and provides a seamless path from bio preview to comprehensive entity information.

## Implementation Details

### Changes Made

**File**: `frontend/src/components/entity/EntityTooltip.tsx`

1. **Added Navigation Support**
   - Imported `Link` from `react-router-dom`
   - Imported `getEntityUrl` utility for GUID-based URL generation
   - Imported `ArrowRight` icon for visual indicator

2. **Wrapped Bio Content in Link**
   - Entire bio card content now wrapped in `<Link>` component
   - Uses `getEntityUrl(entity)` for proper URL generation
   - Supports both GUID-based and legacy ID-based URLs

3. **Added Visual Indicators**
   - Hover effect: `hover:bg-accent` on entire card
   - Cursor pointer: `cursor-pointer` class
   - "View full profile →" text at bottom with arrow icon
   - Smooth transition effect: `transition-colors`

4. **Updated Documentation**
   - Enhanced component docstring to explain clickable navigation
   - Documented GUID-based URL pattern
   - Added navigation trade-offs and design decisions

### URL Pattern

Bio cards now navigate to entity detail pages using stable GUID-based URLs:

```
/entities/{guid}/{slug}
```

**Examples**:
- `/entities/43886eef-f28a-549d-8ae0-8409c2be68c4/jeffrey-epstein`
- `/entities/58486cdd-8c38-5e26-a03c-02a5c58aa818/shelley-lewis`

**Backward Compatibility**: Falls back to ID-based URLs if GUID not available.

## Visual Design

### Before
- Bio card showed on hover but was not clickable
- No indication that card could be interacted with
- Users had to manually search for entity to view full details

### After
- Entire bio card is clickable link
- Hover effect shows background color change (`hover:bg-accent`)
- "View full profile →" text with arrow icon at bottom
- Cursor changes to pointer on hover
- Smooth transition animations

### Layout Structure

```
┌─────────────────────────────────────┐
│ [Icon] Entity Name                  │
│ [Icon] Occupation/Role              │
│                                     │
│ Biography summary text...           │
│ (2-3 sentences)                     │
│                                     │
│ ─────────────────────────────────  │
│ [Badge] [Badge] [Flight Count]      │
│ ─────────────────────────────────  │
│ View full profile →                 │
└─────────────────────────────────────┘
```

## Technical Implementation

### Component Structure

```tsx
<Link
  to={getEntityUrl(entity)}
  className="block space-y-3 rounded-md p-2 -m-2 transition-colors hover:bg-accent cursor-pointer"
>
  {/* Entity Name Section */}
  <div className="space-y-1">
    <div className="flex items-center gap-2">
      <User className="h-4 w-4 text-muted-foreground" />
      <h4 className="text-sm font-semibold leading-none">
        {entityName || entity.name}
      </h4>
    </div>

    {/* Occupation/Role */}
    {getOccupation(entity) && (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Briefcase className="h-3 w-3" />
        <span>{getOccupation(entity)}</span>
      </div>
    )}
  </div>

  {/* Bio Summary */}
  <p className="text-sm text-foreground leading-relaxed">
    {getBioSummary(entity)}
  </p>

  {/* Entity Metadata Badges */}
  <div className="flex flex-wrap gap-2 pt-2 border-t">
    {/* Badges and metadata */}
  </div>

  {/* View Full Profile Link */}
  <div className="flex items-center gap-1.5 text-xs text-primary font-medium pt-2 border-t">
    <span>View full profile</span>
    <ArrowRight className="h-3 w-3" />
  </div>
</Link>
```

### Key Features

1. **GUID Resolution**
   - Uses existing `entity.guid` field from fetched entity data
   - No additional API call needed (GUID already in entity response)
   - `getEntityUrl()` handles GUID → URL conversion automatically

2. **Performance**
   - No performance impact (no extra API calls)
   - Leverages existing entity fetch from hover action
   - GUID already included in cached entity data

3. **Accessibility**
   - Full keyboard navigation support (Link component)
   - Screen reader friendly (semantic link element)
   - Focus states handled by Radix UI HoverCard

4. **Responsive Design**
   - Padding/margin adjustment (`p-2 -m-2`) maintains card spacing
   - Smooth hover transitions
   - Mobile-friendly touch targets

## Usage Examples

### In Timeline Component
```tsx
<EntityTooltip entityId="jeffrey_epstein">
  <span className="cursor-help underline decoration-dotted">
    Jeffrey Epstein
  </span>
</EntityTooltip>
```

**Behavior**:
1. User hovers over "Jeffrey Epstein" text
2. Bio card appears with preview information
3. User sees "View full profile →" text at bottom
4. Clicking anywhere on bio card navigates to `/entities/{guid}/jeffrey-epstein`
5. Entity detail page loads with full information

### In Document Viewer
```tsx
<EntityTooltip entityId={entityId} entityName={entityName}>
  <button className="text-primary hover:underline">
    {entityName}
  </button>
</EntityTooltip>
```

**Behavior**: Same as above, but wraps a button element instead of plain text.

## Testing

### Manual Testing Checklist

- [x] Hover over entity name shows bio card
- [x] Bio card has hover effect (background color change)
- [x] Cursor changes to pointer when hovering card
- [x] "View full profile →" text visible at bottom
- [ ] Clicking bio card navigates to entity detail page
- [ ] Entity detail page loads correctly
- [ ] URL uses GUID format: `/entities/{guid}/{slug}`
- [ ] Back button returns to previous page
- [ ] Works on different entity types (person, organization)
- [ ] Works with entities that have/don't have GUIDs

### Browser Testing

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers (iOS Safari, Chrome Android)

### Accessibility Testing

- [ ] Keyboard navigation (Tab to trigger, Enter to click)
- [ ] Screen reader announces link properly
- [ ] Focus states visible
- [ ] Touch targets adequate for mobile

## Edge Cases Handled

1. **No GUID Available**
   - Falls back to legacy ID-based URL
   - `getEntityUrl()` handles this automatically
   - Example: `/entities/jeffrey_epstein` (without GUID)

2. **No Biography Data**
   - Shows "No biography information available" message
   - Does not render clickable link (nothing to navigate to)

3. **API Fetch Failure**
   - Error state shows "Biography not available"
   - No clickable link rendered (graceful degradation)

4. **Loading State**
   - Skeleton shown while fetching entity data
   - No link rendered until data loaded

## Performance Impact

**Net LOC Impact**: +15 lines (added visual indicator section)

**Performance Metrics**:
- No additional API calls (uses existing entity fetch)
- No JavaScript execution overhead (React Router Link optimization)
- Minimal CSS overhead (utility classes, no custom CSS)

**Memory Impact**:
- Negligible (Link component reuses existing entity data)
- No new state management required

## Future Enhancements

1. **Prefetch Entity Page**
   - Prefetch entity detail page on hover (before click)
   - Reduces perceived navigation delay
   - Implement with React Router `<Link prefetch>`

2. **Open in New Tab**
   - Add Ctrl/Cmd+Click support for new tab
   - Currently supported by default (browser behavior)

3. **Analytics Tracking**
   - Track bio card → entity detail navigation
   - Measure conversion rate (hover → click)

4. **Keyboard Shortcuts**
   - Add hint for "Press Enter to view full profile"
   - Improve keyboard user experience

## Related Components

- **EntityDetail.tsx**: Destination page for navigation
- **Entities.tsx**: Grid view with clickable entity cards
- **getEntityUrl()**: Utility for GUID-based URL generation
- **EntityLinks.tsx**: Navigation cards in entity detail view

## Documentation Updates

- Updated component docstring with navigation details
- Added trade-offs section for clickable navigation
- Documented GUID-based URL pattern
- Added usage examples with navigation behavior

## Dependencies

**No new dependencies added**. Uses existing libraries:
- `react-router-dom` (already in project)
- `lucide-react` (already in project, added ArrowRight icon)
- Radix UI HoverCard (already in project)

## Rollback Plan

If issues arise, revert to previous version:

```bash
git checkout HEAD~1 -- frontend/src/components/entity/EntityTooltip.tsx
```

**Impact**: Bio cards will no longer be clickable, but hover preview will still work.

## Deployment Notes

- No backend changes required
- No database migrations needed
- No configuration changes needed
- Frontend build required (`npm run build`)

## Success Criteria

✅ **Completed**:
1. Bio cards are clickable
2. Visual indicators present (hover effect, cursor, "View full profile →")
3. Navigation uses GUID-based URLs
4. TypeScript compiles without errors
5. Backward compatible with legacy IDs

⏳ **Pending User Verification**:
1. Manual testing on live site
2. User acceptance testing
3. Cross-browser verification

## Files Modified

1. `frontend/src/components/entity/EntityTooltip.tsx` (+15 lines)
   - Added Link wrapper
   - Added visual indicators
   - Updated documentation

**Total Net LOC**: +15 lines

## Conclusion

Successfully implemented clickable bio cards with minimal code changes and zero performance impact. The feature provides a natural navigation path from entity previews to full detail pages, improving user experience and entity discoverability.

**Key Benefits**:
- Improved user experience (fewer clicks to view full entity info)
- Better entity discoverability (tooltips now actionable)
- Consistent with modern web UX patterns (clickable cards)
- Stable URLs using GUIDs (future-proof navigation)
- Zero performance overhead (leverages existing data)

---

**Next Steps**: User testing and cross-browser verification
