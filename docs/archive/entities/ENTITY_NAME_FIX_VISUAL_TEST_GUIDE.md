# Entity Name Fix - Visual Testing Guide

**Purpose**: Verify that entity names no longer display with trailing commas
**URL**: http://localhost:8081
**Date**: 2025-11-18

---

## Quick Test (2 minutes)

### Test 1: Entity Detail Modal
1. Open http://localhost:8081
2. Click on **"Epstein, Jeffrey"** entity
3. **Check**: Entity name in modal header should be **"Epstein, Jeffrey"** (no trailing comma)
4. **✓ PASS** if clean, **✗ FAIL** if shows "Epstein, Jeffrey," or "Jeffrey, Epstein,"

### Test 2: Timeline Entity Tags
1. Open **Timeline** tab
2. Look at any timeline event with related entities
3. **Check**: Entity tags should show clean names like **"Epstein, Jeffrey"**
4. **✓ PASS** if clean, **✗ FAIL** if trailing commas visible

### Test 3: Flight Passengers
1. Open **Flights** tab
2. Click on any flight to expand details
3. **Check**: Passenger names should be clean (e.g., **"Epstein, Jeffrey"**)
4. **✓ PASS** if clean, **✗ FAIL** if trailing commas visible

---

## Comprehensive Test (10 minutes)

### Location 1: Network Graph Labels

**Steps**:
1. Open **Network** tab
2. Zoom in to read node labels clearly
3. Find nodes for "Epstein, Jeffrey", "Roberts, Virginia", "Spacey, Kevin"

**Expected**:
- ✓ Node labels show "Lastname, Firstname" format
- ✓ No trailing commas on any labels
- ✓ Consistent spacing after commas

**Common Issues**:
- ✗ "Epstein, Jeffrey," (trailing comma)
- ✗ "Jeffrey, Epstein" (reversed order)
- ✗ "Epstein,Jeffrey" (missing space)

---

### Location 2: Entity Detail Modal

**Steps**:
1. Click **Dashboard** → **Entities** section
2. Click on any entity name
3. Modal opens with entity details

**Expected**:
- ✓ Modal header shows "Lastname, Firstname"
- ✓ No trailing commas in header
- ✓ Entity type badge displays correctly

**Test These Entities**:
- "Epstein, Jeffrey"
- "Roberts, Virginia"
- "Dubin, Glenn"
- "Spacey, Kevin"
- "Maxwell, Ghislaine" (if present)

---

### Location 3: Timeline Entity Tags

**Steps**:
1. Open **Timeline** tab
2. Scroll through timeline events
3. Look for events with related entities (colored tags)

**Expected**:
- ✓ Entity tags show clean names
- ✓ No trailing commas in tags
- ✓ Clicking tag opens entity modal with clean name

**Example Events to Check**:
- Flight events (usually have multiple related entities)
- Meeting events
- Document events

---

### Location 4: Flight Passenger Lists

**Steps**:
1. Open **Flights** tab
2. Click to expand any flight with passengers
3. Check passenger list display

**Expected**:
- ✓ Passenger names show "Lastname, Firstname"
- ✓ No trailing commas
- ✓ Consistent formatting across all passengers

**Test Flights**:
- Any flight with "Epstein, Jeffrey" as passenger
- Flights with multiple high-profile passengers
- Flights with 10+ passengers (check truncation display)

---

### Location 5: Search Results

**Steps**:
1. Click search bar (top of page)
2. Type "Epstein"
3. Review search results dropdown

**Expected**:
- ✓ Entity names in results show clean format
- ✓ No trailing commas
- ✓ Consistent with other displays

**Test Searches**:
- "Epstein"
- "Roberts"
- "Maxwell"
- "Spacey"

---

### Location 6: Toast Notifications

**Steps**:
1. Open **Network** tab
2. Click on any entity node
3. Click **"Filter Flights"** button
4. Read the toast notification

**Expected**:
- ✓ Toast shows "Showing flights for Epstein, Jeffrey"
- ✓ No trailing comma in name
- ✓ All notification types show clean names

**Test Actions**:
- Filter flights by entity
- Filter documents by entity
- Highlight entity in network
- Show timeline for entity

---

### Location 7: Connected Entities Panel

**Steps**:
1. Open **Network** tab
2. Click on any entity node with connections
3. Right panel shows "Connected Entities"

**Expected**:
- ✓ Panel header shows clean entity name
- ✓ Connected entity names are clean
- ✓ Connection descriptions use clean names

**Example**:
```
Connected Entities: Epstein, Jeffrey
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Roberts, Virginia (3 flights)
Maxwell, Ghislaine (15 flights)
```

---

## Edge Cases to Test

### Edge Case 1: Single-Name Entities
**Entity**: "Madonna" or other single-name entities (if present)
**Expected**: Display as-is, no commas

### Edge Case 2: Special Characters
**Entity**: "PORTABLES, EPSTEIN-" (if present)
**Expected**: Clean display, no extra trailing commas

### Edge Case 3: Long Names
**Entity**: Names with 3+ parts (e.g., "Kellen Vickers, Sarah")
**Expected**: Clean display, single comma only

---

## Testing Checklist

- [ ] **Network Graph Labels**: Clean, no trailing commas
- [ ] **Entity Detail Modal**: Header shows clean name
- [ ] **Timeline Entity Tags**: All tags clean
- [ ] **Flight Passengers**: All passenger names clean
- [ ] **Search Results**: Search dropdown names clean
- [ ] **Toast Notifications**: All notifications clean
- [ ] **Connected Entities**: Panel and list clean
- [ ] **Edge Cases**: Special names handled correctly

---

## Browser Console Check

Open browser console (F12) and run:

```javascript
// Test formatEntityName function directly
console.log('Testing formatEntityName...');
console.log(formatEntityName('Epstein, Jeffrey')); // Should be "Epstein, Jeffrey"
console.log(formatEntityName('Epstein, Jeffrey,')); // Should be "Epstein, Jeffrey"
console.log(formatEntityName('Epstein,Jeffrey')); // Should be "Epstein, Jeffrey"
console.log('✓ All tests should show clean names without trailing commas');
```

**Expected Console Output**:
```
Testing formatEntityName...
Epstein, Jeffrey
Epstein, Jeffrey
Epstein, Jeffrey
✓ All tests should show clean names without trailing commas
```

---

## Known Good Examples

### Before Fix (WRONG)
- ❌ "Epstein, Jeffrey," (trailing comma)
- ❌ "Jeffrey, Epstein," (reversed order + trailing comma)
- ❌ "Epstein,Jeffrey" (missing space)

### After Fix (CORRECT)
- ✅ "Epstein, Jeffrey"
- ✅ "Roberts, Virginia"
- ✅ "Spacey, Kevin"
- ✅ "Dubin, Glenn"

---

## Reporting Issues

If you find any remaining issues:

1. **Screenshot** the problem location
2. **Note** which UI section (Network, Timeline, etc.)
3. **Record** the entity name showing incorrectly
4. **Check** browser console for errors
5. **Verify** cache was cleared (hard refresh: Ctrl+Shift+R or Cmd+Shift+R)

---

## Success Criteria

**All tests PASS** if:
- Zero instances of trailing commas in any UI location
- All entity names in consistent "Lastname, Firstname" format
- No browser console errors related to entity display
- Clean names across Network, Timeline, Flights, Search, Modals

**FIX VERIFIED** ✓

---

## Quick Commands

### Verify JavaScript Cache Updated
```bash
# Check version in loaded HTML
curl -s http://localhost:8081/ | grep "app.js?v="
# Should show: app.js?v=20251118_entity_name_fix
```

### Check API Data Format
```bash
# Verify API returns clean names
curl -s http://localhost:8081/api/entities | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Sample entity names from API:')
for e in data[:5]:
    print(f'  {e[\"name\"]}')
"
```

### Clear Browser Cache
- **Chrome/Edge**: Ctrl+Shift+Del (Windows) or Cmd+Shift+Del (Mac)
- **Firefox**: Ctrl+Shift+Del (Windows) or Cmd+Shift+Del (Mac)
- **Hard Refresh**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

---

**Last Updated**: 2025-11-18
**Fix Version**: app.js?v=20251118_entity_name_fix
**Status**: Ready for Testing
