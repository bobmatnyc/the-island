# UAT Test Report - User-Reported Issues

**Test Date**: 2025-11-19
**Test Environment**: Desktop (1920x1080), Chrome via Playwright
**Server URLs**:
- Frontend: http://localhost:5173/
- Backend API: http://localhost:8081/

---

## Issue 1: Dashboard Timeline Count

### User Report
- **Expected**: Timeline Events card should show "98"
- **Actual**: User reports seeing "TBD"

### Test Results
✅ **ISSUE PARTIALLY CONFIRMED** - Different from user report

**What's Actually Visible**:
- Timeline Events card shows **"0"** (zero), not "TBD"
- See screenshot: `dashboard_screenshot.png`

**Root Cause Analysis**:
```bash
$ curl http://localhost:8081/api/stats
{
  "timeline_events": 0,
  ...
}
```

The API is returning `timeline_events: 0`, so the frontend is correctly displaying the data it receives from the backend.

**Dashboard Code Behavior** (`src/pages/Dashboard.tsx:39`):
```tsx
{stats.timeline_events?.toLocaleString() || 'TBD'}
```

The code will show "TBD" only if:
- `stats.timeline_events` is `null` or `undefined`
- The API call fails or returns no data

Since the API returns `0`, the dashboard shows "0".

**Status**:
- ❌ Timeline count is **incorrect** (0 instead of 98)
- ✅ Frontend is **working correctly** (displaying API data)
- 🔧 Issue is in the **backend** (`/api/stats` endpoint)

---

## Issue 2: Chat Sidebar Missing

### User Report
- **Expected**: Left sidebar with "Search History" header and "New Chat" button should be visible
- **Actual**: User reports sidebar is missing

### Test Results
❌ **ISSUE NOT REPRODUCED** - Sidebar is fully visible

**What's Actually Visible**:
- ✅ Left sidebar is **present and visible**
- ✅ "Search History" header is visible
- ✅ "New" button (New Chat) is visible
- ✅ Sidebar is 300px wide
- ✅ No console errors
- See screenshot: `chat_screenshot.png`

**Technical Details**:
```json
{
  "sidebarExists": true,
  "sidebarVisible": true,
  "sidebarStyles": {
    "display": "block",
    "visibility": "visible",
    "width": "300px",
    "transform": "matrix(1, 0, 0, 1, 0, 0)",
    "opacity": "1",
    "position": "relative",
    "left": "0px"
  },
  "searchHistoryVisible": true,
  "newChatVisible": true,
  "viewportWidth": 1920,
  "isMobile": false
}
```

**Status**:
- ✅ Sidebar is **working correctly** on desktop (1920px viewport)
- ⚠️ **Possible user scenarios**:
  1. User might be on mobile/narrow viewport (< 768px) where sidebar is hidden by default
  2. User might have clicked the toggle button to hide it
  3. Browser window might be too narrow
  4. User might have different browser/OS rendering the CSS differently

**Recommendation**: Ask user for:
- Their screen width/viewport size
- Browser and OS version
- Screenshot from their end
- Whether they tried clicking the menu toggle button (☰)

---

## All Dashboard Stats (Current API Response)

```json
{
  "total_entities": 1702,          ✅ Shown correctly
  "total_documents": 38482,        ✅ Shown correctly
  "timeline_events": 0,            ❌ Should be 98
  "flight_count": null,            ⚠️ Shows "TBD" (API returns null)
  "network_nodes": 284,
  "network_edges": 1624
}
```

**Dashboard Cards Status**:
1. ❌ **Timeline Events**: Shows "0" (API issue - should be 98)
2. ✅ **Entities**: Shows "1,702" (correct)
3. ⚠️ **Flight Logs**: Shows "TBD" (API returns null/undefined)
4. ✅ **Documents**: Shows "38,482" (correct)
5. ✅ **Research Queue**: Shows "TBD" (intentional - hardcoded)

---

## Console Errors
**Dashboard**: None
**Chat Page**: None

---

## Recommendations

### Issue 1 - Timeline Count Fix (Backend)
**Priority**: HIGH

The backend API `/api/stats` needs to return the correct timeline_events count.

**Root Cause Identified**:
The bug is in `/Users/masa/Projects/epstein/server/app.py` line 786:

**Current (incorrect) code**:
```python
"timeline_events": timeline_data.get("total_events", 0),
```

**Timeline.json structure**:
```json
{
  "metadata": {
    "total_events": 98  ← The value is nested under "metadata"
  },
  "events": [...],
  "sources": [...]
}
```

**Fix needed**:
```python
"timeline_events": timeline_data.get("metadata", {}).get("total_events", 0),
```

**File to fix**:
- `/Users/masa/Projects/epstein/server/app.py` (line 786)

### Issue 2 - Chat Sidebar (User Environment)
**Priority**: LOW (Cannot reproduce - likely user-specific)

**Suggested user troubleshooting**:
1. Expand browser window to full screen
2. Check for mobile toggle button (☰) in top-left
3. Try different browser (Chrome, Firefox, Safari)
4. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
5. Check browser zoom level (should be 100%)
6. Clear localStorage: `localStorage.clear()` in browser console

---

## Test Artifacts

- ✅ `dashboard_screenshot.png` - Full dashboard view showing all stat cards
- ✅ `chat_screenshot.png` - Chat page with visible sidebar
- ✅ `test_results.json` - Complete automated test results
- ✅ `test_user_issues.js` - Playwright test script (reusable)

---

## Next Steps

1. **For Issue 1**: Investigate backend `/api/stats` endpoint
2. **For Issue 2**: Request user's browser environment details
3. **Optional**: Add backend API tests to verify timeline_events calculation
4. **Optional**: Add responsive testing for mobile viewports (320px, 768px, 1024px)
