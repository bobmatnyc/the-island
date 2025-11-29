# Entity Document Merge Script

## Overview

`merge_entity_documents.py` merges document reference data from `entity_document_index.json` into `entity_statistics.json` to resolve the blocking issue for bio enrichment.

## Problem Solved

**Issue**: Bio enrichment script expects document references inside `entity_statistics.json`, but document linking created a separate `entity_document_index.json` file.

**Before**: All 1,637 entities showed `"documents": []` and `"total_documents": 0`

**After**: 69 entities now have proper document references (12,277 total document entries)

## Usage

### Basic Usage

```bash
# Execute merge with backup (recommended)
python3 scripts/merge_entity_documents.py --backup

# Preview changes without modifying files
python3 scripts/merge_entity_documents.py --dry-run --verbose

# Execute without backup (not recommended)
python3 scripts/merge_entity_documents.py --no-backup
```

### Command-Line Arguments

- `--dry-run` - Show what would change without writing files
- `--backup` - Create timestamped backup before merge (default: true)
- `--no-backup` - Skip backup creation
- `--verbose` / `-v` - Detailed logging with entity-by-entity updates

## Results

### Merge Statistics

```
✅ Entities updated: 69
📄 Documents added: 12,277
⏭️  Duplicates skipped: 0
⚠️  Entities not found: 0
📚 Total document entries processed: 69
```

### Top Entities by Document Count

| Entity | Documents |
|--------|-----------|
| Jeffrey Epstein | 6,998 |
| Ghislaine Maxwell | 4,421 |
| Sarah Kellen | 173 |
| Virginia Roberts | 125 |
| Michael | 82 |

### File Size Impact

- **Before**: `entity_statistics.json` = 832 KB
- **After**: `entity_statistics.json` = 2.7 MB
- **Growth**: +1.9 MB (document references added)

## Technical Details

### Name Matching Strategy

The script uses a multi-key hash map approach for O(n) complexity:

1. **Exact GUID match** (if available)
2. **Normalized name match** (case-insensitive)
3. **Name variation match** (handles "Last, First" and "First Last" formats)

### Document Format Conversion

**Input** (entity_document_index.json):
```json
{
  "doc_id": "DOJ-OGR-00022924",
  "filename": "DOJ-OGR-00022924.txt",
  "mentions": 50
}
```

**Output** (entity_statistics.json):
```json
{
  "path": "data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-00022924.txt",
  "type": "text",
  "mentions": 50,
  "context": null
}
```

### Error Handling

- ✅ Deduplicates document references
- ✅ Logs missing entities (0 found in this run)
- ✅ Preserves all existing entity fields
- ✅ Creates timestamped backup before modification

## Verification

```bash
# Check specific entities
python3 -c "
import json
with open('data/metadata/entity_statistics.json', 'r') as f:
    stats = json.load(f)

epstein = stats['statistics']['jeffrey_epstein']
print(f'Jeffrey Epstein: {epstein[\"total_documents\"]} documents')
print(f'Sample: {epstein[\"documents\"][0][\"path\"]}')
"
```

### Expected Output

```
Jeffrey Epstein: 6998 documents
Sample: data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-00027419.txt
```

## Backup Files

Backups are created with timestamp format:
```
entity_statistics_backup_YYYYMMDD_HHMMSS.json
```

Example:
```
data/metadata/entity_statistics_backup_20251124_181746.json
```

## Next Steps

Now that document references are merged, you can:

1. ✅ Run bio enrichment script (no longer blocked)
2. ✅ Generate entity biographies with document context
3. ✅ Create entity detail pages with document lists
4. ✅ Implement document mention highlighting

## Performance

- **Time Complexity**: O(n + m) where n = entities, m = document entries
- **Space Complexity**: O(n) for hash map lookups
- **Execution Time**: ~2 seconds for 1,637 entities + 69 document entries
- **Memory Usage**: ~50 MB peak (loading JSON files)

## Files Modified

- ✅ `/data/metadata/entity_statistics.json` - Updated with document references
- ✅ `/data/metadata/entity_statistics_backup_*.json` - Backup created

## Files Referenced

- 📖 `/data/metadata/entity_document_index.json` - Source of document data (read-only)
