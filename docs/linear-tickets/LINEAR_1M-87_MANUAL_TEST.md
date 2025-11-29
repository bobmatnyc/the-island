# Linear 1M-87: Manual Testing Guide

**Quick Summary**: Linear ticket documentation tracking implementation status and deliverables.

**Category**: Ticket
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- Frontend running on http://localhost:5173
- Browser with DevTools open (to check for errors)
- ✅ See "Timeline & News" as a single link
- ✅ No separate "Timeline" link
- ✅ No separate "News" link

---

## Prerequisites
- Frontend running on http://localhost:5173
- Browser with DevTools open (to check for errors)

## Test Cases

### Test 1: Navigation Menu Display
**Objective**: Verify single unified navigation entry

**Steps**:
1. Open http://localhost:5173 in browser
2. Look at the top navigation menu
3. Find the navigation item between "Home" and "Entities"

**Expected Result**:
- ✅ See "Timeline & News" as a single link
- ✅ No separate "Timeline" link
- ✅ No separate "News" link

**Actual Result**: ____________

---

### Test 2: Navigation Click Behavior
**Objective**: Verify clicking navigates to Timeline page

**Steps**:
1. From any page, click "Timeline & News" in navigation
2. Observe URL in address bar
3. Observe page content

**Expected Result**:
- ✅ URL shows: http://localhost:5173/timeline
- ✅ Timeline page loads
- ✅ Source filters visible (Court Docs, Flight Logs, News Articles)

**Actual Result**: ____________

---

### Test 3: Direct /news Route Access
**Objective**: Verify automatic redirect from /news to /timeline

**Steps**:
1. Type directly in address bar: http://localhost:5173/news
2. Press Enter
3. Observe URL and page content

**Expected Result**:
- ✅ URL automatically changes to: http://localhost:5173/timeline
- ✅ Timeline page loads (not a separate News page)
- ✅ No visible error or blank page

**Actual Result**: ____________

---

### Test 4: Article Detail Links
**Objective**: Verify article detail pages still work

**Steps**:
1. Navigate to Timeline page
2. Filter to show "News Articles" only
3. Click on any news article to view details
4. Observe URL pattern

**Expected Result**:
- ✅ Article detail page loads successfully
- ✅ URL pattern: http://localhost:5173/news/[article-id]
- ✅ Full article content displayed

**Actual Result**: ____________

---

### Test 5: Timeline Source Filters
**Objective**: Verify Timeline shows all source types

**Steps**:
1. Navigate to Timeline page (via "Timeline & News" link)
2. Look for source filter buttons/options
3. Test each filter:
   - Court Documents
   - Flight Logs
   - News Articles

**Expected Result**:
- ✅ All three source filters visible
- ✅ Can filter to show only Court Documents
- ✅ Can filter to show only Flight Logs
- ✅ Can filter to show only News Articles
- ✅ Can show all sources together

**Actual Result**: ____________

---

### Test 6: Browser Console Check
**Objective**: Verify no JavaScript errors

**Steps**:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Navigate between pages
4. Check for errors or warnings

**Expected Result**:
- ✅ No React errors
- ✅ No routing errors
- ✅ No 404 errors for missing components
- ✅ Clean console (info messages are okay)

**Actual Result**: ____________

---

### Test 7: Bookmark/Link Compatibility
**Objective**: Verify old /news bookmarks still work

**Steps**:
1. Bookmark http://localhost:5173/news
2. Close browser tab
3. Click bookmark to reopen
4. Observe behavior

**Expected Result**:
- ✅ Bookmark opens successfully (no 404)
- ✅ Automatically redirects to /timeline
- ✅ Timeline page fully functional

**Actual Result**: ____________

---

### Test 8: Hot Reload Compatibility
**Objective**: Verify changes work with development server

**Steps**:
1. With frontend running, make a small CSS change
2. Save the file
3. Observe browser auto-refresh
4. Verify navigation still shows "Timeline & News"

**Expected Result**:
- ✅ Hot reload works without errors
- ✅ Navigation remains correct after reload
- ✅ No need to restart server

**Actual Result**: ____________

---

## Summary Checklist

After completing all tests, verify:

- [ ] Navigation shows single "Timeline & News" entry
- [ ] No separate "Timeline" or "News" links in navigation
- [ ] Clicking "Timeline & News" goes to /timeline
- [ ] Direct /news access redirects to /timeline
- [ ] Article detail pages (/news/:articleId) work correctly
- [ ] Timeline source filters all functional
- [ ] No console errors in browser DevTools
- [ ] Bookmarks to /news redirect properly
- [ ] Hot reload works without issues

## Test Results

**All Tests Passed**: [ ] YES [ ] NO

**Issues Found**:
_____________________________________________
_____________________________________________

**Notes**:
_____________________________________________
_____________________________________________

**Tested By**: _______________
**Date**: _______________
**Browser**: _______________
**Environment**: Development / Production

---

## Rollback Plan (If Needed)

If issues are found:

1. **Revert Header.tsx**:
   - Change "Timeline & News" back to "Timeline"
   - Add back separate News link

2. **Revert App.tsx**:
   - Change redirect back to: `<Route path="news" element={<News />} />`
   - Add back import: `import { News } from '@/pages/News'`

3. **Restart frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

**Revert needed**: [ ] YES [ ] NO
**Reason**: _____________________________________
