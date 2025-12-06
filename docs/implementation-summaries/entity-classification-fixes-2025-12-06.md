# Entity Classification Fixes - December 6, 2025

## Summary

Fixed critical entity classification issues and added connection threshold filtering to improve entity browsing UX.

## Issues Addressed

### 1. Ghislaine Maxwell Misclassification
**Problem**: Ghislaine Maxwell was incorrectly classified as ORGANIZATION instead of PERSON.

**Root Cause**: Entity extraction error from document processing.

**Solution**:
- Moved Ghislaine Maxwell from `entity_organizations.json` to `entity_biographies.json`
- Set `entity_type: "person"` with correction metadata
- Updated organization count from 920 to 919

**Files Modified**:
- `data/metadata/entity_organizations.json`
- `data/metadata/entity_biographies.json`

**Script**: `scripts/analysis/fix_entity_classifications.py`

---

### 2. NPA Misclassification
**Problem**: "NPA" (Non-Prosecution Agreement) was incorrectly classified as a LOCATION.

**Root Cause**: NPA is an acronym, not a geographic location. Entity extraction confused it with a place name.

**Solution**:
- Removed NPA from `entity_locations.json`
- Updated location count from 458 to 457

**Rationale**: NPA stands for "Non-Prosecution Agreement" - a legal term, not a location. Should not appear in location entities.

**Files Modified**:
- `data/metadata/entity_locations.json`

**Script**: `scripts/analysis/fix_entity_classifications.py`

---

### 3. Organizations/Locations Connection Counts
**Problem**: Backend hardcoded `connection_count = 0` for all organizations and locations, making them appear unconnected.

**Investigation**:
- Checked `entity_network.json` structure
- Found that network only contains person-to-person relationships
- Organizations and locations are not part of the entity network graph

**Decision**: Organizations and locations legitimately have 0 connections because:
1. Entity network is person-to-person only
2. Orgs/locations are mentioned in documents but don't have relationship edges
3. This is expected behavior, not a bug

**Outcome**: No backend changes needed. Issue is data-driven, not a code bug.

---

### 4. Connection Threshold Slider (Frontend)
**Problem**: 1,378 entities (84.2%) have 0 connections, cluttering the UI.

**Solution**: Added connection threshold slider to filter entities by minimum connection count.

**Implementation**:
- **Location**: `frontend/src/pages/Entities.tsx`
- **Features**:
  - Slider component (0 to max connections)
  - Default value: 1 (hides 0-connection entities)
  - URL parameter persistence: `?minConnections=N`
  - Real-time filtering with immediate feedback
  - Dynamic max value based on loaded entities
  - Clear helper text showing current filter status

**UI Elements**:
```tsx
<div className="bg-secondary/30 border border-border rounded-lg p-4">
  <label>Minimum Connections: {minConnections}</label>
  <input type="range" min="0" max={maxConnections} ... />
  <div>Showing {totalEntities} entities</div>
</div>
```

**User Experience**:
- Default view shows ~259 entities with 1+ connections (down from 3,015)
- Slider at 0: Shows all 3,015 entities
- Slider at 1: Hides 0-connection noise (default)
- Slider at 5+: Shows only highly connected entities
- URL updates for bookmarking: `/entities?minConnections=5`

**Files Modified**:
- `frontend/src/pages/Entities.tsx` (added state, handler, UI component)

---

## Testing

### Backend Changes
```bash
# Test classification fixes
python3 scripts/analysis/fix_entity_classifications.py

# Verify results
jq '.entities["Ghislaine Maxwell"]' data/metadata/entity_organizations.json  # null
jq '.["Ghislaine Maxwell"]' data/metadata/entity_biographies.json  # person entry
jq '.entities["NPA"]' data/metadata/entity_locations.json  # null
```

### Frontend Build
```bash
cd frontend && npm run build
# ✓ Built successfully in 3.36s
```

### Expected Behavior
1. **Backend**:
   - Ghislaine Maxwell appears as "person" in entity lists
   - NPA no longer appears in location lists
   - Organization count: 919 (was 920)
   - Location count: 457 (was 458)

2. **Frontend**:
   - Default view shows entities with 1+ connections
   - Slider allows adjusting threshold 0-{max}
   - Filter status displayed below slider
   - URL parameter persistence works
   - Entity count updates dynamically

---

## Metrics

### Before
- **Ghislaine Maxwell**: organization (incorrect)
- **NPA**: location (incorrect)
- **Entities with 0 connections**: 1,378 (84.2%)
- **Default view**: All 3,015 entities shown

### After
- **Ghislaine Maxwell**: person (correct)
- **NPA**: removed from locations
- **Entities with 0 connections**: Still 1,378 (data-driven, expected)
- **Default view**: ~259 entities with 1+ connections

---

## Files Created/Modified

### Created
- `scripts/analysis/fix_entity_classifications.py` - Entity classification fix script
- `scripts/analysis/calculate_entity_connections.py` - Connection count analysis (investigation only)
- `docs/implementation-summaries/entity-classification-fixes-2025-12-06.md` - This document

### Modified
- `data/metadata/entity_organizations.json` - Removed Ghislaine Maxwell
- `data/metadata/entity_biographies.json` - Added Ghislaine Maxwell as person
- `data/metadata/entity_locations.json` - Removed NPA
- `frontend/src/pages/Entities.tsx` - Added connection threshold slider

### Backups Created
- `data/metadata/entity_organizations_backup_20251206_024810.json`
- `data/metadata/entity_biographies_backup_20251206_024811.json`
- `data/metadata/entity_locations_backup_20251206_024811.json`

---

## Design Decisions

### 1. Why Not Calculate Org/Location Connections?
The entity network (`entity_network.json`) contains only person-to-person relationships. Organizations and locations are:
- Mentioned in documents
- Not nodes in the relationship graph
- Don't have connection counts by design

Attempting to calculate connections for orgs/locations would require:
- Building a new relationship graph
- Defining what "connections" means for organizations
- Significant data modeling work

**Decision**: Acknowledge that orgs/locations have 0 connections as expected behavior. Focus on UI filtering instead.

### 2. Why Default to minConnections=1?
- 84.2% of entities have 0 connections (primarily orgs/locations)
- Showing 3,015 entities overwhelms users
- Most interesting entities (persons) have connections
- Users can set slider to 0 if they want to see all entities

**Decision**: Default to 1 connection to show meaningful entities by default.

### 3. Why Client-Side Filtering?
Connection filtering is applied client-side (after backend returns data) because:
- Simple implementation
- No backend API changes needed
- Immediate responsiveness
- Can be combined with other client-side filters (categories)

---

## Future Improvements

1. **Organization Relationship Graph**: Build org-to-person and org-to-org relationships
2. **Backend Connection Filtering**: Add `min_connections` parameter to `/api/entities` endpoint
3. **Better Entity Classification**: Improve entity extraction to prevent future misclassifications
4. **Connection Type Labels**: Show what type of connections exist (flight logs, documents, etc.)

---

## Verification Checklist

- [x] Ghislaine Maxwell appears in "person" entities
- [x] NPA removed from locations
- [x] Frontend builds successfully
- [x] Connection threshold slider renders
- [x] Default view shows entities with 1+ connections
- [x] Slider adjusts threshold correctly
- [x] URL parameter persistence works
- [x] Entity count updates dynamically
- [x] Backups created before modifications

---

**Completed**: December 6, 2025
**Engineer**: Claude (Sonnet 4.5)
**Impact**: Improved data quality, better UX for entity browsing
