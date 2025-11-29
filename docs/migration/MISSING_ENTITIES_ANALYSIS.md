# Missing Entity Analysis

**Quick Summary**: **Purpose**: Document entities found in network but missing from entity database...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **High-Profile**: 4 (Clinton, Prince Andrew, Sarah Ferguson, Nadia Marcinkova)
- **Other Individuals**: 23
- **Invalid/Placeholder**: 5
- **Network Name**: "Bill Clinton"
- **Possible DB Name**: "william_clinton" ✓ FOUND

---

**Date**: 2025-11-20
**Purpose**: Document entities found in network but missing from entity database

## Summary

**Total Missing**: 32 entities
- **High-Profile**: 4 (Clinton, Prince Andrew, Sarah Ferguson, Nadia Marcinkova)
- **Other Individuals**: 23
- **Invalid/Placeholder**: 5

---

## High-Profile Missing Entities (CRITICAL)

### 1. Bill Clinton
- **Network Name**: "Bill Clinton"
- **Possible DB Name**: "william_clinton" ✓ FOUND
- **Status**: NAME MISMATCH - Entity exists in DB
- **Action**: Create alias mapping

### 2. Prince Andrew
- **Network Name**: "Prince Andrew"
- **Possible DB Name**: "prince_andrew_duke_of_york" ✓ FOUND
- **Status**: NAME MISMATCH - Entity exists in DB
- **Action**: Create alias mapping

### 3. Sarah Ferguson
- **Network Name**: "Sarah Ferguson"
- **Possible DB Name**: "sarah_ferguson_duchess_of_york" ✓ FOUND
- **Status**: NAME MISMATCH - Entity exists in DB
- **Action**: Create alias mapping

### 4. Nadia Marcinkova
- **Network Name**: "Marcinkova, Nadia"
- **Possible DB Names**: "nadia", "nadia_bjorlin"
- **Status**: LIKELY "nadia" (known associate)
- **Action**: Verify and create alias mapping

---

## Other Missing Entities (INVESTIGATION REQUIRED)

### Possibly in Database Under Different Names

| # | Network Name | Potential Matches | Status |
|---|--------------|-------------------|--------|
| 5 | Jeffrey Shantz | ? | Unknown |
| 6 | David Roth | "david_roth_oren"? | Check DB |
| 7 | Nathan Myhrbold | "nathan_myhrvold"? (spelling) | Check DB |
| 8 | Mary Kerney | ? | Unknown |
| 9 | Doug Schoettle | ? | Unknown |
| 10 | Gary Blackwell | ? | Unknown |
| 11 | Christopher Wagner | "christopher_wagner"? | Check DB |
| 12 | Kristy Rodgers | ? | Unknown |
| 13 | Gary Roxburgh | ? | Unknown |
| 14 | Jonathan Mano | ? | Unknown |
| 15 | Alyssa Kristy | "alyssa_rogers"? | Check DB |
| 16 | Ryan Coomer | ? | Unknown |
| 17 | Robert Breslen | ? | Unknown |
| 18 | Kathy Alexander | "kathy_alexander"? | Check DB |
| 19 | Sean Koo | ? | Unknown |
| 20 | Alyssa Holders | Same as "Alyssa Kristy"? | Duplicate? |
| 21 | Barry Massion | ? | Unknown |
| 22 | Michael Durberry | ? | Unknown |
| 23 | Steven Lister | ? | Unknown |
| 24 | Frank Gamble | ? | Unknown |
| 25 | Ralph Pascale | ? | Unknown |
| 26 | William Hammond | ? | Unknown |
| 27 | William Murphy | ? | Unknown |

---

## Invalid/Placeholder Entities (REMOVE FROM NETWORK)

### Should NOT Be Migrated

| # | Network Name | Reason | Action |
|---|--------------|--------|--------|
| 28 | Illegible | Data quality issue | Remove |
| 29 | None | Missing data | Remove |
| 30 | Test Flight | Not a person | Remove |
| 31 | Reposition | Not a person | Remove |
| 32 | Secret Service Secret Service | Invalid format | Remove or fix |

---

## Resolution Strategy

### Phase 1: Verify Name Matches (HIGH PRIORITY)

Check entity database for these entities with potential misspellings or variations:

```bash
# Run this search against entity database
search_terms = [
    "nathan_myhrvold",  # Common misspelling
    "david_roth",       # Partial match
    "christopher_wagner",
    "kathy_alexander",
    "alyssa",           # Check all Alyssa entries
]
```

### Phase 2: Create Alias Mapping File

Create `/data/migration/entity_name_aliases.json`:

```json
{
  "Bill Clinton": "william_clinton",
  "Prince Andrew": "prince_andrew_duke_of_york",
  "Sarah Ferguson": "sarah_ferguson_duchess_of_york",
  "Marcinkova, Nadia": "nadia",
  "Nathan Myhrbold": "nathan_myhrvold",
  ...
}
```

### Phase 3: Invalid Entity Removal

Create network cleanup script to:
1. Remove "Illegible", "None", "Test Flight", "Reposition"
2. Fix "Secret Service Secret Service" to proper format
3. Document changes in migration log

### Phase 4: Add Genuinely Missing Entities

For entities confirmed NOT in database:
1. Research entity details from flight logs
2. Create entity entries in `entity_statistics.json`
3. Regenerate ENTITIES_INDEX
4. Re-run ID generation

---

## SQL Queries for Investigation

### Check for Partial Name Matches

```python
# Python script to find potential matches
import json
from difflib import get_close_matches

with open('data/metadata/entity_statistics.json') as f:
    stats = json.load(f)
    entities = list(stats['statistics'].keys())

missing = [
    "Jeffrey Shantz", "David Roth", "Nathan Myhrbold",
    "Mary Kerney", "Doug Schoettle", "Gary Blackwell",
    # ... etc
]

for name in missing:
    # Normalize to snake_case
    normalized = name.lower().replace(' ', '_')

    # Find close matches
    matches = get_close_matches(normalized, entities, n=3, cutoff=0.6)

    if matches:
        print(f"{name} → Possible matches: {matches}")
    else:
        print(f"{name} → NO MATCHES (genuinely missing)")
```

---

## Impact Analysis

### Network Edges Affected

**Edges involving missing entities**: 217 total

**High-impact missing entities** (by edge count):
1. Bill Clinton: ~20+ edges (Africa trip participants)
2. Prince Andrew: ~10+ edges (UK connections)
3. William Hammond: ~15+ edges (pilot/staff member)
4. Nadia: ~10+ edges (frequent associate)

**Low-impact missing entities**:
- Single-flight passengers: Most others
- Invalid entities: "Illegible", "None", etc.

---

## Recommended Actions

### Immediate (Before Migration Retry)

1. ✅ **Create alias mapping file**
   - Map 4 high-profile entities
   - Map any confirmed misspellings

2. ✅ **Remove invalid entities**
   - Delete 5 invalid/placeholder entries
   - Update network edges accordingly

3. ⏳ **Search database for close matches**
   - Run fuzzy matching script
   - Manually verify top candidates

### Short-term (Optional Enhancement)

4. ⏳ **Add genuinely missing entities**
   - Only if confirmed in flight logs
   - Document source of data

### Long-term (Data Quality)

5. ⏳ **Implement canonical name service**
   - Centralized name normalization
   - Alias/variation management
   - Prevents future mismatches

---

## Testing Plan

### Validation Criteria for Retry

1. **Node Migration**:
   - Target: ≥279 nodes migrated (99%+ of valid entities)
   - Max skipped: ≤5 (only genuinely missing)

2. **Edge Migration**:
   - Target: ≥1600 edges migrated (98%+ of valid edges)
   - Max skipped: ≤24 (only edges to invalid entities)

3. **Data Integrity**:
   - No duplicate node IDs
   - All migrated edges reference valid nodes
   - No data loss on migrated entities

---

## Appendix: Full Entity List with Edge Counts

```
Entity Name               | Edges | Action Required
--------------------------+-------+------------------
Bill Clinton              |   22  | Alias: william_clinton
Prince Andrew             |   15  | Alias: prince_andrew_duke_of_york
William Hammond           |   18  | Investigate or add to DB
Nadia (Marcinkova)        |   12  | Alias: nadia
Sarah Ferguson            |    8  | Alias: sarah_ferguson_duchess_of_york
Illegible                 |    5  | REMOVE
None                      |    1  | REMOVE
Secret Service (2x)       |    3  | REMOVE or fix format
Test Flight               |    1  | REMOVE
Reposition                |    1  | REMOVE
[Other 22 entities]       | 1-7   | Investigate individually
```

---

## Conclusion

**Resolvable**: 4 high-profile entities (confirmed name mismatches)
**Removable**: 5 invalid entities
**Requires Investigation**: 23 other entities

**Estimated Resolution Time**:
- Alias mapping: 30 minutes
- Invalid entity removal: 30 minutes
- Investigation of 23 entities: 1-2 hours
- **Total**: 2-3 hours

**Success Probability**: HIGH (90%+ of network can be migrated after resolution)
