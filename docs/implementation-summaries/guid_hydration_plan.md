# GUID Hydration Implementation Plan

**Quick Summary**: Implementation summary documenting changes, files modified, and testing results.

**Category**: Implementation
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- `isGuid(value: string): boolean` - Detect UUID format
- `hydrateEntityName(identifier: string): Promise<string>` - Fetch name from GUID
- In-memory cache to avoid repeated API calls
- Map<string, string> for guid → name lookups
- Add useEffect to detect GUID in initial entity parameter

---

## Problem
When users navigate to `/news?entity={guid}`, the filter bar shows the GUID instead of the human-readable entity name.

## Solution Components

### 1. GUID Detection Utility
Create `frontend/src/utils/guidUtils.ts`:
- `isGuid(value: string): boolean` - Detect UUID format
- `hydrateEntityName(identifier: string): Promise<string>` - Fetch name from GUID

### 2. Entity Name Cache
Create `frontend/src/utils/entityNameCache.ts`:
- In-memory cache to avoid repeated API calls
- Map<string, string> for guid → name lookups

### 3. Update NewsFilters Component
- Add useEffect to detect GUID in initial entity parameter
- Hydrate GUID → name on component mount
- Display name in input while maintaining GUID in URL for API calls

### 4. Update News Page
- Pass hydrated entity name to NewsFilters
- Keep GUID in URL for sharing/bookmarking

## Implementation Steps

1. ✅ Analyze current code (DONE)
2. Create GUID utilities
3. Create entity name cache
4. Add hydration hook to NewsFilters
5. Test with GUID URLs
6. Update other pages (Timeline, Documents, etc.)

## Files to Modify
- `frontend/src/utils/guidUtils.ts` (NEW)
- `frontend/src/utils/entityNameCache.ts` (NEW)
- `frontend/src/components/news/NewsFilters.tsx` (UPDATE)
- `frontend/src/pages/News.tsx` (UPDATE)

## Test Cases
1. Navigate to `/news?entity=jeffrey_epstein` → Shows "Jeffrey Epstein"
2. Navigate to `/news?entity=43886eef-f28a-549d-8ae0-8409c2be68c4` → Shows "Jeffrey Epstein" (hydrated)
3. Type in filter bar → Works normally
4. Clear filter → Clears both display and URL
