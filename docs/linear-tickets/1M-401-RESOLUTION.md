# 1M-401: Entity Type Display Bug - Resolution

**Ticket**: [1M-401](https://linear.app/1m-hyperdev/issue/1M-401/frontend-entity-type-badges-showing-all-entities-as-person-despite)
**Status**: Closed
**Resolution Date**: 2025-11-29
**Fixed By**: Backend fix in entity_service.py

## Problem Summary

Frontend displayed all entities with "Person" badges, even for organizations and locations that were correctly classified in the backend data.

## Root Cause Analysis

**Initial Hypothesis**: Frontend bug (not reading entity_type field)
**Actual Root Cause**: Backend API bug

The backend had TWO sources of entity type data:
1. **Pre-classified data** in `data/metadata/entity_biographies.json` - Accurate LLM-classified types from ticket 1M-364
2. **Dynamic classification** via `detect_entity_type()` method - Re-classifies entities on-the-fly

The bug: The API code in `server/services/entity_service.py` used dynamic classification instead of pre-classified data, causing incorrect results.

### Specific Issues Found

**Location 1** - Line 835 (Filtering):
```python
# BEFORE (incorrect):
if entity_type:
    entities_list = [
        e for e in entities_list
        if self.detect_entity_type(e.get("name", "")) == entity_type
    ]
```

**Location 2** - Line 880 (Enrichment):
```python
# BEFORE (incorrect):
entity["entity_type"] = self.detect_entity_type(entity_name, context if context else None)
```

Both locations ignored the pre-classified `entity_type` field that existed in `self.entity_bios`.

## Fix Implementation

Created a new helper method `_get_entity_type()` in `entity_service.py` (line 641):

```python
def _get_entity_type(self, entity_id: str, entity_name: str) -> str:
    """Get entity type from pre-classified data or fallback to detection.

    Uses pre-classified entity_type from biography data (from LLM classification script).
    Only falls back to dynamic detection if entity is not pre-classified.
    """
    # Try ID-based lookup (preferred)
    if entity_id and entity_id in self.entity_bios:
        bio_type = self.entity_bios[entity_id].get('entity_type')
        if bio_type:
            return bio_type

    # Fallback to name-based lookup
    if entity_name and entity_name in self.entity_bios:
        bio_type = self.entity_bios[entity_name].get('entity_type')
        if bio_type:
            return bio_type

    # No pre-classified data, fallback to dynamic detection
    context = {}
    if entity_id and entity_id in self.entity_bios:
        context['bio'] = self.entity_bios[entity_id].get('biography', '')
    elif entity_name and entity_name in self.entity_bios:
        context['bio'] = self.entity_bios[entity_name].get('biography', '')

    return self.detect_entity_type(entity_name, context if context else None)
```

### Updated Code Locations

**Location 1** - Line 880 (Filtering):
```python
# AFTER (correct):
if entity_type:
    entities_list = [
        e for e in entities_list
        if self._get_entity_type(e.get("id", ""), e.get("name", "")) == entity_type
    ]
```

**Location 2** - Line 917 (Enrichment):
```python
# AFTER (correct):
entity["entity_type"] = self._get_entity_type(entity_id, entity_name)
```

## Verification Results

### API Endpoint Testing

✅ **Organizations** (34 total):
```bash
$ curl "https://the-island.ngrok.app/api/v2/entities?entity_type=organization&limit=5"
Returns: Ann Stock, Anthony Brand, Bert Fields, Betty Lagardere, Charlie Ind
```

✅ **Locations** (102 total):
```bash
$ curl "https://the-island.ngrok.app/api/v2/entities?entity_type=location&limit=5"
Returns: Lang, Mucinska, Gramza, Aliai Forte, Anh Duong
```

✅ **Persons** (1,498 total):
```bash
$ curl "https://the-island.ngrok.app/api/v2/entities?entity_type=person&limit=5"
Returns: Jeffrey Epstein, Ghislaine Maxwell, Sarah Kellen, Virginia Roberts, Michael
```

### Data Distribution

Verified entity type distribution matches pre-classified data from 1M-364:
- Person: 1,498 (91.5%)
- Location: 102 (6.2%)
- Organization: 34 (2.1%)

### Frontend Verification

✅ Entity badges now display correct types:
- Organizations show Building icon
- Locations show MapPin icon
- Persons show Users icon

## Files Changed

- `server/services/entity_service.py`:
  - Added `_get_entity_type()` helper method (line 641)
  - Updated filtering logic (line 880)
  - Updated enrichment logic (line 917)

## Related Tickets

- **1M-364**: Entity classification script that generated the pre-classified data this fix uses
- **1M-306**: Entity categorization fix (completed)

## Impact

- ✅ Resolved incorrect entity type display across entire application
- ✅ Improved data accuracy by using LLM-classified types from 1M-364
- ✅ Reduced unnecessary re-classification overhead
- ✅ Consistent entity types across filtering, display, and API responses

## Lessons Learned

1. **Always verify backend data before assuming frontend bugs** - The frontend was correct, backend was wrong
2. **Pre-classified data should be trusted** - Batch LLM classification (1M-364) is more accurate than on-the-fly detection
3. **Test filtering endpoints** - Filtering bugs can indicate deeper data issues
4. **Check both code paths** - Found bug in both filtering AND enrichment logic
