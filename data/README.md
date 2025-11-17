# Data Directory Organization

**Last Updated**: November 16, 2025

This directory contains all data files organized by stage and purpose.

---

## 📁 DIRECTORY STRUCTURE

```
data/
├── README.md                          # This file
│
├── sources/                           # Raw downloads (by collection)
│   ├── documentcloud_6250471/         # 2,024-page collection (partial)
│   ├── giuffre_maxwell/               # 4,553-page collection (partial)
│   ├── house_oversight_nov2025/       # 20,000-page collection (pending)
│   └── house_oversight_sept2025/      # 33,000 documents (pending)
│
├── canonical/                         # Deduplicated canonical documents
│   ├── emails/                        # 5 canonical emails ⭐
│   ├── court_filings/                 # Court documents
│   ├── fbi_reports/                   # FBI Vault documents
│   ├── financial/                     # Financial records
│   ├── flight_logs/                   # Flight logs
│   ├── address_books/                 # Address books
│   └── other/                         # Miscellaneous
│
├── emails/                            # Original 87-page email extraction
│   ├── epstein-emails-complete.pdf    # Original PDF (6.4 MB)
│   ├── epstein-emails-structured.json # Structured data
│   ├── pages/                         # Individual page extracts (87 files)
│   ├── markdown/                      # Converted markdown docs
│   ├── notes/                         # Processing notes
│   ├── EXTRACTION_REPORT.txt          # Extraction details
│   ├── MANIFEST.md                    # Document manifest
│   └── README.md                      # Collection info
│
├── metadata/                          # Databases and indexes
│   └── deduplication.db               # SQLite deduplication database ⭐
│
└── temp/                              # Temporary processing files
```

---

## 📥 SOURCES (`data/sources/`)

### Purpose
Raw downloaded documents organized by collection/source.

### Organization
Each collection has its own directory named by source:
- `documentcloud_XXXXXX/` - DocumentCloud collections
- `giuffre_maxwell/` - Giuffre v. Maxwell court documents
- `house_oversight_*/` - Congressional releases
- `fbi_vault_*/` - FBI Vault releases
- `internet_archive_*/` - Internet Archive collections

### Current Status

| Collection | Size | Files | Status |
|-----------|------|-------|--------|
| documentcloud_6250471 | ~50 MB | 2 PDFs | ⏳ Partial |
| giuffre_maxwell | ~100 MB | 15 PDFs | ⏳ Partial |
| house_oversight_nov2025 | 0 | 0 | ❌ Not downloaded |
| house_oversight_sept2025 | 0 | 0 | ❌ Not downloaded |

### Check Download Status
```bash
# List all downloaded sources
ls -lh data/sources/

# Count files in each collection
find data/sources/ -name "*.pdf" | wc -l

# Disk usage per collection
du -sh data/sources/*
```

---

## ✅ CANONICAL (`data/canonical/`)

### Purpose
Single source of truth for all deduplicated documents.

### Organization by Document Type
- **emails/** - Email communications (5 files currently)
- **court_filings/** - Legal filings, motions, orders
- **fbi_reports/** - FBI investigation documents
- **financial/** - Bank records, transactions
- **flight_logs/** - Private jet passenger logs
- **address_books/** - Contact lists
- **other/** - Miscellaneous documents

### File Naming Convention
```
{document_type}/{hash_prefix}/{content_hash}.md

Example:
emails/a1/a1b2c3d4e5f6...789.md
```

### Current Status
```bash
# Count canonical emails
find data/canonical/emails -name "*.md" | wc -l
# Result: 5 emails

# Total canonical documents
find data/canonical -name "*.md" | wc -l
# Result: 8 documents (5 emails + 3 court filings)
```

### Why Canonical?
- **No Duplicates**: Each unique document appears exactly once
- **Source Tracking**: All sources tracked in deduplication.db
- **Content Hash**: Filename is SHA-256 hash for verification
- **Markdown Format**: Searchable, version-controllable

---

## 📧 EMAILS (`data/emails/`)

### Purpose
Original 87-page email extraction (first processed collection).

### Contents
- **epstein-emails-complete.pdf** (6.4 MB) - Original source PDF
- **epstein-emails-structured.json** - Structured extraction data
- **pages/** - 87 individual page text files
- **markdown/** - Converted markdown documents
- **notes/** - Processing notes and observations

### This Was Our Starting Point
This collection (DocumentCloud 6506732) was the first processed and served as the foundation for building the extraction and deduplication system.

**Status**: ✅ Complete (100% processed)

---

## 💾 METADATA (`data/metadata/`)

### Purpose
Databases and indexes for deduplication and tracking.

### Files

#### `deduplication.db` (SQLite Database)
**Critical File** - Contains all deduplication tracking.

**Schema**:
- **documents** - Canonical documents with content hashes
- **sources** - All source files for each document
- **duplicates** - Detected duplicate relationships
- **metadata** - Document metadata (dates, participants, etc.)

**Query Database**:
```bash
python3 scripts/canonicalization/query_deduplication.py --stats
```

**Backup Regularly**:
```bash
cp data/metadata/deduplication.db data/metadata/deduplication.db.backup
```

---

## 🗑️ TEMP (`data/temp/`)

### Purpose
Temporary files during processing (automatically cleaned).

### Contents
- Intermediate extraction results
- Processing artifacts
- Download temp files

**Note**: This directory is in `.gitignore` and not committed to version control.

---

## 📊 DATA STATISTICS

### Current Data Size
```bash
# Total data directory size
du -sh data/
# Result: ~110 MB

# Sources size
du -sh data/sources/
# Result: ~100 MB

# Canonical size
du -sh data/canonical/
# Result: ~50 KB (5 emails)

# Emails size
du -sh data/emails/
# Result: ~7 MB
```

### Document Counts
- **Canonical Emails**: 5
- **Source PDFs**: ~17 files
- **Processed Pages**: 87 pages (from emails/)
- **Target**: 20,000 emails

### Progress
- **Emails Progress**: 0.025% (5 of 20,000)
- **Collections Downloaded**: 2 partial collections
- **Collections Pending**: 30+ collections

---

## 🎯 DATA WORKFLOW

### Document Processing Pipeline
```
1. DOWNLOAD → data/sources/{collection}/
   ↓
2. EXTRACT → temp processing
   ↓
3. DEDUPLICATE → check data/metadata/deduplication.db
   ↓
4. CANONICALIZE → data/canonical/{type}/{hash}.md
   ↓
5. INDEX → update deduplication.db
```

### Example: Processing New PDF
```bash
# 1. Download to sources
curl -o data/sources/new_collection/file.pdf https://example.com/file.pdf

# 2. Extract emails
python3 scripts/extraction/extract_emails.py data/sources/new_collection/file.pdf

# 3. Canonicalize (deduplicates automatically)
python3 scripts/canonicalization/canonicalize_emails.py

# 4. Verify in canonical directory
find data/canonical/emails -name "*.md" | wc -l
```

---

## 🔍 DATA QUALITY

### Quality Assurance
- **SHA-256 Hashing**: Every document has content hash for integrity
- **Source Tracking**: All original sources recorded in database
- **Duplicate Detection**: Automatic deduplication prevents redundancy
- **OCR Quality**: Scanned documents assessed for quality

### Verification Commands
```bash
# Verify deduplication database integrity
python3 scripts/canonicalization/query_deduplication.py --stats

# Check for orphaned files (in canonical but not in DB)
# (script needed - TODO)

# Verify file hashes match database
# (script needed - TODO)
```

---

## 💡 BEST PRACTICES

### When Adding New Data
1. ✅ Download to appropriate `sources/` subdirectory
2. ✅ Name directory clearly (e.g., `fbi_vault_part_01/`)
3. ✅ Run extraction scripts
4. ✅ Run canonicalization
5. ✅ Verify canonical documents created
6. ✅ Update this README if new data types added

### When Processing Data
1. ✅ Always use canonicalization scripts (don't manually copy)
2. ✅ Check deduplication database before and after
3. ✅ Verify canonical count increased
4. ✅ Backup deduplication.db regularly

### Data Integrity
1. ✅ Never edit canonical files directly
2. ✅ Always regenerate from sources if needed
3. ✅ Keep deduplication.db backed up
4. ✅ Track all sources in version control (except large PDFs)

---

## 🚨 IMPORTANT NOTES

### What's in Git
- ✅ Directory structure
- ✅ README files
- ✅ Small metadata files (.json, .txt, MANIFEST.md)
- ✅ Markdown documentation
- ❌ Large PDFs (in .gitignore)
- ❌ Temporary files (in .gitignore)
- ⚠️ deduplication.db (tracked, but backup regularly)

### What's NOT in Git (Too Large)
- PDFs in `sources/` (use external storage/backup)
- Large processing artifacts
- Temporary extraction files

### Backup Strategy
```bash
# Backup critical data (excluding large PDFs)
tar -czf epstein-data-backup.tar.gz \
  data/canonical/ \
  data/metadata/ \
  data/emails/*.json \
  data/emails/*.txt \
  data/emails/markdown/

# Backup deduplication database separately
cp data/metadata/deduplication.db ~/Backups/deduplication-$(date +%Y%m%d).db
```

---

## 📈 DATA GROWTH PLAN

### Current State (November 16, 2025)
- **Canonical Emails**: 5
- **Downloaded Collections**: 2 partial
- **Total Size**: ~110 MB

### 30-Day Target
- **Canonical Emails**: 1,000+
- **Downloaded Collections**: 5 complete
- **Total Size**: ~2 GB

### 90-Day Target
- **Canonical Emails**: 10,000+
- **Downloaded Collections**: 15+ complete
- **Total Size**: ~8 GB

### 6-Month Target
- **Canonical Emails**: 20,000 (GOAL!)
- **Downloaded Collections**: 30+ complete
- **Total Size**: ~15 GB

---

## 🔗 RELATED FILES

- **Project Overview**: [../README.md](../README.md)
- **Resume Guide**: [../CLAUDE.md](../CLAUDE.md)
- **Documentation**: [../docs/README.md](../docs/README.md)
- **Scripts**: [../scripts/README.md](../scripts/README.md)

---

*For current data statistics, always run queries against `data/metadata/deduplication.db`*
*For data organization help, see [../CLAUDE.md](../CLAUDE.md) Common Operations section*
