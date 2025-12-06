# Frontend Manual Verification Checklist
**Date**: December 6, 2025
**URL**: https://the-island.ngrok.app/entities

> **Note**: Automated Playwright tests could not run due to missing installation.
> Please manually verify the following items in your browser.

---

## Quick Checklist

- [ ] **Page loads successfully**
- [ ] **Connection slider visible** (default value: 1)
- [ ] **Three tabs visible**: Person, Organization, Location
- [ ] **Person tab shows ~1,634 entities**
- [ ] **Organization tab shows ~902 entities**
- [ ] **Location tab shows ~457 entities**
- [ ] **Ghislaine Maxwell found in Person tab**
- [ ] **NPA NOT found in Location tab**
- [ ] **Connection slider filters entities correctly**
- [ ] **No console errors**

---

## Detailed Verification Steps

### 1. Page Load Test
1. Open browser to: https://the-island.ngrok.app/entities
2. Wait for page to fully load
3. **Expected**: Page displays without errors
4. **Check**: Page title shows "Entities - Epstein Island"

**Screenshot**: Capture initial page load

---

### 2. Connection Slider Test
1. Locate the connection threshold slider
2. **Expected**: Slider exists and is visible
3. **Expected**: Default value is 1 (showing entities with 1+ connections)
4. **Check**: Slider range is 0-10

**Screenshot**: Capture slider component

---

### 3. Person Tab Test
1. Click the "Person" tab (if not already selected)
2. Wait for entities to load
3. **Expected**: Entity cards/list displays
4. **Expected**: Count indicator shows ~1,634 total persons
5. **Expected**: Entities have names, connection counts

**Screenshot**: Capture Person tab view

**Sample Test**:
- Search for "Epstein, Jeffrey"
- **Expected**: Should appear in results

---

### 4. Organization Tab Test
1. Click the "Organization" tab
2. Wait for entities to load
3. **Expected**: Entity cards/list displays
4. **Expected**: Count indicator shows ~902 total organizations
5. **Expected**: Different entities than Person tab

**Screenshot**: Capture Organization tab view

**Sample Test**:
- Search for "Department of Justice"
- **Expected**: Should appear in results

---

### 5. Location Tab Test
1. Click the "Location" tab
2. Wait for entities to load
3. **Expected**: Entity cards/list displays
4. **Expected**: Count indicator shows ~457 total locations
5. **Expected**: Location names (cities, addresses, etc.)

**Screenshot**: Capture Location tab view

**Sample Test**:
- Search for "New York"
- **Expected**: Should appear in results

---

### 6. Ghislaine Maxwell Verification Test
1. Go to **Person** tab
2. Use search box to search: "Ghislaine Maxwell"
3. **Expected**: Results found showing "Maxwell, Ghislaine"
4. **Expected**: Entity type shown as "Person"
5. **Check**: Connection count should be 102

**Screenshot**: Capture Ghislaine Maxwell search results

**Additional Check**:
1. Go to **Organization** tab
2. Search: "Ghislaine Maxwell"
3. **Expected**: Primary entity "Maxwell, Ghislaine" NOT in results
4. **Note**: May find variants like "Ghislaine Maxwell's" (legal document titles - expected)

---

### 7. NPA Removal Verification Test
1. Go to **Location** tab
2. Use search box to search: "NPA"
3. **Expected**: Zero results OR "No entities found"
4. **Expected**: NPA should NOT appear in location list

**Screenshot**: Capture NPA search showing no results

---

### 8. Connection Slider Filter Test
1. Ensure on any tab (Person recommended)
2. Note the current number of entities displayed
3. **Test A**: Set slider to 0
   - **Expected**: Maximum entities displayed (all entities)
   - Note the count
4. **Test B**: Set slider to 5
   - **Expected**: Fewer entities displayed (only those with 5+ connections)
   - **Check**: Count should be ≤ count from Test A
5. **Test C**: Set slider to 10
   - **Expected**: Even fewer entities (only those with 10+ connections)
   - **Check**: Count should be ≤ count from Test B

**Screenshot**: Capture slider at different values showing count changes

**Expected Behavior**:
```
Slider = 0  →  Shows all entities (e.g., 1,634 persons)
Slider = 1  →  Shows entities with 1+ connections (e.g., ~259)
Slider = 5  →  Shows entities with 5+ connections (e.g., ~150)
Slider = 10 →  Shows entities with 10+ connections (e.g., ~80)
```

---

### 9. Console Error Check
1. Open browser Developer Tools (F12 or Cmd+Option+I)
2. Go to "Console" tab
3. Navigate through all entity tabs (Person, Organization, Location)
4. Search for various entities
5. Adjust connection slider
6. **Expected**: No red error messages in console
7. **Acceptable**: Warning messages (yellow) are OK
8. **Not Acceptable**: JavaScript errors (red)

**Screenshot**: Capture console showing no errors

---

### 10. End-to-End User Journey Test

**Scenario**: User wants to find well-connected people

1. Navigate to https://the-island.ngrok.app/entities
2. Click "Person" tab
3. Set connection slider to 5 (entities with 5+ connections)
4. Browse results
5. Click on an entity (e.g., "Epstein, Jeffrey")
6. **Expected**: Entity detail page loads
7. **Expected**: Shows documents, connections, timeline

**Screenshot**: Capture entity detail page

---

## Expected Results Summary

| Test | Expected Result | Pass/Fail |
|------|----------------|-----------|
| Page loads | No errors | [ ] |
| Slider exists | Default value 1 | [ ] |
| Person tab | ~1,634 entities | [ ] |
| Organization tab | ~902 entities | [ ] |
| Location tab | ~457 entities | [ ] |
| Ghislaine in Persons | Found with 102 connections | [ ] |
| NPA in Locations | NOT found (0 results) | [ ] |
| Slider filters | Higher = fewer entities | [ ] |
| Console errors | No red errors | [ ] |
| Entity detail | Page loads correctly | [ ] |

---

## Issue Reporting Template

If you find issues, please report using this format:

```markdown
**Issue**: [Brief description]
**Test**: [Which test step]
**Expected**: [What should happen]
**Actual**: [What actually happened]
**Screenshot**: [Attach screenshot]
**Console Errors**: [Copy any error messages]
**Browser**: [Chrome/Firefox/Safari + version]
**Severity**: [Critical/High/Medium/Low]
```

**Example**:
```markdown
**Issue**: Ghislaine Maxwell found in Organizations tab
**Test**: Step 6 - Ghislaine Maxwell Verification
**Expected**: Should NOT appear in Organization tab
**Actual**: Appears as "GHISLAINE MAXWELL" organization
**Screenshot**: [attached]
**Console Errors**: None
**Browser**: Chrome 120.0.6099
**Severity**: Low (appears to be legal document title variant)
```

---

## Screenshots to Capture

Please capture and save the following screenshots:

1. `01-initial-page-load.png` - Entity page after loading
2. `02-connection-slider.png` - Slider component close-up
3. `03-person-tab.png` - Person tab showing entity list
4. `04-organization-tab.png` - Organization tab showing entity list
5. `05-location-tab.png` - Location tab showing entity list
6. `06-ghislaine-search-person.png` - Search results for Ghislaine in Person tab
7. `07-npa-search-location.png` - Search results for NPA in Location tab (showing 0)
8. `08-slider-at-0.png` - Slider at value 0 showing max entities
9. `09-slider-at-5.png` - Slider at value 5 showing filtered entities
10. `10-console-no-errors.png` - Developer console showing no errors

---

## Success Criteria

### ✅ All Tests Pass If:
- Entity page loads without errors
- Connection slider is visible and functional
- All three tabs (Person, Organization, Location) display correct counts
- Ghislaine Maxwell appears in Person tab with 102 connections
- NPA does NOT appear in Location tab
- Connection slider correctly filters entities (higher threshold = fewer entities)
- No JavaScript console errors

### ⚠️ Minor Issues Acceptable:
- Legal document title entities in organizations (e.g., "Ghislaine Maxwell's")
  - These are expected cleanup candidates, not blocking
- Warning messages in console (yellow)
- Slightly different entity counts due to data updates

### ❌ Blocking Issues:
- Page fails to load
- Tabs don't display entities
- Ghislaine Maxwell (primary) NOT in Person tab
- Connection slider doesn't exist or doesn't filter
- JavaScript errors breaking functionality

---

## After Verification

Once completed, please:

1. **Check all boxes** in the Quick Checklist above
2. **Save screenshots** in a folder (e.g., `qa-screenshots-2025-12-06/`)
3. **Note any issues** found using the Issue Reporting Template
4. **Share results** with development team

**Expected Result**: ✅ All tests pass with no critical issues

---

**Manual Verification Guide**
**Created**: December 6, 2025
**QA Agent**: Web QA
**Status**: Ready for user verification
