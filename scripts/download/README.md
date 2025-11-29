# Epstein Document Archive - Download & Deduplication System

## Overview

Comprehensive download and deduplication system for Epstein document sources. Automatically downloads from public repositories, deduplicates via content hashing, and maintains complete provenance tracking.

## Quick Start

### Download New Sources
```bash
python3 download_all_sources.py
```

### Query Master Index
```bash
# Show statistics
python3 query_master_index.py --stats

# Find duplicates
python3 query_master_index.py --duplicates

# Query specific source
python3 query_master_index.py --source fbi_vault

# Find cross-source duplicates
python3 query_master_index.py --cross-source
```

## Features

### Automated Download
- **FBI Vault**: Downloads all 22 parts (Part 22 currently unavailable)
- **DocumentCloud**: Downloads major public releases
- **DOJ Official**: Downloads declassified documents
- **Internet Archive**: Attempts download from archive.org

### Deduplication
- **Content Hashing**: SHA256 hash of entire file
- **Real-time Detection**: Identifies duplicates during download
- **Canonical Selection**: Prioritizes authoritative sources (DOJ > FBI > DocumentCloud)
- **Provenance Tracking**: Records all locations where document appears

### Master Index
- **38,177 unique documents** tracked
- **Complete provenance** for every file
- **Cross-source identification** of duplicate documents
- **Efficient querying** via command-line tools

## System Architecture

```
download_all_sources.py
  ↓
Download from sources → Calculate SHA256 → Check for duplicates
  ↓                                               ↓
Save file                                    Log duplicate
  ↓                                               ↓
Add to master index ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
  ↓
Generate reports
  ↓
Build master_document_index.json
```

## Files Generated

1. **master_document_index.json** (`data/metadata/`)
   - Complete provenance index
   - 38,177 unique document entries
   - Source tracking for all files

2. **download_log.json** (`data/metadata/`)
   - Download session log
   - Success/failure tracking
   - Duplicate detection records

3. **DOWNLOAD_DEDUPLICATION_REPORT.md** (project root)
   - Comprehensive statistics
   - Top documents by size
   - Duplicate analysis
   - Cross-source overlap

4. **download_all_sources.log** (`logs/`)
   - Complete execution log
   - Error tracking
   - Performance metrics

## Statistics (Latest Run)

- **Total Files**: 67,963
- **Unique Documents**: 38,177
- **Duplicates Removed**: 29,786
- **Deduplication Rate**: 43.8%
- **Storage Saved**: 10.1 GB
- **New Downloads**: 25 documents (437 MB)

## Sources

| Source | Documents | Status |
|--------|-----------|--------|
| FBI Vault | 21 | ✅ Downloaded (Part 22 unavailable) |
| DocumentCloud | 3 | ✅ Downloaded |
| DOJ Official | 1 | ✅ Downloaded |
| Internet Archive | 0 | ❌ URL no longer valid |
| Google Pinpoint | 0 | ⚠️ Requires manual download |
| CourtListener | 0 | ⚠️ Requires API/manual download |

## Usage Examples

### Download All Available Sources
```bash
python3 download_all_sources.py
```
Output: Downloads from FBI Vault, DocumentCloud, DOJ, and Internet Archive (if available)

### View Statistics
```bash
python3 query_master_index.py --stats
```
Output:
```
Total Files: 67,963
Unique Documents: 38,177
Duplicate Sets: 3,941
Deduplication Rate: 43.8%
```

### Find Cross-Source Duplicates
```bash
python3 query_master_index.py --cross-source
```
Output: Lists documents appearing in multiple sources with full provenance

### Query Specific Source
```bash
python3 query_master_index.py --source fbi_vault
```
Output: All 21 FBI Vault documents with sizes and hashes

### Search by Hash
```bash
python3 query_master_index.py --hash 674c8534
```
Output: Full document details, all source locations, size, canonical path

## Deduplication Algorithm

1. **Download File**: Fetch from remote source
2. **Calculate Hash**: SHA256 of entire file content
3. **Check Duplicates**: Compare against known hashes
4. **Action**:
   - If duplicate: Delete file, log duplicate
   - If unique: Add hash to set, keep file
5. **Record Provenance**: Track all locations in index

## Canonical File Selection

Priority order for choosing canonical (primary) version:
1. **doj_official** - Authoritative government source
2. **fbi_vault** - FBI investigative files
3. **documentcloud** - Curated public releases
4. **Other sources** - Alphabetically

## Master Index Format

```json
{
  "generated_at": "2025-11-17T04:36:47Z",
  "total_files": 67963,
  "unique_documents": 38177,
  "duplicate_sets": 3941,
  "total_duplicates": 29786,
  "sources": {
    "fbi_vault": {
      "path": "data/sources/fbi_vault",
      "document_count": 21
    }
  },
  "documents": [
    {
      "hash": "7c292dfa6ecb24c2...",
      "canonical_path": "data/sources/fbi_vault/jeffrey_epstein_part_01.pdf",
      "size": 2662470,
      "sources": [
        "data/sources/fbi_vault/jeffrey_epstein_part_01.pdf"
      ],
      "source_count": 1,
      "duplicate_count": 0
    }
  ]
}
```

## Performance

### Download Speed
- **FBI Vault**: ~3 files/second
- **DocumentCloud**: ~31 MB/second
- **Total Download Time**: ~2 minutes for 25 files

### Deduplication Speed
- **Hashing**: ~2,265 files/second
- **Index Generation**: ~1 second
- **Total Time**: ~31 seconds for 67,963 files

## Error Handling

### Automatic Retry
- **Max Retries**: 3 attempts (5 for large files)
- **Backoff**: Exponential (2^attempt seconds)
- **Timeout**: 60 seconds per request

### Known Issues
1. **FBI Vault Part 22**: Returns 404 (may not exist)
2. **Internet Archive**: URL changed or file removed
3. **MacOS Metadata**: 29,746 `__MACOSX` files in house_oversight_nov2025

## Manual Download Required

Some sources cannot be automated:

1. **Google Pinpoint Collection**
   - URL: https://journaliststudio.google.com/pinpoint/search?collection=092314e384a58618
   - Requires: Google account and UI interaction

2. **CourtListener**
   - Giuffre v Maxwell: https://www.courtlistener.com/docket/4355835/
   - Criminal Case: https://www.courtlistener.com/docket/15887848/
   - Requires: API key or manual download

## Next Steps

After download and deduplication:
1. **OCR Processing**: Extract text from all unique PDFs
2. **Document Classification**: Classify by type (email, court filing, etc.)
3. **Entity Extraction**: Extract names, dates, locations
4. **Timeline Building**: Create chronological timeline
5. **Network Analysis**: Build entity relationship network

## Verification

Run verification check:
```bash
python3 -c "
import json
from pathlib import Path
index = json.load(open('../../data/metadata/master_document_index.json'))
print(f'✓ Unique documents: {index[\"unique_documents\"]:,}')
print(f'✓ Duplicates removed: {index[\"total_duplicates\"]:,}')
print(f'✓ Deduplication rate: {index[\"total_duplicates\"] / index[\"total_files\"] * 100:.1f}%')
"
```

## Troubleshooting

### Download Failures
**Symptom**: Some downloads return 404 or timeout
**Solution**: Check logs/download_all_sources.log for specific errors. Some sources may have moved or been removed.

### Duplicate Count Seems High
**Symptom**: 43.8% deduplication rate
**Cause**: MacOS metadata files (.__MACOSX) are duplicates, many court documents appear in multiple collections
**Verification**: Check cross-source duplicates to see expected overlap

### Query Tool Errors
**Symptom**: Query tool returns no results
**Solution**: Ensure master_document_index.json exists in data/metadata/. Re-run download_all_sources.py to regenerate.

## Contributing

To add new sources:
1. Add download method to `EpsteinDocumentDownloader` class
2. Call method in `main()` function
3. Update source documentation in this README
4. Test deduplication works correctly
5. Verify master index includes new source

## License

See project LICENSE file.

## Contact

See project README.md for contribution guidelines and contact information.
