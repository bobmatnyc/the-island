# Entity Display Fixes - December 6, 2025

## Overview

Fixed four critical issues with entity display on the Entities page that affected organizations, locations, and the connection slider functionality.

## Issues Fixed

### Issue 1: Location Names Formatted Wrong ✅

**Problem**: Locations showing as "Plains, White" instead of "White Plains"

**Root Cause**: `formatEntityName()` utility applied "Last, First" reversal to ALL entities

**Solution**: Modified formatEntityName to check entity_type before formatting
- Only reverses "Last, First" to "First Last" for person entities
- Returns name as-is for organizations and locations

**Files Changed**:
- `frontend/src/utils/nameFormat.ts` - Updated function signature to accept `entityType` parameter
- `frontend/src/pages/Entities.tsx` - Pass `entity.entity_type` to formatEntityName

### Issue 2: Organizations/Locations Show 0 Connections ✅

**Problem**: Organizations and locations all showed 0 connections (incorrect)

**Root Cause**: Backend hardcoded connection_count=0 for non-person entities

**Solution**: Calculate real connection counts from document co-mentions
- Loaded `document_entity_index.json` which maps documents → entities
- Created `calculate_entity_connections()` helper function
- Counts unique entities that appear in same documents as the target entity

**Files Changed**:
- `server/app.py`:
  - Added `document_entity_index` global variable
  - Updated `load_data()` to load document_entity_index.json
  - Added `calculate_entity_connections(entity_name)` function
  - Updated get_entities endpoint to calculate real connections for orgs/locations

**Implementation**:
```python
def calculate_entity_connections(entity_name: str) -> int:
    """Calculate connection count based on document co-occurrences"""
    entity_name_lower = entity_name.lower().strip()
    co_mentioned_entities = set()

    for doc_id, entities_in_doc in document_entity_index.items():
        entities_lower = [e.lower().strip() for e in entities_in_doc]
        if entity_name_lower in entities_lower:
            co_mentioned_entities.update(
                e for e in entities_in_doc
                if e.lower().strip() != entity_name_lower
            )

    return len(co_mentioned_entities)
```

### Issue 3: Slider Refreshes Whole Page ✅

**Problem**: Moving connection slider triggered full page reload

**Root Cause**: Slider onChange updated minConnections state, which was in useEffect dependency array

**Solution**: Remove minConnections from useEffect dependencies
- Filter happens client-side only (already implemented on lines 104-106)
- Slider movement now instant without API calls

**Files Changed**:
- `frontend/src/pages/Entities.tsx`:
  - Removed `minConnections` from loadEntities useEffect dependencies (line 71)
  - Removed `minConnections` from page reset useEffect dependencies (line 78)
  - Client-side filtering already existed, just needed to stop triggering refetch

### Issue 4: Pagination Already Implemented ✅

**Status**: Pagination controls already exist and are functional

**Implementation**: Lines 583-706 in Entities.tsx
- Shows page numbers with ellipsis for long lists
- Previous/Next buttons
- Smooth scroll to top on page change
- Only displays when totalEntities > PAGE_SIZE (100)

No changes needed for this issue.

## Verification

### Syntax Validation
- ✅ Python syntax check: `python3 -m py_compile server/app.py`
- ✅ TypeScript compilation: `npx tsc --noEmit`

### Expected Behavior After Fixes

1. **Location Names**:
   - ✅ "White Plains" displays as "White Plains" (not "Plains, White")
   - ✅ "New York" displays as "New York" (not "York, New")
   - ✅ Person names still show as "First Last" from "Last, First" storage

2. **Connection Counts**:
   - ✅ Organizations show > 0 connections (e.g., FBI, DOJ should have many)
   - ✅ Locations show > 0 connections (e.g., New York, Little St. James should have many)
   - ✅ Person connection counts remain accurate

3. **Slider Performance**:
   - ✅ Moving slider filters instantly without page reload
   - ✅ No API calls triggered by slider movement
   - ✅ Smooth, real-time filtering

4. **Pagination**:
   - ✅ Pagination controls visible at bottom when > 100 entities
   - ✅ Page numbers clickable with ellipsis for long lists
   - ✅ Previous/Next buttons work correctly
   - ✅ Smooth scroll to top on page change

## Testing Recommendations

### Manual Testing Steps

1. **Test Location Name Formatting**:
   ```
   - Navigate to /entities
   - Filter by entity_type=location
   - Verify location names display correctly (not reversed)
   - Example: Check "White Plains", "New York", "Palm Beach"
   ```

2. **Test Organization Connection Counts**:
   ```
   - Filter by entity_type=organization
   - Check connection counts for major orgs
   - Expected: DOJ, FBI should show many connections (not 0)
   - Verify counts match co-mentioned entities in documents
   ```

3. **Test Slider Performance**:
   ```
   - Move connection slider from 0 to 50
   - Verify: No loading spinner appears
   - Verify: Filtering happens instantly
   - Check browser DevTools Network tab: No API calls triggered
   ```

4. **Test Pagination**:
   ```
   - Ensure total entities > 100
   - Verify pagination controls visible at bottom
   - Click page 2: Should load next 100 entities
   - Click Previous/Next: Should navigate correctly
   ```

### API Testing

Test the backend endpoint directly:
```bash
# Get organizations with connection counts
curl "http://localhost:8081/api/entities?entity_type=organization&limit=10"

# Expected response should include connection_count > 0 for major orgs
```

### Frontend Integration Testing

```bash
# Build and run frontend
cd frontend
npm run build
npm run preview

# Navigate to http://localhost:4173/entities
# Test all four scenarios above
```

## Code Quality Impact

### Lines of Code (LOC) Impact
- **Frontend**: +8 lines (nameFormat.ts signature change, pass entityType parameter)
- **Backend**: +45 lines (calculate_entity_connections + document_index loading)
- **Net Impact**: +53 LOC (necessary for correct functionality)

### Performance Impact
- **Slider**: Significant improvement - no more API calls on every slider change
- **Connection Calculation**: One-time cost at startup to load document_entity_index
- **Runtime**: Connection counts calculated once per entity when list is fetched

### Maintainability
- Clear separation: person vs non-person formatting logic
- Reusable: `calculate_entity_connections()` can be used elsewhere
- Well-documented: Comments explain why minConnections is not in dependencies

## Related Issues

- Addresses user-reported bug: Organizations showing "0 connections"
- Improves UX: Slider now responsive instead of triggering full reload
- Data accuracy: Locations/orgs now have accurate connection counts
- Name display: Fixes confusion from reversed location names

## Rollback Plan

If issues arise, revert these commits:
1. Frontend: Revert formatEntityName changes
2. Backend: Remove document_entity_index loading and calculation function

No database migrations or data changes required.

## Future Enhancements

1. **Cache Connection Counts**: Pre-calculate and store in entity_organizations.json
2. **Incremental Updates**: Update connection counts when documents are added
3. **Connection Details**: Show which entities are connected, not just count
4. **Performance Optimization**: Index document_entity_index by entity name for O(1) lookup

---

**Implementation Date**: December 6, 2025
**Status**: Completed ✅
**Verified**: Syntax checks passed
**Awaiting**: Manual testing and deployment
