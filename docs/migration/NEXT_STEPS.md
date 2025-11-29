# Entity ID Migration - Next Steps

**Quick Summary**: **Current Status**: ⚠️ Paused at Phase 4 - Data Quality Issues Detected...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Phase 1: Backups created
- Phase 2: Entity IDs generated (1,637 IDs, 0 collisions)
- Phase 3: Statistics migrated (1,637 entities)
- Phase 4: Network migration (32 missing entities, 217 affected edges)
- Phase 5: Metadata migration

---

**Current Status**: ⚠️ Paused at Phase 4 - Data Quality Issues Detected
**Completion**: 3/6 phases complete (50%)
**Entities Migrated**: 1,637/1,637 (100% in completed phases)

---

## Quick Summary

✅ **COMPLETED**:
- Phase 1: Backups created
- Phase 2: Entity IDs generated (1,637 IDs, 0 collisions)
- Phase 3: Statistics migrated (1,637 entities)

⚠️ **BLOCKED**:
- Phase 4: Network migration (32 missing entities, 217 affected edges)

⏸️ **PENDING**:
- Phase 5: Metadata migration
- Phase 6: Final validation

---

## Critical Issue: Missing Entity Mappings

### The Problem

The network file (`entity_network.json`) contains **32 entities** not found in the entity database, blocking migration of 217 network edges (13.4%).

### Root Cause

**Name variation mismatches** between data sources:
- Network: "Bill Clinton" (informal)
- Database: "william_clinton" (normalized)

### Impact

- ❌ 32 nodes cannot be migrated (11.3% of network)
- ❌ 217 edges cannot be migrated (13.4% of edges)
- ❌ High-profile entities affected: Bill Clinton, Prince Andrew, Sarah Ferguson

---

## Resolution Required Before Proceeding

### OPTION 1: Create Entity Name Aliases (RECOMMENDED)

**What**: Add manual mappings for known name variations

**Time**: 30-60 minutes

**Steps**:
```bash
# 1. Create alias mapping file
cat > data/migration/entity_name_aliases.json << 'EOF'
{
  "Bill Clinton": "william_clinton",
  "Prince Andrew": "prince_andrew_duke_of_york",
  "Sarah Ferguson": "sarah_ferguson_duchess_of_york",
  "Marcinkova, Nadia": "nadia"
}
EOF

# 2. Update network migration script to use aliases
# (modify scripts/migration/migrate_entity_network.py)

# 3. Remove invalid entities from network
# (e.g., "Illegible", "None", "Test Flight")

# 4. Re-run network migration
python3 scripts/migration/migrate_entity_network.py
```

**Pros**:
- ✅ Fast implementation
- ✅ Preserves existing database
- ✅ Resolves 4 high-profile entities immediately

**Cons**:
- ⚠️ Doesn't add genuinely missing entities (~23 individuals)
- ⚠️ Network will have fewer nodes than original

### OPTION 2: Add Missing Entities to Database

**What**: Research and add the 32 missing entities to the entity database

**Time**: 2-4 hours

**Steps**:
1. Cross-reference missing names with flight logs
2. Create entity entries in `entity_statistics.json`
3. Regenerate `ENTITIES_INDEX.json`
4. Re-run entity ID generation
5. Re-run network migration

**Pros**:
- ✅ Complete data preservation
- ✅ Maintains network integrity
- ✅ Captures all entities

**Cons**:
- ⚠️ Time-consuming research required
- ⚠️ Some entities may be genuinely unknown

### OPTION 3: Hybrid Approach (BEST)

**What**: Combine alias mapping + removal of invalid entities

**Time**: 1-2 hours

**Steps**:
1. Create aliases for 4 confirmed entities (Clinton, Andrew, etc.)
2. Remove 5 invalid entities ("Illegible", "None", etc.)
3. Investigate remaining 23 entities using fuzzy matching
4. Add confirmed entities, skip unknown ones
5. Re-run migration

**Expected Result**:
- ✅ ~279+ nodes migrated (98%+ success rate)
- ✅ ~1600+ edges migrated (98%+ success rate)
- ✅ All high-profile entities preserved

---

## Detailed Action Plan

### Step 1: Create Alias Mapping (30 min)

**Create**: `/data/migration/entity_name_aliases.json`

```json
{
  "aliases": {
    "Bill Clinton": "william_clinton",
    "Prince Andrew": "prince_andrew_duke_of_york",
    "Sarah Ferguson": "sarah_ferguson_duchess_of_york",
    "Marcinkova, Nadia": "nadia"
  },
  "invalid_entities": [
    "Illegible",
    "None",
    "Test Flight",
    "Reposition",
    "Secret Service Secret Service"
  ]
}
```

### Step 2: Update Migration Script (30 min)

**Modify**: `scripts/migration/migrate_entity_network.py`

Add alias resolution:
```python
def load_aliases(aliases_file):
    """Load name aliases from file"""
    with open(aliases_file, 'r') as f:
        data = json.load(f)
    return data['aliases'], set(data['invalid_entities'])

def get_entity_id(name, id_map, aliases):
    """Get entity ID with alias fallback"""
    # Try direct lookup
    if name in id_map:
        return id_map[name]

    # Try alias
    if name in aliases:
        canonical_name = aliases[name]
        return id_map.get(canonical_name)

    return None
```

### Step 3: Run Fuzzy Matching (30 min)

**Script**: `scripts/migration/find_entity_matches.py`

```python
import json
from difflib import get_close_matches

# Load entity database
with open('data/metadata/entity_statistics.json') as f:
    stats = json.load(f)
    entities = list(stats['statistics'].keys())

# Missing entities from network
missing = [
    "Jeffrey Shantz", "David Roth", "Nathan Myhrbold",
    "Mary Kerney", "Doug Schoettle", "Gary Blackwell",
    # ... add all 23 unknown entities
]

# Find potential matches
for name in missing:
    normalized = name.lower().replace(' ', '_')
    matches = get_close_matches(normalized, entities, n=3, cutoff=0.7)

    if matches:
        print(f"'{name}' → Potential: {matches}")
    else:
        print(f"'{name}' → NO MATCH (genuinely missing)")
```

### Step 4: Manual Verification (30 min)

Review fuzzy matches and manually verify:
- Check entity details in database
- Cross-reference with flight logs
- Confirm identity or reject match

Add confirmed matches to alias file.

### Step 5: Re-run Network Migration (5 min)

```bash
# Verify alias file exists
cat data/migration/entity_name_aliases.json

# Run migration with alias support
python3 scripts/migration/migrate_entity_network.py

# Check results
grep "✅" migration_log.txt
```

### Step 6: Validate Results (5 min)

```bash
# Run validation script
python3 scripts/migration/validate_migration.py --check-network

# Expected results:
# ✅ Nodes migrated: ≥279 (98%+)
# ✅ Edges migrated: ≥1600 (98%+)
# ✅ No duplicate node IDs
# ✅ All edges reference valid nodes
```

---

## Success Criteria

### Minimum Acceptable Results

- ✅ Nodes migrated: ≥279/284 (98%+)
- ✅ Edges migrated: ≥1600/1624 (98%+)
- ✅ All 4 high-profile entities migrated
- ✅ No duplicate node IDs
- ✅ No data corruption

### Ideal Results

- ✅ Nodes migrated: 279/284 (only 5 invalid entities removed)
- ✅ Edges migrated: 1623/1624 (99.9%+)
- ✅ All valid entities migrated
- ✅ Invalid entities documented and removed

---

## After Network Migration Completes

### Phase 5: Metadata Migration

**Files to Migrate**: ~82 metadata files

```bash
# Run metadata migration
python3 scripts/migration/migrate_entity_metadata.py

# This will migrate:
# - entity_biographies.json
# - entity_name_mappings.json
# - Other entity-related metadata
```

**Estimated Time**: 5-10 minutes

### Phase 6: Final Validation

**Run comprehensive validation**:

```bash
# Full validation with benchmarks
python3 scripts/migration/validate_migration.py --benchmark

# Generate final report
python3 scripts/migration/validate_migration.py --report > MIGRATION_FINAL_REPORT.md
```

**Validation Checks** (15 total):
- ✅ Entity count: 1,637
- ✅ All entity IDs unique
- ✅ All entity IDs valid format
- ✅ Network edges reference valid entities
- ✅ No orphaned edges
- ✅ Statistics data integrity
- ✅ Metadata files complete
- ✅ Performance improvement (>10x ID lookup speed)

**Estimated Time**: 5 minutes

---

## Timeline Estimate

| Step | Task | Time |
|------|------|------|
| 1 | Create alias mapping | 30 min |
| 2 | Update migration script | 30 min |
| 3 | Run fuzzy matching | 30 min |
| 4 | Manual verification | 30 min |
| 5 | Re-run network migration | 5 min |
| 6 | Validate network | 5 min |
| 7 | Migrate metadata | 10 min |
| 8 | Final validation | 5 min |
| **TOTAL** | **Full completion** | **2-3 hours** |

---

## Files and References

### Documentation
- **Execution Report**: `/docs/migration/MIGRATION_EXECUTION_REPORT.md`
- **Missing Entities Analysis**: `/docs/migration/MISSING_ENTITIES_ANALYSIS.md`
- **This File**: `/docs/migration/NEXT_STEPS.md`

### Migration Scripts
- ✅ `scripts/migration/generate_entity_ids.py` (Complete)
- ✅ `scripts/migration/migrate_entity_statistics.py` (Complete)
- ⚠️ `scripts/migration/migrate_entity_network.py` (Needs alias support)
- ⏸️ `scripts/migration/migrate_entity_metadata.py` (Pending)
- ⏸️ `scripts/migration/validate_migration.py` (Pending)

### Data Files
- ✅ `/data/migration/entity_id_mappings.json` (1,718 mappings)
- ✅ `/data/metadata/entity_statistics.json` (MIGRATED)
- ⚠️ `/data/metadata/entity_network.json` (ORIGINAL - not migrated)
- ⏸️ `/data/metadata/entity_name_mappings.json` (Pending)
- ⏸️ `/data/metadata/entity_biographies.json` (Pending)

### Backups
- `/backups/pre_entity_id_migration_20251120_183807/` (Complete pre-migration state)
- `/data/metadata/entity_statistics.backup_20251120_183852.json`
- `/data/metadata/entity_network.backup_20251120_183902.json`

---

## Key Decisions Needed

### Decision 1: Resolution Approach
**Question**: Which approach for missing entities?
- Option 1: Alias mapping only (fast, partial coverage)
- Option 2: Add all missing entities (slow, complete coverage)
- Option 3: Hybrid (recommended)

**Recommendation**: **Option 3 (Hybrid)** - Best balance of speed and completeness

### Decision 2: Invalid Entity Handling
**Question**: What to do with invalid entities ("Illegible", "None", etc.)?
- Remove from network (recommended)
- Keep but don't migrate
- Replace with "Unknown" entity

**Recommendation**: **Remove** - These are data quality issues, not real entities

### Decision 3: Unknown Entity Threshold
**Question**: What % missing entities is acceptable?
- 0% (add all missing entities) - Time consuming
- 2% (remove genuinely unknown) - Practical
- 5% (remove unclear entities) - Fast but lossy

**Recommendation**: **2%** - Accept ~5 unknown entities out of 284 (98%+ coverage)

---

## Risk Assessment

### Risks Mitigated ✅
- ✅ Data loss: All backups created
- ✅ Corruption: Validation failures prevented bad migration
- ✅ Rollback: Original files preserved

### Remaining Risks ⚠️
- ⚠️ **Low**: Alias mapping errors (mitigated by manual verification)
- ⚠️ **Low**: Unknown entities remain unknown (acceptable for 2%)
- ⚠️ **Low**: Network structure changes (only removing invalid nodes)

### Risk Level: **LOW**
All critical data is backed up, validation is comprehensive, and resolution path is clear.

---

## Contact / Questions

For questions about this migration:
1. Review `/docs/ENTITY_ID_SCHEMA.md` for design decisions
2. Review `/docs/ENTITY_ID_MIGRATION_PLAN.md` for original plan
3. Check `/docs/migration/MIGRATION_EXECUTION_REPORT.md` for detailed status

---

## Quick Command Reference

```bash
# Check current migration status
ls -lh data/metadata/*.backup_*
wc -l data/migration/entity_id_mappings.json

# View migrated entity count
jq '.total_entities' data/metadata/entity_statistics.json

# Check network backup
jq '.nodes | length, .edges | length' data/metadata/entity_network.backup_20251120_183902.json

# Create alias file
cat > data/migration/entity_name_aliases.json << 'EOF'
{
  "aliases": {
    "Bill Clinton": "william_clinton",
    "Prince Andrew": "prince_andrew_duke_of_york"
  },
  "invalid_entities": ["Illegible", "None"]
}
EOF

# Re-run network migration after fixes
python3 scripts/migration/migrate_entity_network.py

# Validate results
python3 scripts/migration/validate_migration.py --check-network
```

---

## Next Session Checklist

When resuming this migration:

- [ ] Review this document and execution report
- [ ] Decide on resolution approach (Option 1, 2, or 3)
- [ ] Create entity name alias file
- [ ] Update migration script with alias support (or use existing if already updated)
- [ ] Run fuzzy matching to find additional aliases
- [ ] Remove invalid entities from network
- [ ] Re-run network migration
- [ ] Validate network migration results
- [ ] Proceed to Phase 5 (metadata migration)
- [ ] Complete Phase 6 (final validation)
- [ ] Generate performance benchmarks

**Estimated completion time from this point**: 2-3 hours
