# Testing Guide: Timeline Scrubber (1M-154)

## Quick Test Checklist

### Visual Inspection
1. **Navigate to**: http://localhost:5173/activity
2. **Verify**:
   - ✅ Timeline scrubber visible below header (full width card)
   - ✅ Year markers displayed (1995, 1998, 2001, 2004, 2006, etc.)
   - ✅ Activity density bars visible beneath slider
   - ✅ Selected year displayed with flight count
   - ✅ Dropdown selector REMOVED (no longer visible)

### Mouse Interactions
1. **Click Year Marker**:
   - Click any year label (e.g., "2002")
   - ✅ CalendarHeatmap updates to show that year
   - ✅ Selected year label turns bold/blue
   - ✅ Smooth transition (300ms)

2. **Drag Slider**:
   - Click and drag slider thumb
   - ✅ Year updates during drag (debounced 200ms)
   - ✅ CalendarHeatmap updates on release
   - ✅ Activity bars highlight hovered year

3. **Hover Activity Bars**:
   - Hover over activity density bars
   - ✅ Tooltip shows "Year: XXXX, Flights: YY"
   - ✅ Bar opacity changes (hover effect)
   - ✅ Click bar selects that year

### Keyboard Navigation
1. **Focus Slider**: Tab to slider component
2. **Test Keys**:
   - ✅ **Arrow Right**: Next year (e.g., 2002 → 2003)
   - ✅ **Arrow Left**: Previous year (e.g., 2002 → 2001)
   - ✅ **Arrow Up**: Next year (same as Right)
   - ✅ **Arrow Down**: Previous year (same as Left)
   - ✅ **Home**: Jump to first year (1995)
   - ✅ **End**: Jump to last year (2006)
   - ✅ Focus ring visible during navigation

### Mobile Testing (Responsive)
1. **Resize Browser** to mobile width (375px)
2. **Verify**:
   - ✅ Year markers show only start/end years
   - ✅ Slider still draggable with finger
   - ✅ Touch target large enough (44px minimum)
   - ✅ Activity bars visible and clickable
   - ✅ No horizontal scroll issues

### Accessibility Testing
1. **Screen Reader** (VoiceOver/NVDA):
   - Focus slider
   - ✅ Announces: "Year selection slider"
   - ✅ Announces current year and flight count
   - ✅ Arrow keys navigate with announcements
   - ✅ Instructions read by screen reader

2. **Keyboard-Only Navigation**:
   - Disable mouse
   - ✅ Tab to slider (focus visible)
   - ✅ All arrow keys work
   - ✅ No mouse required for full functionality

### Performance Testing
1. **Drag Performance**:
   - Open DevTools Performance tab
   - Record while dragging slider
   - ✅ Debounce prevents excessive re-renders
   - ✅ <100ms response time on release
   - ✅ No layout thrashing

2. **Console Check**:
   - Open browser console
   - Interact with slider
   - ✅ No errors or warnings
   - ✅ No React key warnings

### Edge Case Testing
1. **Empty State**:
   - Modify code to pass empty `years={[]}`
   - ✅ Shows "No year data available"

2. **Single Year**:
   - Pass `years={[2002]}`
   - ✅ Shows "2002" (static text, no slider)

3. **Network Failure**:
   - Block API request in DevTools Network tab
   - ✅ Falls back to default years
   - ✅ Slider still functional

## Expected Behavior

### Before (Dropdown)
- Small dropdown selector (150px width)
- Click → dropdown opens → scroll → select year
- No visual indication of activity across years
- 3-4 interactions to change year

### After (Timeline Scrubber)
- Full-width timeline with visual context
- Click year marker OR drag slider OR keyboard arrows
- Activity density visible at-a-glance
- 1-2 interactions to change year
- Better UX for temporal navigation

## Common Issues & Solutions

### Issue: Slider doesn't update CalendarHeatmap
**Solution**: Check browser console for API errors. Verify year is in available range.

### Issue: Activity bars show all gray
**Solution**: Verify `activityData` prop is passed. Check flight data API response.

### Issue: Keyboard navigation doesn't work
**Solution**: Ensure slider is focused (Tab key). Check for JavaScript errors.

### Issue: Mobile touch not responsive
**Solution**: Verify touch events not blocked by CSS. Check Radix Slider is mounted correctly.

## Browser Compatibility

Tested on:
- ✅ Chrome 120+ (macOS, Windows, Android)
- ✅ Safari 17+ (macOS, iOS)
- ✅ Firefox 121+ (macOS, Windows)
- ✅ Edge 120+ (Windows)

## Deployment Verification

After deployment:
1. Visit production URL
2. Navigate to Activity page
3. Verify slider visible and functional
4. Test on mobile device (not simulator)
5. Check browser console (no errors)
6. Verify CalendarHeatmap updates on year change

---

**Last Updated**: 2025-11-24
**Linear Ticket**: 1M-154
**Status**: Ready for QA ✅
