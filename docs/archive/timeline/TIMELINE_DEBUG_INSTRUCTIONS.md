# Timeline Debug Instructions

## Problem
Timeline page shows empty despite all components appearing correct.

## Changes Made

### 1. Added Comprehensive Debug Logging

**File: `server/web/app.js`**

Added detailed console logging to track execution flow:

#### Global Error Handlers (Lines 4-14)
- Catches all JavaScript errors
- Catches unhandled promise rejections
- Logs error details including file, line, and column

#### loadTimeline() Function (Lines 3482-3533)
- Logs when function is called
- Logs baseline events count
- Logs API URL being fetched
- Logs response status
- Logs API data received
- Logs total timeline data count
- Logs filtered data count before render

#### renderTimeline() Function (Lines 3551-3578)
- Logs when function is called
- Logs filtered data length
- Logs container element status
- Alerts if container not found
- Logs number of events being rendered

#### switchTab() Function (Line 3292)
- Logs when timeline tab is activated
- Confirms loadTimeline() is being called

#### applyTimelineFilters() Function (Lines 3692-3730)
- Logs current filter values
- Logs timeline data length before filtering
- Logs filtered data length after filtering

### 2. Updated Cache Version

**File: `server/web/index.html`** (Line 5747)
- Changed from `v=20251118` to `v=20251118debug`
- Forces browser to fetch fresh JavaScript

### 3. Created Debug Test Page

**File: `server/web/timeline_debug_test.html`**

Standalone test page with features:
- Visual console output display
- Direct API test button
- Full timeline load test
- Event counter and statistics
- Simplified rendering for easier debugging

## Diagnostic Steps

### Step 1: Open Debug Test Page

```bash
# Open in browser:
http://localhost:8081/timeline_debug_test.html
```

**What to check:**
1. Click "Test API Directly" button
2. Check console output for API response
3. Verify event count matches expected (98 events)
4. Click "Load Timeline (Full Function)" button
5. Check if events render correctly

**Expected Output:**
```
🔍 Testing API directly...
📡 Fetching from: http://localhost:8081/api/timeline
📊 Response status: 200 OK
✅ API Response: {events: Array(98)}
📊 Events count: 98
```

### Step 2: Check Main Application

```bash
# Open main application:
http://localhost:8081/
```

**What to do:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Clear console (Ctrl+L)
4. Click Timeline tab
5. Watch console output

**Expected Console Flow:**
```
🔄 Tab switched to timeline - calling loadTimeline()
🔍 loadTimeline() called
📊 Baseline events: 6
📡 Fetching from: http://localhost:8081/api/timeline
📊 Response status: 200 OK
✅ API data received: {events: Array(98)}
📊 API events count: 98
📋 Total timeline data: 104 events
🎨 About to render 104 events
🎨 renderTimeline() called
📊 filteredTimelineData.length: 104
📦 Container element: <div id="timeline-events">
✅ Rendering 104 events to container
```

### Step 3: Identify the Break Point

Based on console output, identify where the process stops:

#### Scenario A: "Tab switched to timeline" NOT logged
**Problem:** Tab switching not working
**Check:**
- Is `switchTab('timeline')` being called?
- Check if tab click handler is attached
- Verify timeline tab button exists and has correct onclick

#### Scenario B: "loadTimeline() called" NOT logged
**Problem:** Function not being invoked
**Check:**
- Line 3292 in app.js
- Verify if statement condition is correct
- Check if tabName parameter is 'timeline'

#### Scenario C: API fetch fails or returns error
**Problem:** Backend API issue
**Check:**
- Network tab in DevTools
- Server console for errors
- API endpoint accessibility

#### Scenario D: Container element is null
**Problem:** DOM structure issue
**Check:**
- Search HTML for `id="timeline-events"`
- Verify element exists in timeline tab content
- Check if timeline tab content is rendered in DOM

#### Scenario E: filteredTimelineData.length is 0
**Problem:** Data being filtered out
**Check:**
- applyTimelineFilters() log output
- Current filter values (timelineFilters object)
- Check if filters are being applied unexpectedly

#### Scenario F: Everything logs correctly but timeline still empty
**Problem:** CSS hiding content or rendering issue
**Check:**
- Inspect timeline-events element in Elements tab
- Check if innerHTML is actually being set
- Look for CSS display: none or visibility: hidden
- Check for z-index issues

## Common Issues and Solutions

### Issue 1: Cache Not Cleared
**Symptoms:** Old version of app.js still running, debug logs not appearing
**Solution:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Clear browser cache
- Try incognito/private window
- Check Network tab to verify `app.js?v=20251118debug` is loaded

### Issue 2: API CORS Error
**Symptoms:** Console shows CORS error or network error
**Solution:**
- Check if server is running on port 8081
- Verify API_BASE is correct (should be auto-constructed)
- Check server CORS configuration

### Issue 3: JavaScript Error Before Timeline Code Runs
**Symptoms:** No timeline logs appear at all
**Solution:**
- Check for syntax errors in app.js
- Look for earlier errors in console
- Verify all dependencies loaded (lucide icons, etc.)

### Issue 4: Timeline Filters Removing All Events
**Symptoms:** filteredTimelineData.length is 0 despite timelineData having events
**Solution:**
- Check timelineFilters object values
- Reset filters to defaults
- Verify filter logic in applyTimelineFilters()

### Issue 5: Container Element Wrong ID
**Symptoms:** "Container #timeline-events not found in DOM!"
**Solution:**
- Search HTML file for actual container ID
- Update renderTimeline() to use correct ID
- Verify timeline tab content is in DOM

## Success Criteria

✅ **Timeline Working Correctly When:**
1. Console shows all expected debug logs
2. API returns 98 events (or expected count)
3. Total timeline data = 104 events (98 API + 6 baseline)
4. filteredTimelineData matches timelineData (initially)
5. Container element is found in DOM
6. Timeline events render visually on page
7. No JavaScript errors in console

## API Verification

Test API directly with curl:

```bash
curl -s http://localhost:8081/api/timeline | jq '.events | length'
# Should output: 98
```

## Files Modified

1. **server/web/app.js**
   - Added global error handlers (lines 4-14)
   - Enhanced loadTimeline() logging (lines 3482-3533)
   - Enhanced renderTimeline() logging (lines 3551-3578)
   - Enhanced switchTab() logging (line 3292)
   - Enhanced applyTimelineFilters() logging (lines 3692-3730)

2. **server/web/index.html**
   - Updated cache version to v=20251118debug (line 5747)

3. **server/web/timeline_debug_test.html** (NEW)
   - Standalone debug test page with visual console

## Next Steps

1. Open debug test page and verify API works in isolation
2. Open main app with DevTools console open
3. Click Timeline tab and watch console output
4. Identify where the flow breaks based on logs
5. Report findings with console output screenshots

## Reporting Issues

When reporting, include:
1. Full console output (copy/paste text)
2. Screenshot of timeline page
3. Network tab screenshot showing API requests
4. Browser and version
5. Any visible errors or warnings
6. Which diagnostic scenario (A-F) matches the symptoms
