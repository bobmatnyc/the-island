# Testing Guide - UI Bug Fixes

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ All entity names display as single, clean text
- ✅ No HTML tags visible in names
- ✅ No duplicate text rendering
- ✅ Names with `&`, `<`, `>`, `"`, `'` display correctly
- Added HTML escaping to prevent special characters from breaking rendering

---

**Version**: 1.0
**Date**: 2025-11-17
**URL**: http://localhost:8081

## Quick Test Summary

All three critical bugs have been fixed. Follow these steps to verify:

---

## Test 1: Duplicate First Names in Entity Display

### Steps to Test:
1. Navigate to **Entities** tab
2. Look for entity names, especially those with special characters
3. Verify names display correctly without duplication

### Expected Behavior:
- ✅ All entity names display as single, clean text
- ✅ No HTML tags visible in names
- ✅ No duplicate text rendering
- ✅ Names with `&`, `<`, `>`, `"`, `'` display correctly

### What Was Fixed:
- Added HTML escaping to prevent special characters from breaking rendering
- Applied to both entity cards and connection lists

---

## Test 2: Entity Network Links Navigation

### Steps to Test:
1. Go to **Entities** tab
2. Click on any entity card
3. Observe the transition to Network Graph

### Expected Behavior:
- ✅ Page switches to **Network Graph** tab smoothly
- ✅ Network graph centers on the selected entity
- ✅ Selected node is highlighted with glow effect
- ✅ Connected entities panel appears on bottom-left
- ✅ Node name matches the entity you clicked

### Additional Test Cases:
**Test Case A**: Entity with many connections (e.g., "Ghislaine Maxwell")
- Should center on node
- Should show all connections in panel
- Can click connections to navigate to other nodes

**Test Case B**: Entity with few/no connections
- Should show message in chat: "Entity X is not in the network graph"
- Chat sidebar should auto-open

### What Was Fixed:
- Added timing delays for tab switching and D3 simulation initialization
- Added validation to check if entity exists in network before selection
- Added user feedback for entities not in the network

---

## Test 3: Document Links Navigation

### Steps to Test:
1. Go to **Entities** tab
2. Find an entity card with document count > 0
3. Click on the **Documents** number (blue number in the card)

### Expected Behavior:
- ✅ Click is handled (doesn't trigger card click)
- ✅ Chat sidebar opens automatically
- ✅ System message appears with document list
- ✅ Message format:
  ```
  Found X document(s) mentioning "Entity Name":

  1. Document Name 1
  2. Document Name 2
  ...

  Note: Document viewer coming soon!
  ```

### Edge Cases:
**No Documents Found**:
- Should show message: "No documents found for [entity]. This entity may be from flight logs or contact lists only."

**API Error**:
- Should show message: "Unable to fetch documents. Please try using the chat to search for this entity."

### What Was Fixed:
- Added `showEntityDocuments()` function with API integration
- Added click handler with event propagation control
- Implemented auto-open chat sidebar for results
- Added comprehensive error handling

---

## Browser Testing Matrix

Test all fixes in:
- [ ] Chrome 120+ (primary)
- [ ] Firefox 120+
- [ ] Safari 16+
- [ ] Edge 120+

---

## Regression Testing

Ensure existing features still work:

### Network Graph Tab:
- [ ] Search box finds entities correctly
- [ ] Filters work (billionaires, connection levels)
- [ ] Zoom and pan work smoothly
- [ ] Node dragging works
- [ ] Connected entities panel shows/hides correctly

### Entities Tab:
- [ ] Search filters entities by name
- [ ] Filter dropdown works (All, Billionaires, High Connections)
- [ ] Entity cards display all information correctly
- [ ] Billionaire badge shows for billionaires

### Chat Assistant:
- [ ] Can send messages
- [ ] Receives responses
- [ ] Chat history displays correctly
- [ ] Sidebar collapse/expand works

---

## Performance Testing

### Load Times:
- [ ] Entities tab loads in < 2 seconds
- [ ] Network graph renders in < 3 seconds
- [ ] Entity click navigation completes in < 500ms
- [ ] Document query returns in < 1 second

### Memory:
- [ ] No memory leaks when switching tabs repeatedly
- [ ] Network graph simulation doesn't consume excessive CPU
- [ ] Multiple document queries don't leak memory

---

## Accessibility Testing

### Keyboard Navigation:
- [ ] Can tab through entity cards
- [ ] Can press Enter on entity card to navigate
- [ ] Network controls are keyboard accessible
- [ ] Chat input is keyboard accessible

### Screen Reader:
- [ ] Entity names announced correctly
- [ ] Document counts announced as interactive
- [ ] Network graph has ARIA labels (future improvement)

---

## Console Testing

Open browser console (F12) and verify:

### No Errors:
- [ ] No JavaScript errors on page load
- [ ] No errors when clicking entity cards
- [ ] No errors when clicking document counts
- [ ] No errors during network navigation

### Proper Logging:
Look for these helpful debug messages:
- `"Entity not found: [name]"` - when entity doesn't exist
- `"Node not found in network: [name]"` - when entity not in graph
- `"Error fetching entity documents:"` - when API call fails

---

## Test Data

### Good Test Entities:
1. **Ghislaine Maxwell**
   - Has many network connections
   - Should navigate to network successfully
   - Should have documents

2. **Bill Clinton**
   - Appears in multiple sources
   - Good for testing document links

3. **Donald Trump**
   - High-profile entity
   - Should have multiple connections

### Edge Case Entities:
1. Entity with special characters (if any exist in data)
2. Entity with very long name
3. Entity with zero connections (isolated node)
4. Entity with zero documents

---

## API Endpoint Testing

Test the document search endpoint directly:

```bash
# Test entity with documents
curl -u username:password "http://localhost:8081/api/entities/search?query=Clinton"

# Test entity without documents
curl -u username:password "http://localhost:8081/api/entities/search?query=Unknown"
```

Expected responses:
- Should return JSON with `documents` array
- Should handle URL encoding correctly
- Should return empty array if no documents found

---

## Known Limitations

1. **Document Viewer**: Not yet implemented - shows list in chat only
2. **Document Page**: Dedicated Documents tab planned for future
3. **PDF Preview**: In-app viewer not yet available
4. **Bulk Document Actions**: Not yet implemented

These are **not bugs** - they are planned features for future releases.

---

## Reporting Issues

If you find any issues during testing:

1. **Check browser console** for error messages
2. **Note the exact steps** to reproduce
3. **Take a screenshot** if visual bug
4. **Record network tab** if API-related
5. **Test in multiple browsers** to confirm

Report format:
```
**Bug**: Brief description
**Steps**: 1. Do this, 2. Then this...
**Expected**: What should happen
**Actual**: What actually happened
**Browser**: Chrome 120.0.6099.109
**Console Errors**: [paste errors]
```

---

## Success Criteria

All fixes are successful if:

- ✅ Zero duplicate text in entity names
- ✅ 100% success rate for entity card → network navigation
- ✅ Document links respond with appropriate feedback
- ✅ No console errors during normal usage
- ✅ All existing features continue to work
- ✅ No performance degradation
- ✅ No memory leaks

---

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass in all browsers
- [ ] No console errors
- [ ] Performance metrics acceptable
- [ ] Code review completed
- [ ] Documentation updated (this file)
- [ ] User guide updated if needed
- [ ] Backup of previous version taken
- [ ] Rollback plan in place

---

## Next Steps After Testing

1. Monitor user feedback for 24-48 hours
2. Watch server logs for API errors
3. Check analytics for user behavior changes
4. Plan Document Viewer feature (Bug #3 enhancement)
5. Consider adding entity detail modal (UX improvement)

---

**Happy Testing!** 🧪
