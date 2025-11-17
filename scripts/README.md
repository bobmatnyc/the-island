# Scripts Index

**Last Updated**: November 16, 2025

This directory contains all scripts organized by purpose.

---

## 📁 DIRECTORY STRUCTURE

```
scripts/
├── README.md                          # This file
│
├── core/                              # Core library modules
│   ├── __init__.py                    # Module initialization
│   ├── database.py                    # SQLite database management
│   ├── deduplicator.py                # Deduplication logic
│   ├── hasher.py                      # Content hashing (SHA-256)
│   └── ocr_quality.py                 # OCR quality assessment
│
├── extraction/                        # PDF extraction scripts
│   └── extract_emails.py              # Extract emails from PDFs
│
├── canonicalization/                  # Deduplication scripts
│   ├── canonicalize.py                # Main canonicalization script
│   ├── canonicalize_emails.py         # Email-specific canonicalization
│   ├── initialize_deduplication.py    # Setup deduplication database
│   ├── process_bulk_emails.py         # Bulk email processing
│   └── query_deduplication.py         # Query deduplication database
│
├── analysis/                          # Analysis scripts
│   └── analyze_giuffre_maxwell_pdfs.py  # Analyze Giuffre-Maxwell docs
│
├── utilities/                         # Helper scripts
│   └── convert_emails_to_markdown.py  # PDF → Markdown converter
│
└── downloaders/                       # Download scripts (empty, ready)
```

---

## 🔧 CORE LIBRARY (`scripts/core/`)

### Purpose
Reusable library modules for deduplication, hashing, and database management.

### Modules

#### `database.py`
**Purpose**: SQLite database management for deduplication

**Key Classes**:
- `DeduplicationDatabase` - Main database interface
- Schema management (documents, sources, duplicates, metadata)

**Usage**:
```python
from core.database import DeduplicationDatabase

db = DeduplicationDatabase('data/metadata/deduplication.db')
db.add_document(content_hash, content, metadata)
```

#### `deduplicator.py`
**Purpose**: Main deduplication logic

**Key Classes**:
- `Deduplicator` - Content deduplication engine
- Fuzzy matching for near-duplicates
- Source tracking

**Usage**:
```python
from core.deduplicator import Deduplicator

dedup = Deduplicator(db)
canonical_id = dedup.add_or_find_duplicate(content, source, metadata)
```

#### `hasher.py`
**Purpose**: Content hashing for duplicate detection

**Key Functions**:
- `hash_content(text)` - SHA-256 hash of normalized text
- `normalize_text(text)` - Text normalization
- Whitespace handling

**Usage**:
```python
from core.hasher import hash_content

content_hash = hash_content("Email content here...")
```

#### `ocr_quality.py`
**Purpose**: OCR quality assessment for scanned documents

**Key Functions**:
- `assess_ocr_quality(text)` - Quality score (0-100)
- Character pattern analysis
- Confidence scoring

**Usage**:
```python
from core.ocr_quality import assess_ocr_quality

quality_score = assess_ocr_quality(extracted_text)
```

---

## 📥 EXTRACTION (`scripts/extraction/`)

### `extract_emails.py`
**Purpose**: Extract emails from PDF documents

**Features**:
- PDF text extraction using pdfplumber
- Email detection and parsing
- Metadata extraction (from, to, date, subject)
- Structured JSON output

**Usage**:
```bash
python3 scripts/extraction/extract_emails.py path/to/emails.pdf
```

**Output**:
- Individual email text files
- Structured JSON with metadata
- Extraction report

---

## 🔄 CANONICALIZATION (`scripts/canonicalization/`)

### `initialize_deduplication.py`
**Purpose**: Initialize or reset deduplication database

**Usage**:
```bash
python3 scripts/canonicalization/initialize_deduplication.py
```

**What it does**:
- Creates `data/metadata/deduplication.db`
- Sets up database schema (documents, sources, duplicates, metadata)
- Ready for deduplication

### `canonicalize.py`
**Purpose**: Main canonicalization script for all document types

**Features**:
- Process any document type (emails, court filings, etc.)
- Automatic duplicate detection
- Canonical file creation
- Source tracking

**Usage**:
```bash
python3 scripts/canonicalization/canonicalize.py --input data/sources/collection/ --type emails
```

### `canonicalize_emails.py`
**Purpose**: Email-specific canonicalization

**Features**:
- Email metadata preservation
- Thread detection
- Participant tracking
- Date normalization

**Usage**:
```bash
python3 scripts/canonicalization/canonicalize_emails.py
```

**What it does**:
1. Scans extracted emails
2. Checks for duplicates in database
3. Creates canonical copy in `data/canonical/emails/`
4. Updates deduplication database

### `process_bulk_emails.py`
**Purpose**: Bulk processing of entire email collections

**Features**:
- Batch processing of directories
- Progress tracking
- Error handling
- Summary reports

**Usage**:
```bash
python3 scripts/canonicalization/process_bulk_emails.py data/sources/giuffre_maxwell/
```

### `query_deduplication.py`
**Purpose**: Query and analyze deduplication database

**Features**:
- Statistics (total documents, duplicates, sources)
- Search by keyword
- Find duplicates
- List sources

**Usage**:
```bash
# Get statistics
python3 scripts/canonicalization/query_deduplication.py --stats

# Search for documents
python3 scripts/canonicalization/query_deduplication.py --search "Maxwell"

# Find all duplicates
python3 scripts/canonicalization/query_deduplication.py --duplicates
```

---

## 📊 ANALYSIS (`scripts/analysis/`)

### `analyze_giuffre_maxwell_pdfs.py`
**Purpose**: Analyze Giuffre v. Maxwell PDF collection

**Features**:
- PDF content analysis
- Document classification
- Metadata extraction
- Summary statistics

**Usage**:
```bash
python3 scripts/analysis/analyze_giuffre_maxwell_pdfs.py
```

**Output**:
- Analysis report
- Document classifications
- Metadata summaries

---

## 🛠️ UTILITIES (`scripts/utilities/`)

### `convert_emails_to_markdown.py`
**Purpose**: Convert PDF emails to Markdown format

**Features**:
- PDF → Markdown conversion
- Metadata preservation
- Formatting cleanup
- Structure preservation

**Usage**:
```bash
python3 scripts/utilities/convert_emails_to_markdown.py input.pdf output.md
```

---

## 📦 DOWNLOADERS (`scripts/downloaders/`)

### Status
**Currently empty** - Ready for automated download scripts

### Planned Scripts
- `download_internet_archive.py` - Internet Archive bulk downloads
- `download_documentcloud.py` - DocumentCloud API integration
- `download_fbi_vault.py` - FBI Vault automated retrieval
- `download_house_oversight.py` - House Oversight collection downloads

---

## 🚀 COMMON WORKFLOWS

### Extract and Canonicalize New PDFs
```bash
# 1. Extract emails from PDF
python3 scripts/extraction/extract_emails.py data/sources/new/file.pdf

# 2. Canonicalize extracted emails
python3 scripts/canonicalization/canonicalize_emails.py
```

### Bulk Process Entire Collection
```bash
# Process all PDFs in a directory
python3 scripts/canonicalization/process_bulk_emails.py data/sources/giuffre_maxwell/
```

### Query Deduplication Status
```bash
# Get statistics
python3 scripts/canonicalization/query_deduplication.py --stats

# Find duplicates
python3 scripts/canonicalization/query_deduplication.py --duplicates

# Search documents
python3 scripts/canonicalization/query_deduplication.py --search "keyword"
```

### Analyze Document Collection
```bash
# Analyze PDFs
python3 scripts/analysis/analyze_giuffre_maxwell_pdfs.py
```

---

## 🔍 SCRIPT DEPENDENCIES

### Python Packages Required
- **pdfplumber** - PDF text extraction
- **pypdfium2** - PDF rendering
- **PyYAML** - YAML config parsing
- **sqlite3** - Database (built-in)
- **hashlib** - Content hashing (built-in)

### Installation
```bash
pip install pdfplumber pypdfium2 PyYAML
```

---

## 🐛 TROUBLESHOOTING

### Import Errors
```bash
# Make sure you're in the project root
cd /Users/masa/Projects/Epstein

# Activate virtual environment
source .venv/bin/activate

# Verify Python packages installed
pip list | grep -E "(pdfplumber|pypdfium2|PyYAML)"
```

### Database Not Found
```bash
# Initialize deduplication database
python3 scripts/canonicalization/initialize_deduplication.py
```

### Module Not Found
```bash
# Run scripts from project root, not scripts/ directory
cd /Users/masa/Projects/Epstein
python3 scripts/canonicalization/canonicalize_emails.py
```

---

## 📝 ADDING NEW SCRIPTS

### Guidelines
1. **Place in appropriate directory**:
   - PDF extraction → `extraction/`
   - Deduplication → `canonicalization/`
   - Data analysis → `analysis/`
   - General helpers → `utilities/`
   - Download automation → `downloaders/`

2. **Use core library**: Import from `scripts/core/` for reusable logic

3. **Add to this README**: Document new scripts here

4. **Include docstrings**: Add usage examples and documentation

---

## 🎯 SCRIPT DEVELOPMENT PRIORITIES

### Immediate (This Week)
- [ ] Enhance `extract_emails.py` for better email detection
- [ ] Add error handling to bulk processing
- [ ] Improve OCR quality assessment

### Short-term (This Month)
- [ ] Build automated download scripts in `downloaders/`
- [ ] Create analysis scripts for other collections
- [ ] Add progress bars to bulk processing

### Long-term (Next 3 Months)
- [ ] Build web scraping for online databases
- [ ] Develop timeline analysis tools
- [ ] Create network graph generation scripts

---

*For complete project documentation, see [../docs/README.md](../docs/README.md)*
*For project status and resumption guide, see [../CLAUDE.md](../CLAUDE.md)*
