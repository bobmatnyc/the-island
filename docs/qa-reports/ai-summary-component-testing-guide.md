# AI Summary Component Testing Guide

**Component**: DocumentSummary + DocumentDetail
**Date**: 2025-11-26
**Status**: Ready for QA Testing

## Quick Test URLs

Assuming backend running on `http://localhost:8081` and frontend on `http://localhost:5173`:

```
# Test with any document ID from your system
http://localhost:5173/documents/{document-id}

# Example (replace with actual document ID):
http://localhost:5173/documents/6250471
```

## Test Scenarios

### 1. Happy Path: Cached Summary

**Steps**:
1. Navigate to document detail page
2. Observe AI Summary section loads

**Expected Result**:
```
✅ Loading spinner appears briefly (< 2 seconds)
✅ Summary card appears with purple sparkle icon
✅ Summary text displays (200-300 words)
✅ "Cached" badge visible in top-right
✅ Metadata shows: Model name, date/time, "Instant retrieval"
✅ Download button is prominent and clickable
```

**Screenshot Points**:
- [ ] Full page layout
- [ ] Summary card with cache badge
- [ ] Download button placement

---

### 2. Happy Path: Fresh Summary (First Generation)

**Steps**:
1. Navigate to document that hasn't been summarized yet
2. Observe loading state

**Expected Result**:
```
✅ Loading message: "Generating AI Summary..."
✅ Subtext: "This may take 5-10 seconds"
✅ Spinner animates
✅ After 5-10s, summary appears
✅ NO "Cached" badge (first generation)
✅ Metadata shows generation timestamp
```

---

### 3. Download Functionality

**Steps**:
1. Navigate to any document
2. Click "Download Full PDF" button

**Expected Result**:
```
✅ New tab/window opens
✅ PDF download begins automatically
✅ File saves to Downloads folder
✅ Filename matches document filename
```

---

### 4. PDF Viewer: Small Files (<5MB)

**Steps**:
1. Navigate to document <5MB in size
2. Observe "View in Browser" button appears
3. Click "View in Browser"

**Expected Result**:
```
✅ "View in Browser" button visible
✅ Click expands PDF viewer section
✅ PDF renders in browser (react-pdf viewer)
✅ PDF navigation controls work (page prev/next, zoom)
✅ "Hide Viewer" button appears
✅ Click "Hide Viewer" collapses viewer
```

---

### 5. Large Files (>5MB)

**Steps**:
1. Navigate to document >5MB in size
2. Observe UI differences

**Expected Result**:
```
✅ NO "View in Browser" button
✅ Blue informational message appears:
    "Large file detected: This document is too large to view in the browser.
     Please download it to view the full PDF."
✅ Download button still works
✅ Summary still loads correctly
```

---

### 6. Error: Document Not Found (404)

**Steps**:
1. Navigate to `/documents/invalid-id-12345`
2. Observe error handling

**Expected Result**:
```
✅ Red destructive alert appears
✅ Alert title: "Document Not Found"
✅ Alert message: "Document not found. Please check the document ID."
✅ No loading spinner stuck
✅ Download button hidden or disabled
```

---

### 7. Error: Scanned PDF Without OCR (422)

**Steps**:
1. Navigate to scanned document without OCR text
2. Observe error handling

**Expected Result**:
```
✅ Default (non-red) alert appears
✅ Alert title: "OCR Text Unavailable"
✅ Alert message: "This is a scanned document without OCR text.
                  Please download the PDF to view it."
✅ Download button still works
```

---

### 8. Error: AI Service Unavailable (503)

**Simulation**:
1. Stop backend AI service (or mock 503 response)
2. Navigate to document

**Expected Result**:
```
✅ Red destructive alert appears
✅ Alert title: "Service Unavailable"
✅ Alert message: "Unable to generate summary at this time.
                  Please try again or download the PDF."
✅ Download button still works
```

---

### 9. Error: Network/Backend Down

**Simulation**:
1. Stop backend server completely
2. Navigate to document detail page

**Expected Result**:
```
✅ Red destructive alert appears
✅ Alert title: "Connection Error"
✅ Alert message includes: "Cannot connect to backend server at http://localhost:8081"
✅ Helpful message about ensuring backend is running
✅ Page doesn't crash (graceful degradation)
```

---

## Visual Regression Tests

### Desktop Layout
- [ ] Summary card displays full-width with padding
- [ ] Download button is large and prominent
- [ ] Metadata footer is readable and aligned
- [ ] PDF viewer (when shown) doesn't overflow

### Mobile Layout (< 768px)
- [ ] Summary card stacks properly
- [ ] Download button remains full-width on mobile
- [ ] Metadata wraps to multiple lines
- [ ] Text remains readable (no tiny fonts)

### Dark Mode
- [ ] Summary card has proper dark background
- [ ] Purple sparkle icon visible in dark mode
- [ ] Alert colors have sufficient contrast
- [ ] Cache badge readable in dark mode

---

## Performance Tests

### Initial Load Time
```
Measure time from page load to summary displayed:

Target: < 2 seconds (cached)
Target: < 10 seconds (fresh generation)

Test with Chrome DevTools Network tab (throttle to "Fast 3G")
```

### Browser Compatibility
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

---

## Accessibility Tests

### Keyboard Navigation
- [ ] Tab through all interactive elements
- [ ] Download button focusable and activatable with Enter
- [ ] View in Browser button focusable
- [ ] Focus indicators visible

### Screen Reader
- [ ] Summary card announces correctly
- [ ] Alert messages announce with proper role
- [ ] Button labels are clear and descriptive

### Color Contrast
- [ ] All text meets WCAG AA (4.5:1 for normal text)
- [ ] Alert icons and text have sufficient contrast
- [ ] Links and buttons are distinguishable

---

## API Integration Tests

### Backend Contract Verification

**Test 1: Successful Response**
```bash
curl -X GET "http://localhost:8081/api/documents/6250471/ai-summary" \
  -H "Content-Type: application/json"

Expected Response:
{
  "document_id": "6250471",
  "summary": "This document...",
  "summary_generated_at": "2025-11-26T18:00:00Z",
  "summary_model": "x-ai/grok-4.1-fast:free",
  "word_count": 250,
  "from_cache": true
}
```

**Test 2: 404 Error**
```bash
curl -X GET "http://localhost:8081/api/documents/invalid-id/ai-summary" \
  -H "Content-Type: application/json"

Expected Response: 404 Not Found
{
  "detail": "Document not found"
}
```

**Test 3: 422 Error (No OCR)**
```bash
# Document without OCR text
curl -X GET "http://localhost:8081/api/documents/{scanned-doc-id}/ai-summary" \
  -H "Content-Type: application/json"

Expected Response: 422 Unprocessable Entity
{
  "detail": "Document has no extractable text"
}
```

---

## Manual Test Checklist

### Before Testing
- [ ] Backend server running (`python3 server/app.py 8081`)
- [ ] Frontend dev server running (`cd frontend && npm run dev`)
- [ ] Browser DevTools open (Console + Network tabs)

### Core Functionality
- [ ] AI summary loads for valid document
- [ ] Loading state displays correctly
- [ ] Cache indicator shows for cached summaries
- [ ] Download button downloads correct file
- [ ] View in Browser button appears for small files
- [ ] View in Browser button hidden for large files
- [ ] PDF viewer renders correctly (small files)
- [ ] Toggle button shows/hides viewer

### Error Handling
- [ ] 404 error displays correct message
- [ ] 422 error (no OCR) displays non-destructive alert
- [ ] 503 error displays service unavailable message
- [ ] Network error displays connection message
- [ ] All errors allow download button to work

### UI/UX
- [ ] Layout matches design spec
- [ ] Spacing and padding consistent
- [ ] Icons render correctly
- [ ] Badges display properly
- [ ] Responsive on mobile devices
- [ ] Dark mode styling correct
- [ ] No console errors or warnings

### Performance
- [ ] Cached summary loads in < 2 seconds
- [ ] Fresh summary generates in < 10 seconds
- [ ] PDF viewer doesn't block summary loading
- [ ] No memory leaks (check DevTools Memory tab)

---

## Bug Reporting Template

If you find issues, report using this format:

```markdown
## Bug Report: [Brief Description]

**Severity**: Critical / High / Medium / Low
**Environment**:
- Browser: [Chrome 120 / Firefox 121 / Safari 17]
- OS: [macOS 14 / Windows 11 / Ubuntu 22.04]
- Backend: [Running / Not Running]

**Steps to Reproduce**:
1. Navigate to /documents/123
2. Click "Download Full PDF"
3. Observe...

**Expected Behavior**:
Download should start immediately

**Actual Behavior**:
Download button does nothing, console shows error

**Console Errors**:
```
Error: Failed to fetch...
```

**Screenshots**:
[Attach screenshots]

**Suggested Fix** (optional):
Check CORS headers on download endpoint
```

---

## Success Criteria

Test passes if:

✅ All happy path scenarios work
✅ All error scenarios handled gracefully
✅ No console errors or warnings
✅ Performance targets met
✅ Mobile responsive works
✅ Dark mode works
✅ Accessibility requirements met
✅ Download functionality works in all states

---

**QA Sign-off**: _________________ Date: _________
