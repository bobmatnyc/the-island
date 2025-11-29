# Entity Biography Batch Merge Guide

Quick reference for merging biography batch files into the master entity_biographies.json.

## Quick Start

```bash
# Merge specific batch (recommended)
python3 scripts/analysis/merge_biography_batches.py 9

# Merge multiple batches
python3 scripts/analysis/merge_biography_batches.py 9 10 11

# Merge all available batches
python3 scripts/analysis/merge_biography_batches.py --all
```

## What It Does

1. **Creates automatic backup** with timestamp
2. **Loads master file** (data/metadata/entity_biographies.json)
3. **Merges specified batch files** into master
4. **Calculates aggregate statistics** (quality scores, word counts)
5. **Updates metadata** with merge details
6. **Generates comprehensive report**

## Features

### ✅ Safety
- Automatic timestamped backups before any modification
- Data integrity checks (no duplicates, valid scores, positive word counts)
- Validation of batch file structure

### ✅ Flexibility
- Selective batch merging (specify batch numbers)
- Handles updates to existing entities
- Supports both metadata structures (nested and top-level)

### ✅ Visibility
- Detailed merge statistics
- Per-batch summaries
- Duplicate detection reporting
- Aggregate quality metrics

## Batch File Structure

Expected structure:
```json
{
  "entities": {
    "entity_id": {
      "id": "entity_id",
      "display_name": "Display Name",
      "biography": "Biography text...",
      "generated_by": "grok-4.1-fast",
      "generation_date": "2025-11-26T...",
      "quality_score": 0.95,
      "word_count": 233
    }
  },
  "metadata": {
    "total_entities": 65,
    "successful": 65,
    "failed": 0,
    "total_tokens_used": 93204
  }
}
```

## Output

### Files Created/Modified
- `entity_biographies.json` - Updated master file
- `entity_biographies_backup_YYYYMMDD_HHMMSS.json` - Automatic backup

### Console Report
```
============================================================
✅ MERGE COMPLETE - Summary Report
============================================================

📊 Entity Counts:
  Before merge: 569
  New entities:  65
  Updated:       0
  After merge:   634

📈 Aggregate Statistics:
  Avg quality score: 0.932
  Avg word count:    217.8

📁 Batch Details:
  entity_biographies_batch9.json:
    Total: 65, Added: 65, Updated: 0
```

## Verification Commands

```bash
# Check total entity count
python3 -c "
import json
with open('data/metadata/entity_biographies.json') as f:
    data = json.load(f)
print(f'Total entities: {len(data[\"entities\"])}')
"

# View metadata
python3 -c "
import json
with open('data/metadata/entity_biographies.json') as f:
    data = json.load(f)
print(json.dumps(data['metadata'], indent=2))
"

# Verify specific batch entities exist
python3 -c "
import json

# Load batch file
with open('data/metadata/entity_biographies_batch9.json') as f:
    batch = json.load(f)
batch_ids = set(batch['entities'].keys())

# Load merged file
with open('data/metadata/entity_biographies.json') as f:
    merged = json.load(f)

# Check
found = len(batch_ids & set(merged['entities'].keys()))
print(f'Batch 9: {found}/{len(batch_ids)} entities found in master')
"
```

## Current Status (as of 2025-11-26)

### Merged Batches
- ✅ Batches 4-8 (previously merged)
- ✅ Batch 9 (merged 2025-11-26)

### Pending Batches
- ⏳ Batch 2a - 34 entities
- ⏳ Batch 2b - 33 entities
- ⏳ Batch 3a - 34 entities
- ⏳ Batch 3b - 33 entities
- ❓ Batch 10 - File not found (may not be generated)

### Total Coverage
- **Current**: 634 entities
- **If all merged**: ~768 entities (634 + 134 from batches 2-3)

## Common Issues

### Issue: Batch file not found
```
⚠️  Batch 10 file not found: entity_biographies_batch10.json
```
**Solution**: Verify batch file exists or generate it first

### Issue: Duplicate entities
```
⚠️  Duplicates Found: 5
```
**Behavior**: Existing entities are updated with batch data (not an error)

### Issue: Statistics show 0.0
**Solution**: Script now handles both metadata structures automatically

## Best Practices

1. **Merge selectively** - Specify batch numbers to avoid re-merging
2. **Verify backups** - Check backup file created successfully
3. **Review report** - Check entity counts and statistics
4. **Test integration** - Verify new entities display in frontend

## Related Documentation

- Main report: `docs/SESSION_SUMMARY_2025-11-26_BIOGRAPHY_BATCH9_MERGE.md`
- Biography enrichment plan: `docs/1M-184-BIO-ENRICHMENT-PLAN.md`
- Entity system: `docs/features/ENTITY_SYSTEM.md`

---

*Last updated: 2025-11-26*
