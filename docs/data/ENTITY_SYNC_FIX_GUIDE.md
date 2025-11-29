# Entity Sync Fix - Quick Reference Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ 1,637 entities
- ✅ Only one "Epstein, Jeffrey"
- ✅ PORTABLES removed
- ❌ Out of sync
- ❌ 1,702 entities (65 extra)

---

**Issue:** Duplicate Jeffrey Epstein entities and removed PORTABLES entity still appearing in frontend

**Root Cause:** Secondary statistics file (`entity_statistics.json`) out of sync with primary index

**Solution:** Rebuild entity_statistics.json

---

## Quick Fix (Recommended)

### Option 1: Rebuild Entity Statistics

If a rebuild script exists:

```bash
# Look for existing rebuild script
find /Users/masa/Projects/epstein/scripts -name "*rebuild*" -o -name "*statistics*"

# Run if found
python3 scripts/data_quality/rebuild_entity_statistics.py
```

### Option 2: Manual Merge Fix

Use existing merge scripts:

```bash
# Check for merge scripts
ls -la /Users/masa/Projects/epstein/scripts/data_quality/merge_*

# Run Epstein merge if exists
python3 scripts/data_quality/merge_epstein_duplicates.py
```

---

## Verification Steps

### 1. Check Entity Counts

```bash
# Primary index count
cat /Users/masa/Projects/epstein/data/md/entities/ENTITIES_INDEX.json | \
  python3 -c "import sys,json; print(f\"Primary: {len(json.load(sys.stdin)['entities'])} entities\")"

# Secondary index count
cat /Users/masa/Projects/epstein/data/metadata/entity_statistics.json | \
  python3 -c "import sys,json; print(f\"Secondary: {len(json.load(sys.stdin)['statistics'])} entities\")"

# Should match: 1,637 entities in both
```

### 2. Check for Jeffrey Epstein Duplicates

```bash
# Primary (should return 1 entity)
cat /Users/masa/Projects/epstein/data/md/entities/ENTITIES_INDEX.json | \
  python3 -c "import sys,json; entities=json.load(sys.stdin)['entities']; \
  matches = [e['name'] for e in entities if 'jeffrey' in e['name'].lower() and 'epstein' in e['name'].lower()]; \
  print(f'Found {len(matches)}: {matches}')"

# Secondary (should return 1 entity after fix)
cat /Users/masa/Projects/epstein/data/metadata/entity_statistics.json | \
  python3 -c "import sys,json; stats=json.load(sys.stdin)['statistics']; \
  matches = [k for k in stats.keys() if 'jeffrey' in k.lower() and 'epstein' in k.lower()]; \
  print(f'Found {len(matches)}: {matches}')"
```

### 3. Check for PORTABLES

```bash
# Should return no results in either file
grep -i "portables" /Users/masa/Projects/epstein/data/md/entities/ENTITIES_INDEX.json
grep -i "portables" /Users/masa/Projects/epstein/data/metadata/entity_statistics.json
```

---

## Current State

### Primary Index (ENTITIES_INDEX.json)
- ✅ Clean
- ✅ 1,637 entities
- ✅ Only one "Epstein, Jeffrey"
- ✅ PORTABLES removed

### Secondary Index (entity_statistics.json)
- ❌ Out of sync
- ❌ 1,702 entities (65 extra)
- ❌ Two Jeffrey Epstein entries
- ❌ PORTABLES still present

### Discrepancy
```
1,702 (secondary) - 1,637 (primary) = 65 stale entities
```

---

## What the Fix Should Do

1. **Remove duplicate "Jeffrey Epstein" entry**
   - Keep: "Epstein, Jeffrey" (with 162 connections)
   - Remove: "Jeffrey Epstein" (with 0 connections)

2. **Remove "PORTABLES, EPSTEIN-"**
   - Already removed from primary
   - Should not exist in secondary

3. **Synchronize entity counts**
   - Match primary: 1,637 entities
   - Remove 65 stale entries

4. **Preserve entity data**
   - Keep connection counts
   - Keep document associations
   - Keep flight data

---

## Expected Results After Fix

### Entity Statistics Summary
```json
{
  "total_entities": 1637,
  "entities_with_connections": 284,
  "entities_with_flights": 258,
  "billionaires": 32
}
```

### Jeffrey Epstein (Single Entry)
```json
{
  "name": "Epstein, Jeffrey",
  "normalized_name": "Jeffrey Epstein",
  "sources": ["black_book", "flight_logs"],
  "connection_count": 162,
  "flight_count": 8,
  "has_connections": true,
  "merged_from": ["Jeffrey Steiner"]
}
```

### PORTABLES
```
(No results - entity removed)
```

---

## Rollback Plan

If the fix causes issues:

```bash
# entity_statistics.json has backups
ls -lah /Users/masa/Projects/epstein/data/metadata/entity_statistics.backup*

# Restore from backup
cp /Users/masa/Projects/epstein/data/metadata/entity_statistics.backup_20251117_185321.json \
   /Users/masa/Projects/epstein/data/metadata/entity_statistics.json

# Restart server
./start_server.sh
```

---

## Testing the Fix

### 1. Frontend Test

```bash
# Start server
./start_server.sh

# Open browser to entities page
open http://localhost:5001/entities

# Search for "Jeffrey Epstein"
# Should show only ONE card
```

### 2. API Test

```bash
# Query entities API
curl "http://localhost:5001/api/entities?search=jeffrey%20epstein" | python3 -m json.tool

# Should return single entity
```

### 3. Network Graph Test

```bash
# Check entity in network
curl "http://localhost:5001/api/entities/Epstein%2C%20Jeffrey/connections" | python3 -m json.tool

# Should show 162 connections
```

---

## Files to Check

### Before Running Fix
```bash
# Backup current state
cp /Users/masa/Projects/epstein/data/metadata/entity_statistics.json \
   /Users/masa/Projects/epstein/data/metadata/entity_statistics.backup_$(date +%Y%m%d_%H%M%S).json
```

### Files That Should Change
- `/data/metadata/entity_statistics.json` (will be updated)

### Files That Should NOT Change
- `/data/md/entities/ENTITIES_INDEX.json` (already correct)
- `/data/metadata/entity_network.json` (already correct)
- `/data/metadata/entity_biographies.json` (unrelated)

---

## Related Scripts

Check these locations for helpful scripts:

```bash
# Data quality scripts
/Users/masa/Projects/epstein/scripts/data_quality/

# Existing merge scripts
merge_epstein_duplicates.py
merge_royal_duplicates.py
restore_entity_bios.py

# Analysis scripts
/Users/masa/Projects/epstein/scripts/analysis/
```

---

## Contact/Reference

- **Primary Index:** `/data/md/entities/ENTITIES_INDEX.json`
- **Secondary Index:** `/data/metadata/entity_statistics.json`
- **Backup Location:** `/data/md/entities/backup_invalid_removal/`
- **Investigation Report:** `/docs/data/ENTITY_DATA_QUALITY_INVESTIGATION_REPORT.md`

---

*Quick Reference Guide - Entity Sync Fix*
*Generated: 2025-11-20*
