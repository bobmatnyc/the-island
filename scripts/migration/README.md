# Entity ID Migration Scripts

Production-ready Python scripts for migrating Epstein archive from name-based to ID-based entity identifiers.

## Quick Start

```bash
# 1. Generate entity IDs (dry-run first)
python3 generate_entity_ids.py --dry-run
python3 generate_entity_ids.py

# 2. Migrate data files
python3 migrate_entity_statistics.py
python3 migrate_entity_network.py
python3 migrate_entity_metadata.py

# 3. Validate migration
python3 validate_migration.py --benchmark
```

## Scripts Overview

### 1. `generate_entity_ids.py`

**Purpose**: Generate deterministic snake_case entity IDs

**Output**:
- `data/migration/entity_id_mappings.json` - Complete ID registry
- `data/migration/collision_report.json` - Conflicts requiring review (if any)

**Usage**:
```bash
python3 generate_entity_ids.py [--dry-run] [--verbose]
```

**Example**:
```bash
$ python3 generate_entity_ids.py
Total entities processed: 1637
Unique IDs generated: 1637
Collisions detected: 2
✅ ID mappings saved to: data/migration/entity_id_mappings.json
```

### 2. `migrate_entity_statistics.py`

**Purpose**: Migrate `entity_statistics.json` to ID-keyed structure

**Changes**:
- Root keys: names → entity IDs
- Added `id` field to each entity
- Preserved all existing data

**Usage**:
```bash
python3 migrate_entity_statistics.py [--dry-run] [--no-backup] [--verbose]
```

**Safety**:
- Creates automatic backup before modification
- Validates data integrity before committing
- Rollback available if validation fails

### 3. `migrate_entity_network.py`

**Purpose**: Migrate network graph to ID-based references

**Changes**:
- Node IDs: names → entity IDs
- Edge references: names → entity IDs
- Validates no orphaned edges

**Usage**:
```bash
python3 migrate_entity_network.py [--dry-run] [--no-backup] [--verbose]
```

**Critical**:
- Network graph integrity validated
- All edge references must exist
- Zero tolerance for orphaned edges

### 4. `migrate_entity_metadata.py`

**Purpose**: Migrate biographies, tags, and name mappings

**Files Updated**:
- `entity_biographies.json`
- `entity_tags.json`
- `entity_name_mappings.json`

**Usage**:
```bash
python3 migrate_entity_metadata.py [--dry-run] [--no-backup] [--verbose]
```

### 5. `validate_migration.py`

**Purpose**: Comprehensive validation suite

**Checks**:
- ID format compliance
- Entity count preservation
- Reference integrity
- Network graph validity
- Performance benchmarks

**Usage**:
```bash
python3 validate_migration.py [--benchmark] [--verbose] [--output report.json]
```

**Example**:
```bash
$ python3 validate_migration.py --benchmark
Status: PASSED
Total checks: 15
Passed: 15
Failed: 0

📊 Performance:
  ID lookup: 0.003ms
  Name search: 1.2ms
  Speedup: 400x
```

## Command Reference

### Common Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Run without modifying files |
| `--verbose` | Enable detailed logging |
| `--no-backup` | Skip backup creation (not recommended) |
| `--benchmark` | Run performance tests (validation only) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failure (check logs) |

## File Locations

**Input**:
- `data/metadata/entity_statistics.json`
- `data/metadata/entity_network.json`
- `data/metadata/entity_biographies.json`
- `data/metadata/entity_tags.json`
- `data/metadata/entity_name_mappings.json`

**Output**:
- `data/migration/entity_id_mappings.json`
- `data/migration/collision_report.json` (if collisions)
- `data/migration/validation_report.json` (with --output)

**Backups**:
- `data/metadata/*.backup_TIMESTAMP.json`

**Logs**:
- `logs/id_generation.log`
- `logs/migrate_statistics.log`
- `logs/migrate_network.log`
- `logs/migrate_metadata.log`
- `logs/validation.log`

## Migration Workflow

**Recommended Order**:

```
1. generate_entity_ids.py
   ↓
2. Review collision_report.json (if exists)
   ↓
3. migrate_entity_statistics.py
   ↓
4. migrate_entity_network.py
   ↓
5. migrate_entity_metadata.py
   ↓
6. validate_migration.py
```

**Safety Checkpoints**:
- Each script validates before committing
- Automatic backups created
- Validation gates prevent corruption
- Rollback available at each step

## Rollback Procedures

### Full Rollback

```bash
# Restore all files from backup
BACKUP_DIR="data/backups/pre_migration_TIMESTAMP"

cp "$BACKUP_DIR"/*.json data/metadata/
```

### Partial Rollback (Single File)

```bash
# Example: Rollback network only
cp data/metadata/entity_network.backup_TIMESTAMP.json \
   data/metadata/entity_network.json
```

## Troubleshooting

### "No ID mapping found"

**Cause**: Entity exists in data file but not in entity_statistics.json

**Solution**:
1. Add missing entity to entity_statistics.json
2. Re-run `generate_entity_ids.py`
3. Re-run migration for affected file

### "Orphaned edges detected"

**Cause**: Edge references node not in migrated nodes

**Solution**:
1. Check which nodes are missing
2. Verify they exist in entity_statistics.json
3. Re-run network migration

### "Validation failed"

**Cause**: Data integrity issue

**Solution**:
1. Check logs/validation.log for details
2. Identify failing check
3. Rollback affected file
4. Fix underlying issue
5. Re-run migration

## Performance

**Expected Runtime** (1,637 entities):
- ID generation: <30 seconds
- Statistics migration: <10 seconds
- Network migration: <10 seconds
- Metadata migration: <5 seconds
- Validation: <10 seconds
- **Total**: <2 minutes

**Performance Improvement**:
- ID lookups: 10-100x faster
- Network queries: Simplified
- URL routing: Direct (no encoding)

## Dependencies

**None** - Uses Python 3.8+ standard library only:
- `json` - JSON parsing
- `pathlib` - File operations
- `logging` - Logging
- `argparse` - CLI arguments
- `unicodedata` - Unicode normalization
- `re` - Regular expressions

## Testing

### Dry-Run Mode

Test all scripts without modifying data:

```bash
python3 generate_entity_ids.py --dry-run
python3 migrate_entity_statistics.py --dry-run
python3 migrate_entity_network.py --dry-run
python3 migrate_entity_metadata.py --dry-run
```

### Validation

Verify migration success:

```bash
python3 validate_migration.py --benchmark --verbose
```

## Documentation

- **Schema Specification**: `/docs/ENTITY_ID_SCHEMA.md`
- **Migration Plan**: `/docs/ENTITY_ID_MIGRATION_PLAN.md`
- **Research Analysis**: `/docs/ENTITY_ID_RESEARCH_ANALYSIS.md`

## Support

**Logs**: Check `logs/` directory for detailed execution logs

**Errors**: All errors logged with context for debugging

**Questions**: See migration plan for comprehensive guide

## License

Part of the Epstein Archive project.
