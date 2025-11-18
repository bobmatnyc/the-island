# Entity Card Navigation - Testing Instructions

## Quick Start Testing

### 1. Start the Server
```bash
cd /Users/masa/Projects/epstein/server
python3 app.py
```

Server will start at: `http://localhost:8000`

### 2. Open in Browser
Navigate to: `http://localhost:8000`

### 3. Test Entity Card Buttons

#### Step-by-Step Test:
1. **Click on any entity card** in the Entities tab
2. **Observe the modal** - should show 4 buttons:
   - ✈️ Flights (with count badge)
   - 📄 Docs (with count badge)
   - 🔗 Network (with count badge)
   - 📅 Timeline (with count badge)

3. **Test Flights Button**:
   - Click "Flights" button
   - Modal should close
   - Page should switch to "Flights" tab
   - Filter should show only flights for that entity
   - URL should update to: `#flights?entity=EntityName`
   - Toast message should appear

4. **Test Docs Button**:
   - Go back to Entities tab
   - Click same entity card
   - Click "Docs" button
   - Should navigate to Documents tab with filter applied
   - URL should update to: `#documents?entity=EntityName`

5. **Test Network Button**:
   - Repeat for Network button
   - Should highlight entity in network graph
   - URL should update to: `#network?entity=EntityName`

6. **Test Timeline Button**:
   - Repeat for Timeline button
   - Should filter timeline events for that entity
   - URL should update to: `#timeline?entity=EntityName`

### 4. Test Deep Linking

#### Test URLs to Try:
```
http://localhost:8000/#flights?entity=Epstein,%20Jeffrey
http://localhost:8000/#documents?entity=Trump,%20Donald
http://localhost:8000/#network?entity=Clinton,%20Bill
http://localhost:8000/#timeline?entity=Maxwell,%20Ghislaine
```

**Expected Behavior**:
1. Open URL in new browser tab
2. Page loads normally
3. Automatically switches to specified tab
4. Filter is automatically applied
5. Relevant data is displayed

### 5. Test Disabled States

**Find an entity with limited data** (e.g., someone with documents but no flights):

1. Open their entity card
2. **Buttons with 0 count should be**:
   - Gray background (not blue)
   - Dimmed (40% opacity)
   - Not clickable
   - Badge shows "0"

3. **Buttons with data should be**:
   - Blue background
   - Full opacity
   - Clickable
   - Badge shows actual count

### 6. Test Button Hover Effects

**Enabled buttons**:
- Hover over → should lift up slightly
- Background darkens
- Shadow appears
- Cursor changes to pointer

**Disabled buttons**:
- Hover over → no effect
- Stays gray and dim
- Cursor shows "not-allowed"

## Browser Console Checks

### Open DevTools (F12)

#### Expected Console Output:
```
Filtering flights by entity: Epstein, Jeffrey
Switching to tab: flights
Applied flight filters
Toast: Showing flights for Epstein, Jeffrey
```

#### Should NOT See:
```
❌ Uncaught TypeError
❌ ReferenceError: filterTimelineByEntity is not defined
❌ Cannot read property 'value' of null
❌ Failed to load resource
```

## Visual Verification Checklist

- [ ] 4 buttons visible in entity modal
- [ ] Count badges display on right side of each button
- [ ] Icons render correctly (plane, file, network, calendar)
- [ ] Blue buttons for enabled, gray for disabled
- [ ] Hover effect works on enabled buttons only
- [ ] Modal closes when button clicked
- [ ] Tab switches correctly
- [ ] Filter applies automatically
- [ ] Toast notification appears
- [ ] URL hash updates in address bar

## Specific Test Cases

### Test Case 1: Jeffrey Epstein
**Expected Results**:
- Flights: > 0 (enabled, blue)
- Docs: > 0 (enabled, blue)
- Network: > 0 (enabled, blue)
- Timeline: > 0 (enabled, blue)

**Test**:
1. Open Epstein's entity card
2. Verify all 4 buttons are blue
3. Click each button and verify navigation
4. Check URL hash updates correctly

### Test Case 2: Entity with No Flights
**Expected Results**:
- Flights: 0 (disabled, gray)
- Docs: > 0 (enabled, blue)
- Network: varies
- Timeline: varies

**Test**:
1. Find entity with no flights
2. Verify Flights button is gray and disabled
3. Try clicking → should do nothing
4. Click enabled buttons → should work

### Test Case 3: Deep Link Sharing
**Test**:
1. Open entity card for "Trump, Donald"
2. Click "Documents" button
3. Copy URL from address bar: `#documents?entity=Trump,%20Donald`
4. Open URL in new tab
5. Verify it loads directly to Documents tab with filter applied

## Performance Testing

### Timing Expectations:
- **Modal open**: < 100ms
- **Button click to tab switch**: < 100ms
- **Filter application**: < 500ms (depends on data size)
- **URL hash update**: Instant

### Memory Testing:
1. Open and close 10 entity cards
2. Click different buttons each time
3. Check browser memory usage (should not continuously increase)
4. Verify no memory leaks in DevTools Performance tab

## Mobile Testing (Optional)

If testing on mobile/narrow screen:

- [ ] Buttons wrap to 2 columns on narrow screens
- [ ] All buttons remain clickable
- [ ] Touch targets are adequate (minimum 44x44px)
- [ ] Hover states work (or are disabled on touch)

## Regression Testing

### Verify Existing Features Still Work:
- [ ] Entity search/filtering
- [ ] Entity type filters
- [ ] Network graph interactions
- [ ] Document search
- [ ] Flight filtering
- [ ] Timeline filtering
- [ ] Theme switching (dark/light mode)

## Bug Report Template

If you find issues, report with this format:

```
### Bug: [Short description]

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Browser**: Chrome 120 / Firefox 121 / Safari 17
**Console Errors**: [Copy any errors from console]
**Screenshots**: [Attach if applicable]
```

## Success Criteria

Implementation is successful if:

✅ All 4 buttons appear in entity modal
✅ Count badges show accurate numbers
✅ Buttons navigate to correct tabs
✅ Filters apply automatically
✅ URL hash updates correctly
✅ Deep links work on page load
✅ Disabled buttons are non-interactive
✅ Hover effects work on enabled buttons
✅ No JavaScript console errors
✅ Toast notifications appear
✅ Modal closes on button click

## Common Issues and Solutions

### Issue: Counts Show as "0" for All Entities
**Solution**: Check that entity data is loaded before opening modal
**Fix**: Refresh page, wait for data to load

### Issue: Deep Links Don't Navigate
**Solution**: Check browser console for errors
**Fix**: Verify `handleHashNavigation()` is called on page load

### Issue: Buttons Don't Close Modal
**Solution**: Check that `closeEntityCard()` is called
**Fix**: Verify onclick handlers include `closeEntityCard()`

### Issue: Icons Don't Render
**Solution**: Check Lucide icons are loaded
**Fix**: Verify `lucide.createIcons()` is called after modal insert

## Final Verification

Before marking as complete:

1. **Test all 4 button types** (Flights, Docs, Network, Timeline)
2. **Test deep linking** with at least 2 different entities
3. **Test disabled states** with entity that has 0 counts
4. **Verify browser console** has no errors
5. **Check URL hash** updates correctly
6. **Confirm toast messages** appear
7. **Test across multiple entities** (at least 5 different ones)

## Questions to Answer

After testing, answer these:

- [ ] Do all buttons navigate correctly? (Yes/No)
- [ ] Are count badges accurate? (Yes/No)
- [ ] Do deep links work? (Yes/No)
- [ ] Are disabled buttons non-interactive? (Yes/No)
- [ ] Is the UI visually appealing? (Yes/No)
- [ ] Are there any console errors? (Yes/No)
- [ ] Does the implementation meet requirements? (Yes/No)

If all answers are Yes (except console errors = No), implementation is complete!
