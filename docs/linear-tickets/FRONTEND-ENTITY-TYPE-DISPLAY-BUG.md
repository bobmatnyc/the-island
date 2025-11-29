# Linear Ticket: Frontend Entity Type Display Bug

**Status**: Ready to create
**Priority**: High (P1)
**Project**: Epstein Island (13ddc89e7271)
**Tags**: bug, frontend, ui, entity-types

## Title

Frontend: Entity type badges showing all entities as 'Person' despite correct backend classification

## Problem

The frontend UI is displaying all entities with 'Person' badges, even for organizations and locations that are correctly classified in the backend data.

## Root Cause

Backend classification is **correct** (verified in `entity_biographies.json` on 2025-11-29):
- Person: 1494 (91.3%)
- Location: 112 (6.8%)
- Organization: 31 (1.9%)

The bug is in the **frontend** - likely one of:
1. Not reading the `entity_type` field from backend
2. Using wrong field name (`type` instead of `entity_type`)
3. Hardcoded to show 'Person' for all entities

## Examples of Misclassified Entities in UI

**Organizations showing as Person:**
- ann_stock
- anthony_brand
- bert_fields
- betty_lagardere
- charlie_ind

**Locations showing as Person:**
- aliai_forte
- anh_duong
- ariane
- armado_fakhre
- azzedine_alaia

## Files to Investigate

- `frontend/src/components/entity/EntityCard.tsx`
- `frontend/src/components/entity/EntityBio.tsx`
- `frontend/src/pages/Entities.tsx`
- `frontend/src/pages/EntityDetail.tsx`
- Entity service files that fetch/display entity data
- Any TypeScript interfaces defining entity structure

## Technical Details

**Correct Backend Field Name**: `entity_type` (NOT `type`)

**Possible Values**:
- `"person"`
- `"organization"`
- `"location"`

**Data Location**: `data/metadata/entity_biographies.json`

**Example Entity Structure**:
```json
{
  "ann_stock": {
    "name": "Ann Stock",
    "entity_type": "organization",  // This is the correct field
    "display_name": "Ann Stock",
    "summary": "...",
    // ... other fields
  }
}
```

## Acceptance Criteria

- [ ] Organizations display with Organization badge (or appropriate icon/color)
- [ ] Locations display with Location badge (or appropriate icon/color)
- [ ] People display with Person badge (or appropriate icon/color)
- [ ] Badge types match `entity_type` field from backend API
- [ ] All 1,637 entities display correct type badge
- [ ] Entity detail pages show correct type
- [ ] Entity cards on all pages (Entities, Network, etc.) show correct type

## Impact

**User Experience**: Users cannot distinguish between people, organizations, and locations in the UI, reducing the utility of the archive's entity classification system.

**Data Accuracy**: Despite having correctly classified backend data, the frontend misrepresents all entities as people, creating confusion about the nature of entities in the archive.

## Related Tickets

- **1M-364**: Backend entity type classification fix (completed) - Fixed LLM prompt bug that was causing misclassification
- **1M-306**: Entity categorization fix (completed) - Initial entity type classification implementation

## Verification Steps

After fix is implemented:

1. Navigate to https://the-island.ngrok.app/entities
2. Search for "ann_stock" - should show **Organization** badge
3. Search for "aliai_forte" - should show **Location** badge
4. Search for "jeffrey_epstein" - should show **Person** badge
5. Check entity detail pages for each type
6. Verify badge display in entity network graph
7. Verify badge display in search results

## Notes

- Backend API endpoint: `/api/entities`
- Backend is serving correct `entity_type` values
- This is purely a frontend display issue
- Fix should be straightforward (use correct field name)

---

**Created**: 2025-11-29
**Verified Backend Correct**: 2025-11-29
**Session**: Entity classification verification post-1M-364
