# Timeline Debug Checklist

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- [ ] Click **"Test API Directly"** button
- [ ] Check "Statistics" box shows: **"Total Events: 98"**
- [ ] Console shows green text: **"✅ API Response"**
- ✅ API works → Continue to next test
- ❌ API fails → Report API error (see bottom of checklist)

---

## 🎯 Quick Test Procedure (5 minutes)

Follow this checklist to diagnose the timeline issue:

---

## Step 1: Debug Test Page (2 min)

### Open Debug Page
```
URL: http://localhost:8081/timeline_debug_test.html
```

### Test API Directly
- [ ] Click **"Test API Directly"** button
- [ ] Check "Statistics" box shows: **"Total Events: 98"**
- [ ] Console shows green text: **"✅ API Response"**

**Result:**
- ✅ API works → Continue to next test
- ❌ API fails → Report API error (see bottom of checklist)

---

### Test Timeline Loading
- [ ] Click **"Load Timeline (Full Function)"** button
- [ ] Check "Statistics" box shows: **"Total Events: 104"**
- [ ] Scroll down - should see **104 event cards**
- [ ] Each card has: date, title, description, category tag

**Result:**
- ✅ Events appear → Timeline code works! Issue is in main app integration
- ❌ Events don't appear → Report rendering error (see bottom of checklist)

---

## Step 2: Main Application Test (3 min)

### Prepare Browser
- [ ] Open: http://localhost:8081/
- [ ] Press **F12** to open DevTools
- [ ] Click **"Console"** tab
- [ ] Clear console: Click 🚫 button or press **Ctrl+L**

### Test Timeline Tab
- [ ] Click **"Timeline"** tab in the application
- [ ] Watch console output carefully

**Expected Console Output:**
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

### Check Each Log Appears
- [ ] "🔄 Tab switched to timeline" ← Tab click detected
- [ ] "🔍 loadTimeline() called" ← Function started
- [ ] "📡 Fetching from:" ← API request sent
- [ ] "📊 Response status: 200 OK" ← API responded
- [ ] "✅ API data received" ← Data parsed successfully
- [ ] "📋 Total timeline data: 104" ← Data merged
- [ ] "🎨 About to render" ← Ready to display
- [ ] "🎨 renderTimeline() called" ← Render started
- [ ] "📦 Container element:" ← DOM element found
- [ ] "✅ Rendering X events" ← Render complete

---

## Step 3: Visual Verification

### Check Timeline Display
- [ ] Timeline area is visible (not empty)
- [ ] Events appear as cards with borders
- [ ] Each event shows: date, title, description
- [ ] Can scroll through events
- [ ] Statistics header shows correct counts

**If ALL checks pass:** ✅ Timeline is working!

**If ANY check fails:** ❌ Continue to troubleshooting

---

## 🔧 Troubleshooting Guide

### Issue A: No Console Logs Appear

**Symptoms:**
- [ ] No emoji logs in console
- [ ] Console completely silent when clicking Timeline tab

**Likely Cause:** Browser cache not cleared

**Fix:**
1. Hard refresh: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
2. Check Network tab
3. Look for: `app.js?v=20251118debug`
4. Verify it loaded (status 200)
5. If still cached, try Incognito/Private window

---

### Issue B: Stops at "Tab switched to timeline"

**Symptoms:**
- [ ] See "🔄 Tab switched to timeline"
- [ ] But NOT "🔍 loadTimeline() called"

**Likely Cause:** `loadTimeline()` function not defined or syntax error

**What to Check:**
1. Scroll up in console for earlier errors
2. Look for red error messages before clicking Timeline
3. Check if `loadTimeline is not defined` error appears

---

### Issue C: Stops at "Fetching from:"

**Symptoms:**
- [ ] See "📡 Fetching from: http://..."
- [ ] But NOT "📊 Response status:"

**Likely Cause:** Network request blocked or CORS error

**What to Check:**
1. Click **"Network"** tab in DevTools
2. Look for red failed request to `/api/timeline`
3. Check error message (CORS, timeout, refused, etc.)
4. Verify server is running: `ps aux | grep "python.*app.py"`

---

### Issue D: Response Status Not 200

**Symptoms:**
- [ ] See "📊 Response status: 404" or "500" or other error

**Likely Cause:** API endpoint error or server issue

**What to Check:**
1. Test API directly: `curl http://localhost:8081/api/timeline`
2. Check server console for Python errors
3. Verify server is running on port 8081

---

### Issue E: Filtered Data Length is 0

**Symptoms:**
- [ ] See "📋 Total timeline data: 104"
- [ ] But "📊 filteredTimelineData.length: 0"

**Likely Cause:** Filters are removing all events

**What to Check:**
1. Look for "🔍 applyTimelineFilters() called"
2. Check filter values shown in log
3. Reset filters in console:
   ```javascript
   timelineFilters = {type: 'all', startDate: null, endDate: null, search: ''};
   applyTimelineFilters();
   ```

---

### Issue F: Container Element Not Found

**Symptoms:**
- [ ] See "❌ CRITICAL: Container #timeline-events not found in DOM!"

**Likely Cause:** HTML element missing or wrong ID

**What to Check:**
1. Click **"Elements"** tab in DevTools
2. Press **Ctrl+F** to search
3. Search for: `timeline-events`
4. Verify element exists
5. Check if it's inside timeline tab content

---

### Issue G: Everything Logs Successfully But Timeline Empty

**Symptoms:**
- [ ] All console logs show success
- [ ] "✅ Rendering 104 events to container" appears
- [ ] But timeline area is blank/empty

**Likely Cause:** CSS hiding content or rendering blocked

**What to Check:**
1. Right-click empty timeline area
2. Click **"Inspect Element"**
3. Look at `<div id="timeline-events">`
4. Check if it has HTML content inside
5. Look for CSS: `display: none`, `visibility: hidden`, `height: 0`, `overflow: hidden`
6. Check parent elements for hiding styles

---

## 📋 Reporting Template

Copy this template and fill in your results:

```markdown
## Timeline Debug Report

**Date/Time:** [Current date and time]
**Browser:** [Chrome 120 / Firefox 119 / Safari 17 / Edge 120]

### Debug Test Page Results

**API Test:**
- Events returned: [Number or "Failed"]
- Status: [✅ Success / ❌ Failed]
- Error (if any): [Error message]

**Timeline Render Test:**
- Events displayed: [Number or "None"]
- Status: [✅ Success / ❌ Failed]
- Error (if any): [Error message]

### Main Application Results

**Console Output:**
[Paste FULL console output here - copy as text]

**Last Successful Log:**
[Which was the last emoji log that appeared?]

**First Missing Log:**
[Which expected log didn't appear?]

**Timeline Visible:**
[Yes / No / Partial]

**Visual Issues:**
[Describe what you see - empty, loading, error, etc.]

### Network Tab

**API Request Status:**
- /api/timeline: [200 OK / 404 / 500 / Failed / Not sent]

### Additional Information

**Error Messages:**
[Any red error messages in console]

**Warnings:**
[Any yellow warning messages]

**Other Observations:**
[Anything else unusual]

### Screenshots
[Attach if helpful]
- [ ] Timeline page screenshot
- [ ] Console output screenshot
- [ ] Network tab screenshot
```

---

## ✅ Success Indicators

You'll know timeline is working when:

- [ ] Debug test page shows 104 events
- [ ] Main app console shows all ✅ success logs
- [ ] Timeline displays scrollable event list
- [ ] No red errors in console
- [ ] Statistics show correct counts
- [ ] Events have dates, titles, descriptions
- [ ] Can search and filter events

---

## 🎯 Quick Command Reference

**Test API directly:**
```bash
curl -s http://localhost:8081/api/timeline | python3 -c "import sys, json; data = json.load(sys.stdin); print(f'Events: {len(data.get(\"events\", []))}')"
```

**Check server running:**
```bash
ps aux | grep "python.*app.py"
```

**Hard refresh browser:**
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Open DevTools:**
- All browsers: `F12`
- Mac alternative: `Cmd + Option + I`

**Clear console:**
- Click 🚫 button
- Or: `Ctrl + L`

---

## 📚 More Help

**Quick Start:** `TIMELINE_DEBUG_QUICKSTART.md`
**Detailed Guide:** `TIMELINE_DEBUG_INSTRUCTIONS.md`
**Full Summary:** `TIMELINE_DEBUG_SUMMARY.md`

---

**Status:** Ready for testing
**Next:** Complete checklist and report results
