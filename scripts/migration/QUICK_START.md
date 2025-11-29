# Entity ID Migration - Quick Start

**⏱️ Total Time**: 10-15 minutes (with dry-run testing)

## Prerequisites Check

```bash
# Verify files exist
ls -lh data/metadata/entity_statistics.json
ls -lh data/metadata/entity_network.json

# Verify Python version (need 3.8+)
python3 --version

# Create directories
mkdir -p data/migration logs data/backups
```

## Step-by-Step Execution

### Step 1: Generate IDs (2 minutes)

```bash
# Dry-run first (safe, no changes)
python3 scripts/migration/generate_entity_ids.py --dry-run

# Actual execution
python3 scripts/migration/generate_entity_ids.py

# Verify output
ls -lh data/migration/entity_id_mappings.json
jq '.metadata' data/migration/entity_id_mappings.json
```

**Expected Output**:
```
Total entities processed: 1637
Unique IDs generated: 1637
Collisions detected: 0-5
✅ ID mappings saved
```

### Step 2: Migrate Statistics (2 minutes)

```bash
# Dry-run first
python3 scripts/migration/migrate_entity_statistics.py --dry-run

# Actual execution
python3 scripts/migration/migrate_entity_statistics.py

# Verify (should see slug IDs, not names)
jq '.statistics | keys | .[0:3]' data/metadata/entity_statistics.json
```

**Expected Output**:
```
Entities migrated: 1637
Validation: ✅ PASSED
Backup saved: entity_statistics.backup_TIMESTAMP.json
```

### Step 3: Migrate Network (2 minutes)

```bash
# Dry-run first
python3 scripts/migration/migrate_entity_network.py --dry-run

# Actual execution
python3 scripts/migration/migrate_entity_network.py

# Verify (should see slug IDs)
jq '.nodes[0].id' data/metadata/entity_network.json
```

**Expected Output**:
```
Nodes migrated: 284
Edges migrated: 1624
Orphaned edges: 0
Validation: ✅ PASSED
```

### Step 4: Migrate Metadata (1 minute)

```bash
# Dry-run first
python3 scripts/migration/migrate_entity_metadata.py --dry-run

# Actual execution
python3 scripts/migration/migrate_entity_metadata.py
```

**Expected Output**:
```
Biographies migrated: 20
Tags migrated: 68
Name mappings created: 1000+
✅ Metadata migration complete
```

### Step 5: Validate (2 minutes)

```bash
# Run comprehensive validation with benchmarks
python3 scripts/migration/validate_migration.py --benchmark
```

**Expected Output**:
```
Status: PASSED
Total checks: 15
Passed: 15
Failed: 0

📊 Performance:
  ID lookup: 0.001-0.01ms
  Speedup: 50-200x
```

## One-Line Migration (if confident)

```bash
# Run all migrations in sequence
python3 scripts/migration/generate_entity_ids.py && \
python3 scripts/migration/migrate_entity_statistics.py && \
python3 scripts/migration/migrate_entity_network.py && \
python3 scripts/migration/migrate_entity_metadata.py && \
python3 scripts/migration/validate_migration.py --benchmark
```

**Note**: Only use after testing with dry-run mode!

## Verification Commands

```bash
# Check entity count (should be 1637)
jq '.statistics | length' data/metadata/entity_statistics.json

# Check network (should be 284 nodes, 1624 edges)
jq '.metadata' data/metadata/entity_network.json

# Sample entity lookup by ID
jq '.statistics.jeffrey_epstein' data/metadata/entity_statistics.json

# Check ID format (should be lowercase slugs)
jq '.statistics | keys | .[0:5]' data/metadata/entity_statistics.json
```

## Rollback (if needed)

```bash
# List backups
ls -lt data/metadata/*.backup_*.json

# Restore all from backups (replace TIMESTAMP)
cp data/metadata/entity_statistics.backup_TIMESTAMP.json data/metadata/entity_statistics.json
cp data/metadata/entity_network.backup_TIMESTAMP.json data/metadata/entity_network.json
cp data/metadata/entity_biographies.backup_TIMESTAMP.json data/metadata/entity_biographies.json
cp data/metadata/entity_tags.backup_TIMESTAMP.json data/metadata/entity_tags.json
cp data/metadata/entity_name_mappings.backup_TIMESTAMP.json data/metadata/entity_name_mappings.json
```

## Troubleshooting

### Error: "File not found"

```bash
# Check you're in project root
pwd  # Should be /path/to/epstein

# Check files exist
ls data/metadata/
```

### Error: "No ID mapping found"

```bash
# Re-run ID generation
python3 scripts/migration/generate_entity_ids.py

# Verify mappings created
jq '.metadata.total_entities' data/migration/entity_id_mappings.json
```

### Validation Failed

```bash
# Check validation log
cat logs/validation.log

# Rollback and retry
# (see rollback commands above)
```

## Success Checklist

After migration, verify:

- [ ] `entity_id_mappings.json` exists with 1,637 entities
- [ ] `entity_statistics.json` uses slug IDs as keys
- [ ] `entity_network.json` nodes and edges use slug IDs
- [ ] Validation script reports "PASSED"
- [ ] All backups created successfully
- [ ] Performance benchmarks show 10x+ improvement

## Next Steps

1. **Test API endpoints** with new IDs
2. **Update frontend** routing
3. **Monitor** for issues
4. **Document** completion

## Help

- **Full documentation**: `/docs/ENTITY_ID_MIGRATION_PLAN.md`
- **Schema details**: `/docs/ENTITY_ID_SCHEMA.md`
- **Script reference**: `/scripts/migration/README.md`
- **Logs**: Check `logs/` directory

## Time Breakdown

| Step | Time |
|------|------|
| ID Generation | 2 min |
| Statistics Migration | 2 min |
| Network Migration | 2 min |
| Metadata Migration | 1 min |
| Validation | 2 min |
| **Total** | **~10 min** |

With dry-run testing: **15 minutes**

---

**Status**: ✅ Ready to execute
**Risk**: Low (backups automatic)
**Reversible**: Yes (rollback available)
