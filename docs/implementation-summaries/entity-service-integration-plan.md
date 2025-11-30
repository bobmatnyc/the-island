# EntityService Integration Plan for Organizations and Locations

**Ticket**: 1M-410 - Extract non-human entities (organizations, locations) from documents

**Date**: 2025-11-29

**Status**: Preparation - Extraction currently running (PID 93114, ~4.4% complete)

## Overview

This document outlines the code changes needed to integrate organization and location entities extracted from documents into the EntityService, alongside the existing 1,637 person entities from contact books.

## Expected Output Files

Once extraction completes (PID 93114), these files will be created:

1. **`data/metadata/entity_organizations.json`** (~920 organizations expected)
   ```json
   {
     "metadata": {
       "extraction_date": "2025-11-29T...",
       "total_organizations": 920,
       "min_mentions": 10
     },
     "entities": {
       "FBI": {
         "name": "FBI",
         "entity_type": "organization",
         "mention_count": 150,
         "documents": ["doc1.txt", "doc2.txt"],
         "contexts": ["Context 1...", "Context 2..."],
         "biography": "FBI is mentioned 150 times in the Epstein archive..."
       }
     }
   }
   ```

2. **`data/metadata/entity_locations.json`** (~458 locations expected)
   ```json
   {
     "metadata": {
       "extraction_date": "2025-11-29T...",
       "total_locations": 458,
       "min_mentions": 10
     },
     "entities": {
       "Little Saint James": {
         "name": "Little Saint James",
         "entity_type": "location",
         "mention_count": 200,
         "documents": ["doc1.txt", "doc2.txt"],
         "contexts": ["Context 1...", "Context 2..."],
         "biography": "Little Saint James is mentioned 200 times..."
       }
     }
   }
   ```

## Current Implementation

**File**: `server/services/entity_service.py`

**Lines 136-142**: Loads biographies from single file
```python
# Load biographies
bio_path = self.metadata_dir / "entity_biographies.json"
if bio_path.exists():
    with open(bio_path) as f:
        data = json.load(f)
        self.entity_bios = data.get("entities", {})

    logger.info(f"Loaded {len(self.entity_bios)} entity biographies")
```

## Required Changes

### 1. Modify `load_data()` Method

**Location**: `server/services/entity_service.py`, lines 136-142

**Current**: Loads only `entity_biographies.json` (persons)

**New**: Load and merge 3 entity files

```python
# Load biographies from all three entity files
entity_files = [
    ("entity_biographies.json", "person"),      # 1,637 persons
    ("entity_organizations.json", "organization"),  # ~920 orgs
    ("entity_locations.json", "location")       # ~458 locations
]

self.entity_bios = {}
total_loaded = 0

for filename, entity_type in entity_files:
    file_path = self.metadata_dir / filename
    if file_path.exists():
        try:
            with open(file_path) as f:
                data = json.load(f)
                entities = data.get("entities", {})

                # Merge entities, ensuring entity_type is set
                for entity_key, entity_data in entities.items():
                    # Ensure entity_type field exists
                    if "entity_type" not in entity_data:
                        entity_data["entity_type"] = entity_type

                    self.entity_bios[entity_key] = entity_data

                logger.info(f"Loaded {len(entities)} entities from {filename}")
                total_loaded += len(entities)
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
    else:
        logger.warning(f"Entity file not found: {filename}")

logger.info(f"Total entities loaded: {total_loaded}")
logger.info(f"Entity type distribution: {self._count_entity_types()}")
```

### 2. Add Entity Type Counter Helper

**New method to add after `load_data()`**:

```python
def _count_entity_types(self):
    """Count entities by type for logging"""
    from collections import Counter
    types = Counter()
    for entity_data in self.entity_bios.values():
        entity_type = entity_data.get("entity_type", "unknown")
        types[entity_type] += 1
    return dict(types)
```

### 3. API Endpoint Updates

**Location**: `server/main.py` (entity endpoints)

**Current behavior**: Already returns entity_type from biography data

**Verification needed**: Ensure API properly serves merged entities

**Test cases**:
- GET `/api/entities` - Should return all 3 types mixed (~3,015 total)
- GET `/api/entities?type=person` - Should return only persons (1,637)
- GET `/api/entities?type=organization` - Should return only orgs (~920)
- GET `/api/entities?type=location` - Should return only locations (~458)

### 4. Entity Type Filtering

**Current**: Entity filtering likely exists in API endpoints

**Verify**: Check if filtering by `entity_type` works correctly

**Test**: Ensure frontend can filter entities by type

## Frontend Integration

**Status**: ✅ Already complete - No changes needed

**File**: `frontend/src/pages/Entities.tsx`

**Already implemented**:
```tsx
const getEntityIcon = (type: string) => {
  switch (type) {
    case 'organization':
      return <Building2 className="h-5 w-5" />;
    case 'location':
      return <MapPin className="h-5 w-5" />;
    default:
      return <Users className="h-5 w-5" />;
  }
};
```

Frontend is ready and will automatically display correct icons once backend serves the data.

## Expected Entity Distribution

After integration:

| Entity Type | Count | Source |
|-------------|-------|--------|
| Person | 1,637 | Contact books (existing) |
| Organization | ~920 | Documents (new) |
| Location | ~458 | Documents (new) |
| **Total** | **~3,015** | **Combined** |

## Testing Plan

### 1. Backend Integration Testing

```bash
# After extraction completes and integration implemented:

# 1. Start backend
pm2 restart backend

# 2. Test API endpoints
curl http://localhost:8081/api/entities | jq '.entities | length'
# Expected: ~3,015

curl http://localhost:8081/api/entities | jq '[.entities[].entity_type] | group_by(.) | map({type: .[0], count: length})'
# Expected:
# [
#   {"type": "person", "count": 1637},
#   {"type": "organization", "count": 920},
#   {"type": "location", "count": 458}
# ]

# 3. Test filtering
curl "http://localhost:8081/api/entities?type=organization" | jq '.entities | length'
# Expected: ~920

# 4. Test specific entities
curl http://localhost:8081/api/entities/fbi | jq '.entity_type'
# Expected: "organization"

curl http://localhost:8081/api/entities/little_saint_james | jq '.entity_type'
# Expected: "location"
```

### 2. Frontend Testing

```bash
# 1. Open browser to https://the-island.ngrok.app/entities

# 2. Verify entity badges:
#    - Person entities: Users icon (default)
#    - Organization entities: Building2 icon
#    - Location entities: MapPin icon

# 3. Test filtering:
#    - Filter by type dropdown should show all 3 types
#    - Filtering should work correctly

# 4. Test search:
#    - Search for "FBI" should show organization entity
#    - Search for "Little Saint James" should show location entity
```

## Implementation Steps

1. ✅ **Extraction** (IN PROGRESS)
   - Process 33,561 documents with spaCy NER
   - Filter by min-mentions threshold (10)
   - Generate entity JSON files

2. ⏳ **Backend Integration** (PENDING - After extraction completes)
   - Modify `load_data()` to load 3 files
   - Add entity type counter helper
   - Test API endpoints
   - Verify filtering works

3. ⏳ **QA Testing** (PENDING)
   - Backend API endpoint testing
   - Frontend integration testing
   - Entity filtering verification

4. ⏳ **Documentation** (PENDING)
   - Update Linear ticket 1M-410
   - Document extraction results
   - Note any issues or improvements

## Estimated Timeline

- **Extraction completion**: ~4-5 hours from 22:30 (around 02:30-03:30)
- **Backend integration**: ~30 minutes
- **QA testing**: ~30 minutes
- **Documentation**: ~15 minutes

**Total remaining**: ~5-6 hours

## Dependencies

- Extraction process (PID 93114) must complete successfully
- Both JSON files must be created in `data/metadata/`
- No backend code changes can begin until files exist

## Rollback Plan

If integration causes issues:

1. Revert changes to `entity_service.py`
2. Restart backend: `pm2 restart backend`
3. System will fall back to person entities only
4. Investigation can proceed without affecting production

## Notes

- The extraction script creates placeholder biographies from document contexts
- Future enhancement: Use LLM to generate better biographies (mentioned in script comments)
- Entity deduplication is handled by the extraction script's normalization logic
- No schema changes needed - entity structure is compatible with existing system

## References

- Extraction script: `scripts/analysis/extract_nonhuman_entities.py`
- Current entity service: `server/services/entity_service.py` (lines 136-142)
- Frontend entity display: `frontend/src/pages/Entities.tsx`
- Linear ticket: 1M-410
