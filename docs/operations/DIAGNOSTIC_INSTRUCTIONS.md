# Diagnostic Instructions for Broken UI

**Quick Summary**: - Server: ✓ Running on http://localhost:8081/...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Server: ✓ Running on http://localhost:8081/
- HTML: ✓ Loading correctly (180KB)
- JavaScript files: ✓ All loading (app.js, documents.js, hot-reload.js)
- APIs: ✓ All responding (/api/stats, /api/network, etc.)
- **Visual**: ✗ Blank white page

---

## Current Status
- Server: ✓ Running on http://localhost:8081/
- HTML: ✓ Loading correctly (180KB)
- JavaScript files: ✓ All loading (app.js, documents.js, hot-reload.js)
- APIs: ✓ All responding (/api/stats, /api/network, etc.)
- **Visual**: ✗ Blank white page

## Issue
A JavaScript runtime error is preventing the page from initializing.

## Diagnostic Steps

### 1. Open Browser DevTools
1. Open http://localhost:8081/ in your browser
2. Press F12 (Windows/Linux) or Cmd+Option+I (Mac)
3. Click the "Console" tab

### 2. Look for Errors
Check for any red error messages. Common patterns:

```
ReferenceError: [variable] is not defined
TypeError: Cannot read property 'X' of null
TypeError: Cannot read property 'X' of undefined
Uncaught Error: ...
```

### 3. Check Network Tab
1. Click "Network" tab in DevTools
2. Reload the page (F5 or Cmd+R)
3. Look for any red/failed requests
4. Check if all JavaScript files loaded (app.js, documents.js, hot-reload.js)

### 4. Collect Information
Please provide:
- [ ] Full text of any JavaScript errors (including stack trace)
- [ ] List of any failed network requests
- [ ] Screenshot of Console tab showing errors

## Manual Tests

### Test 1: Check if JavaScript is executing
Open Console tab and type:
```javascript
typeof switchTab
```
Expected: `"function"`
If you see `"undefined"`, the JavaScript files didn't load or execute.

### Test 2: Check if DOM elements exist
```javascript
document.getElementById('overview-view')
```
Expected: Should return an HTML element
If `null`, the HTML didn't render.

### Test 3: Check network data
```javascript
fetch('/api/stats').then(r => r.json()).then(console.log)
```
Expected: Should print stats object
If error, API connection failed.

### Test 4: Force initialization
Try manually calling the initialization:
```javascript
loadStats()
```
Watch console for any errors.

## Suspected Root Causes

Based on static analysis, possible issues:

1. **Async function failure**: One of these might be failing:
   - `loadStats()` (line 775 in app.js)
   - `loadNetworkData()` (line 1091)
   - `loadEntityBiographies()` (line 745)
   - `loadEntityTags()` (line 760)
   - `loadEntitiesList()`
   - `loadRecentCommits()`

2. **Missing DOM elements**: A `document.getElementById()` call might be returning `null`

3. **External library failure**:
   - D3.js (https://d3js.org/d3.v7.min.js)
   - Lucide icons (https://unpkg.com/lucide@latest)
   - Leaflet maps (https://unpkg.com/leaflet@1.9.4/dist/leaflet.js)

## Quick Fix Attempt

If the issue is recent, try reverting recent changes:

```bash
cd /Users/masa/Projects/epstein
git diff HEAD -- server/web/app.js server/web/documents.js
git log --oneline -5 -- server/web/
```

The `documents.js` file was added in the latest commit. Try reverting to see if that fixes it:

```bash
git stash
# Test if page works now
# If yes, the issue is in the recent changes
```

## Contact Developer

Please provide the console output and error messages so I can pinpoint the exact issue.
