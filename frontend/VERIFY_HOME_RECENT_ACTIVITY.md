# Visual Verification Guide: Home Page Recent Activity

## Quick Test Steps

### 1. Open the Home Page
Navigate to: **http://localhost:5173**

### 2. Locate the Recent Activity Section
Scroll down to find the "Recent Activity" section. It should be positioned:
- **After**: Dashboard Cards (with statistics)
- **Before**: The "About This Archive" section

### 3. Visual Checklist

#### Section Header
- [ ] "Recent Activity" title with calendar icon
- [ ] "Latest timeline events and news coverage" subtitle
- [ ] "View Full Timeline →" link in top-right

#### Loading State (Brief)
- [ ] Skeleton placeholders appear during data fetch
- [ ] Shows 5 skeleton items with circular icons

#### Timeline Events (📅)
Each timeline event should display:
- [ ] Circular icon badge (primary color) on left
- [ ] Category badge (biographical/case/documents) with appropriate color
- [ ] Formatted date (e.g., "Jan 1, 2020")
- [ ] Event title (clickable, links to /timeline)
- [ ] Event description (truncated to 2 lines)
- [ ] Related entities as small badges (max 3 shown, "+X more" if needed)
- [ ] Hover effect (light background highlight)

**Color Coding:**
- 🔵 Biographical: Blue background badge
- 🔴 Case: Red background badge
- 🟢 Documents: Green background badge

#### News Articles (📰)
Each news article should display:
- [ ] Circular icon badge (blue) with newspaper icon
- [ ] "News" badge in blue
- [ ] Formatted date (e.g., "Jan 1, 2020")
- [ ] Publication name (e.g., "• The New York Times")
- [ ] Article title (clickable external link)
- [ ] External link icon appears on hover
- [ ] Content excerpt (truncated to 2 lines)
- [ ] Entity mentions as small badges (max 3 shown, "+X more" if needed)
- [ ] Hover effect (light background highlight)

#### Combined Display
- [ ] Both timeline events and news articles appear in the same list
- [ ] Items sorted by date (most recent first)
- [ ] Maximum of 10 items total displayed
- [ ] Visual distinction between timeline and news items

#### Responsive Design
Test on different screen sizes:

**Desktop (>1024px):**
- [ ] Card takes full width
- [ ] Entity badges wrap properly
- [ ] Text doesn't overflow

**Tablet (768px-1024px):**
- [ ] Layout remains clean
- [ ] Badges wrap to new lines if needed

**Mobile (<768px):**
- [ ] Card is full width
- [ ] Icon badges remain visible
- [ ] Text truncation works correctly
- [ ] All content readable

### 4. Interaction Tests

#### Links
- [ ] Click event title → navigates to /timeline
- [ ] Click "View Full Timeline →" → navigates to /timeline
- [ ] Click news article title → opens in new tab
- [ ] External link icon appears on news article hover

#### Empty State (if no data)
- [ ] Shows calendar icon
- [ ] Displays "No recent activity found" message

### 5. Browser Console
Check for errors:
```javascript
// Open browser console (F12 or Cmd+Option+I)
// Should see:
[useTimelineNews] Effect triggered
[useTimelineNews] Starting fetch
[useTimelineNews] Fetch complete
[useTimelineNews] Articles grouped by date
```

**No errors should appear** related to:
- TypeScript type errors
- API fetch failures
- React rendering errors
- Missing dependencies

### 6. Network Tab
Check API calls:
- [ ] `GET /api/timeline` - returns timeline events
- [ ] `GET /api/news/articles?start_date=...&end_date=...&limit=10` - returns news articles
- [ ] Both requests complete successfully (200 OK)

### 7. Performance
- [ ] Section loads within 2-3 seconds
- [ ] Loading skeleton appears immediately
- [ ] Page remains usable during fetch
- [ ] No layout shift when data loads

## Expected Behavior Examples

### Sample Timeline Event Display
```
🔵 biographical                Jan 15, 1999
    Jeffrey Epstein purchases Little St. James Island
    Jeffrey Epstein acquires the private island in the US Virgin Islands for $7.95 million...
    [Jeffrey Epstein] [Virgin Islands] [Little St. James]
```

### Sample News Article Display
```
📰 News                        Jan 15, 2019 • Miami Herald
    Billionaire sex offender Jeffrey Epstein and his pals...
    A Miami Herald investigation reveals the full scope of a serial sex abuser...
    [Jeffrey Epstein] [Ghislaine Maxwell] [Alexander Acosta]
```

## Common Issues & Solutions

### Issue: Section doesn't appear
**Solution**:
1. Check browser console for errors
2. Verify backend is running on port 8081
3. Check Network tab for failed API requests

### Issue: Shows "No recent activity found"
**Solution**:
1. Verify timeline data exists: `curl http://localhost:8081/api/timeline`
2. Verify news data exists: `curl "http://localhost:8081/api/news/articles?limit=10"`
3. Check date range (last 30 days)

### Issue: Only timeline events or only news articles
**Solution**:
1. Check which API call failed in Network tab
2. Verify both APIs are accessible
3. Check console logs for fetch errors

### Issue: Items not sorted correctly
**Solution**:
1. Check browser console for sort errors
2. Verify dates are valid ISO format
3. Check combined array in React DevTools

## Test Passed ✅
If all checklist items pass, the Recent Activity section is working correctly!

## Screenshots
Take screenshots showing:
1. Full Home page with Recent Activity section visible
2. Close-up of Timeline event card
3. Close-up of News article card
4. Mobile view (responsive design)

Save screenshots to: `/Users/masa/Projects/epstein/frontend/screenshots/home-recent-activity/`
