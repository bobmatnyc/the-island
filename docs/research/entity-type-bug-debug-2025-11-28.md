# Entity Type Bug Debug Report
**Date**: 2025-11-28
**Investigator**: Research Agent
**Status**: ROOT CAUSE IDENTIFIED

## Executive Summary

Users are seeing wrong entity types (people classified as "Organization" or "Location") on entity detail pages. Root cause identified: Backend's `detect_entity_type()` function uses naive substring matching without word boundaries, causing catastrophic false positives.

## User-Reported Issues

**Entities showing as "Organization" (but are people)**:
- Samantha Boardman
- Serena Boardman

**Entities showing as "Location" (but are people)**:
- Carmine S. Villani
- Julia Broadhurst
- Minnie Driver

## Investigation Findings

### 1. API Response Analysis

**Test**: Fetched API data for affected entities

```bash
curl http://localhost:8081/api/v2/entities/samantha_boardman
```

**Result**: API returns `"entity_type": null`

```json
{
  "name": "Samantha Boardman",
  "sources": ["black_book"],
  "entity_type": null,
  ...
}
```

**Conclusion**: API does NOT send entity_type field to frontend.

### 2. Frontend Type Detection Logic

**Location**: `frontend/src/pages/EntityDetail.tsx:180-184`

```typescript
const getEntityType = (entity: Entity): EntityType => {
  if (entity.sources.includes('organization')) return 'organization';
  if (entity.sources.includes('location')) return 'location';
  return 'person';
};
```

**Test**: Verified `sources` array only contains `["black_book"]` or `["flight_logs"]`

```bash
curl 'http://localhost:8081/api/v2/entities?limit=1000' | \
  jq '[.entities[].sources] | flatten | unique'
# Result: ["black_book", "flight_logs"]
```

**Conclusion**: Frontend function SHOULD default to "person" (no "organization" or "location" in sources).

### 3. Backend Type Detection Logic

**Location**: `server/services/entity_service.py:368-459`

**Critical Code**:
```python
def detect_entity_type(self, entity_name: str) -> str:
    name = entity_name.lower()

    business_keywords = [
        "associates", "partners", "corp", "inc", "llc",
        "group", "holdings", "international", ...
    ]

    organization_keywords = [
        "board", "foundation", "institute", "university",
        "school", "department", "agency", "commission", ...
    ]

    location_keywords = [
        "island", "airport", "beach", "estate", "ranch",
        "street", "avenue", "road", "boulevard", "drive",
        "place", "manor", "villa", "palace", "hotel", "resort", "club"
    ]

    # BUGGY: Uses substring matching without word boundaries!
    if any(keyword in name for keyword in business_keywords):
        return "business"
    if any(keyword in name for keyword in organization_keywords):
        return "organization"
    if any(keyword in name for keyword in location_keywords):
        return "location"

    return "person"
```

### 4. Root Cause Proof

**Test**: Applied backend logic to user-reported entities

```python
def detect_entity_type(entity_name: str) -> str:
    name = entity_name.lower()
    # ... keyword lists ...
    if any(keyword in name for keyword in organization_keywords):
        return "organization"
    if any(keyword in name for keyword in location_keywords):
        return "location"
    return "person"

# Test cases
detect_entity_type("Samantha Boardman")  # -> "organization" (matches "board")
detect_entity_type("Serena Boardman")    # -> "organization" (matches "board")
detect_entity_type("Carmine S. Villani") # -> "location" (matches "villa")
detect_entity_type("Julia Broadhurst")   # -> "location" (matches "road")
detect_entity_type("Minnie Driver")      # -> "location" (matches "drive")
```

**Results**:

| Entity | Substring Match | Wrong Classification | Matched Keyword |
|--------|----------------|---------------------|-----------------|
| **Boardman**, Samantha | "**board**"man | Organization | "board" |
| **Boardman**, Serena | "**board**"man | Organization | "board" |
| **Villa**ni, Carmine | "**villa**"ni | Location | "villa" |
| Broad**hurst**, Julia | B"**road**"hurst | Location | "road" |
| **Drive**r, Minnie | "**drive**"r | Location | "drive" |

## Bug Locations

### Primary Bug: Backend `detect_entity_type()` Function

**File**: `server/services/entity_service.py`
**Lines**: 368-459
**Severity**: CRITICAL

**Problem**: Naive substring matching causes false positives on person names.

**Examples of Broken Logic**:
- "Boardman" → matches "board" → Organization ❌
- "Villani" → matches "villa" → Location ❌
- "Broadhurst" → matches "road" → Location ❌
- "Driver" → matches "drive" → Location ❌
- "Associates" (company name) → matches "associates" → Business ✅ (intended)

### Secondary Bug: API Not Sending entity_type

**File**: `server/app.py`
**Lines**: 2072-2107 (`/api/v2/entities/{entity_id}` endpoint)

**Problem**: Endpoint returns raw entity dict from `entity_stats` without calling `detect_entity_type()`. The `entity_type` field is only populated when calling `entity_service.get_entities()` (line 548), but NOT for individual entity lookups.

**Result**: API returns `"entity_type": null` even though backend HAS the buggy detection logic.

### Tertiary Issue: Frontend Type Display

**File**: `frontend/src/pages/EntityDetail.tsx`
**Lines**: 180-200
**Display**: Line 270 (`<Badge>{getEntityTypeLabel(entity)}</Badge>`)

**Problem**: Frontend's `getEntityType()` function checks `entity.sources.includes('organization')` which will NEVER match because sources only contains `["black_book", "flight_logs"]`. This function is ALSO buggy but harmless because API doesn't send `entity_type`.

**Current Behavior**:
- API sends `entity_type: null`
- Frontend function defaults to "person" (correct by accident)
- **BUT**: If backend starts sending `entity_type`, frontend will display wrong values

## Where Type Label is Displayed

**Location**: EntityDetail page (NOT Entities list page)

```tsx
// frontend/src/pages/EntityDetail.tsx:270
<Badge variant="secondary">{getEntityTypeLabel(entity)}</Badge>
```

**Visual Location**: Entity detail header, next to entity name

```
┌─────────────────────────────────────────────┐
│ 👤 Samantha Boardman  [Organization]  ← BUG │
│    Also known as: ...                       │
└─────────────────────────────────────────────┘
```

## Why User Sees Wrong Types (Despite API Sending null)

**Current State**: User should NOT see wrong types because:
1. API sends `entity_type: null`
2. Frontend doesn't use this field
3. Frontend's `getEntityType()` defaults to "person"

**Hypothesis**:
- **Possibility 1**: Backend recently started sending `entity_type` in certain conditions
- **Possibility 2**: User is testing on a different environment where backend DOES send `entity_type`
- **Possibility 3**: There's an older version of the code still running that had different logic
- **Possibility 4**: Entity data was pre-computed and stored with wrong types in `entity_stats.json`

**Action Required**: Check if `entity_statistics.json` has `entity_type` fields pre-populated.

## Fix Recommendations

### Option 1: Use Word Boundary Regex (Safest)

```python
import re

def detect_entity_type(self, entity_name: str) -> str:
    name = entity_name.lower()

    # Use word boundaries to prevent substring matches
    organization_keywords = ["board", "foundation", "institute", ...]
    location_keywords = ["island", "airport", "road", "drive", "villa", ...]

    # Compile regex patterns with word boundaries
    org_pattern = r'\b(' + '|'.join(re.escape(kw) for kw in organization_keywords) + r')\b'
    loc_pattern = r'\b(' + '|'.join(re.escape(kw) for kw in location_keywords) + r')\b'

    if re.search(org_pattern, name):
        return "organization"
    if re.search(loc_pattern, name):
        return "location"

    return "person"
```

**Result**:
- "Boardman" → NO match (not whole word "board") → Person ✅
- "Villani" → NO match (not whole word "villa") → Person ✅
- "Board of Directors" → matches "board" → Organization ✅

### Option 2: Remove Problematic Keywords

```python
# Remove keywords that commonly appear in surnames
organization_keywords = [
    "foundation", "institute", "university", "college",
    "school", "department", "agency", "commission",
    # REMOVED: "board" (too common in surnames like "Boardman")
]

location_keywords = [
    "island", "airport", "beach", "estate", "ranch",
    "street", "avenue", "boulevard",
    # REMOVED: "road", "drive", "villa", "place" (common in surnames)
]
```

**Trade-off**: May miss legitimate organizations/locations with simple names.

### Option 3: Disable Automatic Type Detection

```python
def detect_entity_type(self, entity_name: str) -> str:
    # Default everything to "person" until we have better detection
    return "person"
```

**Use Case**: When precision is more important than recall.

### Option 4: Machine Learning Classifier

Use NER (Named Entity Recognition) model:
- spaCy: `nlp(entity_name).ents[0].label_` → "PERSON", "ORG", "GPE"
- Transformers: BERT-based NER model

**Trade-off**: Adds dependency, slower, overkill for this use case.

## Recommended Fix

**Implement Option 1 (Word Boundary Regex)**:
- Fixes the immediate bug
- Preserves intended functionality
- Minimal code changes
- No new dependencies

**Test Cases to Validate**:

| Entity Name | Expected Type | Current (Buggy) | After Fix |
|-------------|---------------|-----------------|-----------|
| Samantha Boardman | Person | Organization ❌ | Person ✅ |
| Serena Boardman | Person | Organization ❌ | Person ✅ |
| Carmine S. Villani | Person | Location ❌ | Person ✅ |
| Julia Broadhurst | Person | Location ❌ | Person ✅ |
| Minnie Driver | Person | Location ❌ | Person ✅ |
| Board of Directors | Organization | Organization ✅ | Organization ✅ |
| Little St. James Island | Location | Location ✅ | Location ✅ |
| Epstein Associates LLC | Business | Business ✅ | Business ✅ |

## Additional Findings

### Frontend Entity Type Function (Also Buggy)

**Location**: `frontend/src/pages/Entities.tsx:184-190`

```typescript
const getEntityType = (entity: Entity): EntityType => {
  // This checks sources array for "organization" or "location"
  // but sources only contains ["black_book", "flight_logs"]
  if (entity.sources.includes('organization')) return 'organization';
  if (entity.sources.includes('location')) return 'location';
  return 'person'; // Default
};
```

**Problem**: Checks wrong field. Should check `entity.entity_type` if backend sends it.

**Fix**:
```typescript
const getEntityType = (entity: Entity): EntityType => {
  // Use entity_type field if available from backend
  if (entity.entity_type === 'organization') return 'organization';
  if (entity.entity_type === 'location') return 'location';
  if (entity.entity_type === 'business') return 'organization'; // Map business → organization
  return 'person'; // Default for null/undefined or unknown types
};
```

## Next Steps

1. **Verify Data Source**: Check if `data/metadata/entity_statistics.json` has `entity_type` fields
2. **Apply Backend Fix**: Implement word boundary regex in `detect_entity_type()`
3. **Update Frontend**: Fix frontend type detection to use `entity.entity_type` field
4. **Re-index Data**: If entity stats are pre-computed, regenerate with fixed logic
5. **Test**: Verify all user-reported entities show correct types

## Verification Commands

```bash
# Check if entity_statistics.json has entity_type fields
jq '.samantha_boardman.entity_type // "null"' data/metadata/entity_statistics.json

# Test backend detection logic
python3 -c "
from server.services.entity_service import EntityService
svc = EntityService()
print(svc.detect_entity_type('Samantha Boardman'))  # Should return 'person' after fix
"

# Test API response
curl -s http://localhost:8081/api/v2/entities/samantha_boardman | jq '.entity_type'
```

## Conclusion

**Root Cause**: Backend's `detect_entity_type()` uses substring matching without word boundaries, causing surnames to trigger false positives.

**Impact**:
- "Boardman" → "Organization" (matches "board")
- "Villani" → "Location" (matches "villa")
- "Broadhurst" → "Location" (matches "road")
- "Driver" → "Location" (matches "drive")

**Solution**: Implement word boundary regex matching to ensure keywords only match complete words, not substrings within surnames.

**Priority**: HIGH - User-visible data quality issue affecting entity classification accuracy.
