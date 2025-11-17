# Epstein Document Canonicalization System
## System Design Specification v1.0

**Date**: November 16, 2025
**Status**: Implementation Ready
**Target Scale**: 100,000+ documents across 30+ sources

---

## Executive Summary

This system provides a robust framework for downloading, deduplicating, and canonicalizing Epstein-related documents from multiple sources. It handles significant overlap between collections while preserving complete provenance information.

### Key Features
- **Content-based deduplication** using SHA-256 hashing with fuzzy matching for OCR variations
- **Multi-source provenance tracking** - every canonical document tracks all sources where it appears
- **Quality-based version selection** - automatically chooses the best version based on OCR quality, redactions, completeness
- **Standardized YAML frontmatter** - consistent metadata across all documents
- **Scalable architecture** - handles 100,000+ documents efficiently
- **Partial overlap handling** - manages documents that share some but not all pages

---

## Architecture Overview

### Data Flow
```
┌─────────────────┐
│  Source A       │
│  (20,000 docs)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Download       │───▶│  Hash & Extract  │───▶│  Deduplicate    │
│  with Metadata  │    │  Metadata        │    │  & Merge        │
└─────────────────┘    └──────────────────┘    └────────┬────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                           ┌─────────────────┐
│  Source B       │                           │  Canonical      │
│  (4,500 docs)   │                           │  Collection     │
└─────────────────┘                           │  + Index DB     │
                                              └─────────────────┘
```

### Component Architecture
```
/Epstein/
├── scripts/
│   ├── download_collection.py      # Source-specific downloaders
│   ├── hash_documents.py           # Hash generation & extraction
│   ├── deduplicate.py              # Deduplication engine
│   ├── canonicalize.py             # Canonical version creation
│   ├── verify_completeness.py      # Quality checks
│   └── quality_report.py           # Statistics & reports
│
├── data/
│   ├── sources/                    # Raw downloads (one dir per source)
│   │   ├── documentcloud_6506732/
│   │   ├── house_oversight_nov2025/
│   │   ├── giuffre_maxwell/
│   │   └── ...
│   │
│   ├── canonical/                  # Deduplicated canonical versions
│   │   ├── emails/
│   │   ├── court_filings/
│   │   ├── financial/
│   │   ├── flight_logs/
│   │   └── other/
│   │
│   └── metadata/                   # Tracking databases
│       ├── deduplication_index.db  # SQLite database
│       ├── source_manifest.json    # All source metadata
│       ├── quality_report.json     # Quality metrics
│       └── duplicate_map.json      # Duplicate relationships
│
└── config/
    ├── source_definitions.yaml     # Source configurations
    └── canonicalization_rules.yaml # Deduplication rules
```

---

## Database Schema

### SQLite Schema (`deduplication_index.db`)

#### Table: `canonical_documents`
```sql
CREATE TABLE canonical_documents (
    canonical_id TEXT PRIMARY KEY,           -- Format: epstein_doc_[content_hash]
    content_hash TEXT NOT NULL,              -- SHA-256 of normalized content
    file_hash TEXT NOT NULL,                 -- SHA-256 of original file
    document_type TEXT NOT NULL,             -- email|court_filing|memo|invoice|etc
    title TEXT,
    date TEXT,                               -- ISO 8601: YYYY-MM-DD
    from_person TEXT,
    to_persons TEXT,                         -- JSON array
    subject TEXT,

    -- Quality metrics
    ocr_quality REAL,                        -- 0.0-1.0
    has_redactions BOOLEAN,
    completeness TEXT,                       -- complete|partial|fragment
    page_count INTEGER,

    -- Source selection
    primary_source TEXT,                     -- Source name chosen as canonical
    selection_reason TEXT,                   -- Why this version was chosen

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(content_hash)
);
```

#### Table: `document_sources`
```sql
CREATE TABLE document_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    source_name TEXT NOT NULL,               -- e.g., "DocumentCloud 6506732"
    source_url TEXT,
    collection TEXT,                         -- e.g., "Florida Public Records"
    download_date TEXT,                      -- ISO 8601
    pages TEXT,                              -- e.g., "1-5" or "523-527"
    file_path TEXT,                          -- Path to source file

    -- Quality metrics for this source
    quality_score REAL,                      -- 0.0-1.0
    file_size INTEGER,
    format TEXT,                             -- pdf|txt|docx|etc

    FOREIGN KEY (canonical_id) REFERENCES canonical_documents(canonical_id),
    UNIQUE(canonical_id, source_name)
);
```

#### Table: `duplicate_groups`
```sql
CREATE TABLE duplicate_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_id TEXT NOT NULL,
    duplicate_type TEXT,                     -- exact|fuzzy|partial
    similarity_score REAL,                   -- 0.0-1.0
    detection_method TEXT,                   -- file_hash|content_hash|fuzzy_match

    FOREIGN KEY (canonical_id) REFERENCES canonical_documents(canonical_id)
);
```

#### Table: `partial_overlaps`
```sql
CREATE TABLE partial_overlaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_a_canonical_id TEXT NOT NULL,
    doc_b_canonical_id TEXT NOT NULL,
    overlap_type TEXT,                       -- page_range|content_subset|attachment
    overlap_percentage REAL,                 -- 0.0-1.0
    pages_a TEXT,                            -- Page range in doc A
    pages_b TEXT,                            -- Page range in doc B

    FOREIGN KEY (doc_a_canonical_id) REFERENCES canonical_documents(canonical_id),
    FOREIGN KEY (doc_b_canonical_id) REFERENCES canonical_documents(canonical_id)
);
```

#### Table: `processing_log`
```sql
CREATE TABLE processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation TEXT,                          -- download|hash|deduplicate|canonicalize
    source TEXT,
    status TEXT,                             -- success|error|warning
    message TEXT,
    details TEXT                             -- JSON
);
```

---

## YAML Frontmatter Schema

### Standard Template
```yaml
---
# Canonical Identification
canonical_id: "epstein_doc_[content_hash_first_12]"
document_type: "email|court_filing|memo|invoice|flight_log|address_book|fbi_report|deposition|other"
title: "Descriptive title of document"
date: "YYYY-MM-DD"  # Primary date (sent/filed/created)

# Content Classification
category: "legal|financial|personal|administrative|investigative"
tags: ["tag1", "tag2", "tag3"]
sensitivity: "public|confidential|sealed"

# Source Tracking (list ALL sources where this document appears)
sources:
  - source_name: "DocumentCloud 6506732"
    url: "https://www.documentcloud.org/documents/6506732-Epstein-Emails-Doc-Dump/"
    download_date: "2025-11-16"
    pages: "1-5"
    collection: "Florida Public Records 2019"
    quality_score: 0.95
    file_path: "data/sources/documentcloud_6506732/doc_001.pdf"

  - source_name: "House Oversight Nov 2025"
    url: "https://oversight.house.gov/..."
    download_date: "2025-11-17"
    pages: "523-527"
    collection: "Estate Document Release"
    quality_score: 0.88
    file_path: "data/sources/house_oversight_nov2025/file_523.pdf"

# Metadata (document-specific fields)
from: "person@example.com"
to: ["recipient1@example.com", "recipient2@example.com"]
cc: ["cc@example.com"]
subject: "Subject line for emails"
attachments: ["attachment1.pdf", "attachment2.xlsx"]

# For court documents
case_number: "1:15-cv-07433-LAP"
court: "U.S. District Court, Southern District of New York"
filing_type: "motion|deposition|exhibit|order"

# For financial documents
amount: "$1,000,000"
transaction_date: "2008-05-15"
account: "JPMorgan Chase Account #12345"

# Deduplication Information
duplicates_found: 2
primary_source: "DocumentCloud 6506732"
selection_reason: "Higher OCR quality (0.95 vs 0.88), fewer redactions"
content_hash: "sha256:abc123def456..."
file_hash: "sha256:789ghi012jkl..."
fuzzy_hash: "ssdeep:3072:abc..."  # For near-duplicate detection

# Quality Metrics
ocr_quality: 0.95  # 0.0-1.0 (low/medium/high)
redactions: false
completeness: "complete"  # complete|partial|fragment
page_count: 5
file_size: 1234567  # bytes
format: "pdf|txt|docx"

# Processing Metadata
extracted_at: "2025-11-16T10:30:00Z"
extracted_by: "canonicalize.py v1.0"
version: 1
---
```

### Minimal Required Fields
```yaml
---
canonical_id: "epstein_doc_abc123"
document_type: "email"
title: "Document title"
date: "2025-11-16"
sources:
  - source_name: "Source Name"
    download_date: "2025-11-16"
content_hash: "sha256:..."
---
```

---

## Deduplication Algorithm

### Phase 1: Exact Matching
```python
def detect_exact_duplicates(documents):
    """
    Identify exact duplicates using file hash and content hash.

    Returns:
        groups: List of duplicate groups
    """
    file_hash_map = {}      # file_hash -> [doc_ids]
    content_hash_map = {}   # content_hash -> [doc_ids]

    for doc in documents:
        # File hash (exact binary match)
        file_hash = sha256_hash(doc.file_path)
        file_hash_map.setdefault(file_hash, []).append(doc.id)

        # Content hash (normalized text)
        content = normalize_text(extract_text(doc))
        content_hash = sha256_hash(content)
        content_hash_map.setdefault(content_hash, []).append(doc.id)

    # Create duplicate groups
    groups = []
    for hash_val, doc_ids in content_hash_map.items():
        if len(doc_ids) > 1:
            groups.append({
                'type': 'exact',
                'docs': doc_ids,
                'hash': hash_val,
                'similarity': 1.0
            })

    return groups
```

### Phase 2: Fuzzy Matching (OCR Variations)
```python
def detect_fuzzy_duplicates(documents, threshold=0.90):
    """
    Identify near-duplicates using fuzzy hashing and text similarity.

    Args:
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        groups: List of fuzzy duplicate groups
    """
    import ssdeep
    from difflib import SequenceMatcher

    fuzzy_hashes = {}
    text_content = {}

    for doc in documents:
        # Extract and normalize text
        text = normalize_text(extract_text(doc))
        text_content[doc.id] = text

        # Generate fuzzy hash (ssdeep)
        fuzzy_hash = ssdeep.hash(text)
        fuzzy_hashes[doc.id] = fuzzy_hash

    # Compare all pairs
    groups = []
    compared = set()

    for doc_a in documents:
        for doc_b in documents:
            if doc_a.id >= doc_b.id:
                continue

            pair = (doc_a.id, doc_b.id)
            if pair in compared:
                continue
            compared.add(pair)

            # Fuzzy hash comparison
            fuzzy_sim = ssdeep.compare(
                fuzzy_hashes[doc_a.id],
                fuzzy_hashes[doc_b.id]
            ) / 100.0

            # Text similarity (for short docs)
            text_sim = SequenceMatcher(
                None,
                text_content[doc_a.id][:10000],
                text_content[doc_b.id][:10000]
            ).ratio()

            # Combined score
            similarity = max(fuzzy_sim, text_sim)

            if similarity >= threshold:
                groups.append({
                    'type': 'fuzzy',
                    'docs': [doc_a.id, doc_b.id],
                    'similarity': similarity,
                    'method': 'ssdeep' if fuzzy_sim > text_sim else 'text_diff'
                })

    return groups
```

### Phase 3: Metadata Matching (Emails)
```python
def detect_metadata_duplicates(documents, doc_type='email'):
    """
    Identify duplicates using metadata (from/to/date/subject).
    Useful for emails that may have different OCR but same metadata.
    """
    metadata_map = {}

    for doc in documents:
        if doc.document_type != doc_type:
            continue

        # Create metadata signature
        signature = (
            doc.from_person,
            frozenset(doc.to_persons or []),
            doc.date,
            normalize_subject(doc.subject)
        )

        metadata_map.setdefault(signature, []).append(doc.id)

    # Groups with matching metadata
    groups = []
    for signature, doc_ids in metadata_map.items():
        if len(doc_ids) > 1:
            groups.append({
                'type': 'metadata',
                'docs': doc_ids,
                'signature': signature,
                'similarity': 0.95  # High confidence for metadata match
            })

    return groups
```

### Phase 4: Partial Overlap Detection
```python
def detect_partial_overlaps(documents):
    """
    Detect documents that share some pages but not all.
    E.g., Doc A has pages 1-10, Doc B has pages 5-15.
    """
    overlaps = []

    for doc_a in documents:
        for doc_b in documents:
            if doc_a.id >= doc_b.id:
                continue

            # Extract page hashes
            pages_a = hash_pages(doc_a)
            pages_b = hash_pages(doc_b)

            # Find common pages
            common = set(pages_a.values()) & set(pages_b.values())

            if common:
                overlap_pct_a = len(common) / len(pages_a)
                overlap_pct_b = len(common) / len(pages_b)

                if 0.1 < overlap_pct_a < 0.9 or 0.1 < overlap_pct_b < 0.9:
                    overlaps.append({
                        'doc_a': doc_a.id,
                        'doc_b': doc_b.id,
                        'common_pages': len(common),
                        'overlap_pct_a': overlap_pct_a,
                        'overlap_pct_b': overlap_pct_b,
                        'type': 'partial'
                    })

    return overlaps
```

---

## Best Version Selection Algorithm

### Priority Criteria (in order)

1. **OCR Quality Score** (40% weight)
   - Calculated using character recognition confidence
   - Tests: Word dictionary matches, character corruption rate
   - Range: 0.0 (poor) to 1.0 (excellent)

2. **Redaction Level** (25% weight)
   - Count of redacted sections
   - Fewer redactions = better
   - Binary: redacted vs. unredacted

3. **Completeness** (20% weight)
   - Page count completeness
   - complete > partial > fragment
   - Checks for missing pages

4. **Source Authority** (10% weight)
   - Court records > Government FOIA > Media
   - Official releases preferred over third-party

5. **File Quality** (5% weight)
   - Resolution for images
   - File size (larger often better for PDFs)
   - Format (searchable PDF > scanned PDF > images)

### Selection Algorithm
```python
def select_best_version(duplicate_group):
    """
    Choose the best version from a group of duplicates.

    Returns:
        best_doc_id, selection_reason
    """
    scores = {}

    for doc in duplicate_group:
        score = 0.0
        reasons = []

        # OCR Quality (40%)
        ocr_score = calculate_ocr_quality(doc)
        score += ocr_score * 0.40
        if ocr_score > 0.9:
            reasons.append(f"High OCR quality ({ocr_score:.2f})")

        # Redactions (25%)
        if not doc.has_redactions:
            score += 0.25
            reasons.append("No redactions")
        else:
            redaction_penalty = count_redactions(doc) * 0.05
            score += max(0, 0.25 - redaction_penalty)

        # Completeness (20%)
        completeness_scores = {
            'complete': 0.20,
            'partial': 0.10,
            'fragment': 0.0
        }
        comp_score = completeness_scores.get(doc.completeness, 0)
        score += comp_score
        if doc.completeness == 'complete':
            reasons.append("Complete document")

        # Source Authority (10%)
        authority_scores = {
            'court_record': 0.10,
            'government_foia': 0.08,
            'official_release': 0.06,
            'media': 0.04,
            'archive': 0.02
        }
        auth_score = authority_scores.get(doc.source_type, 0)
        score += auth_score

        # File Quality (5%)
        quality_score = calculate_file_quality(doc)
        score += quality_score * 0.05

        scores[doc.id] = {
            'score': score,
            'reasons': reasons,
            'doc': doc
        }

    # Select best
    best_id = max(scores.keys(), key=lambda k: scores[k]['score'])
    best_info = scores[best_id]

    return best_id, "; ".join(best_info['reasons'])
```

---

## Directory Structure

```
/Users/masa/Projects/Epstein/
│
├── data/
│   ├── sources/                              # Raw downloads (one directory per source)
│   │   ├── documentcloud_6506732/
│   │   │   ├── manifest.json                 # Source metadata
│   │   │   ├── doc_001.pdf
│   │   │   ├── doc_002.pdf
│   │   │   └── ...
│   │   │
│   │   ├── house_oversight_nov2025/
│   │   │   ├── manifest.json
│   │   │   ├── emails/
│   │   │   ├── court_docs/
│   │   │   └── ...
│   │   │
│   │   ├── giuffre_maxwell/
│   │   │   ├── manifest.json
│   │   │   ├── batch_01/
│   │   │   ├── batch_02/
│   │   │   └── ...
│   │   │
│   │   └── [other_sources]/
│   │
│   ├── canonical/                            # Deduplicated canonical versions
│   │   ├── emails/
│   │   │   ├── 2006/
│   │   │   │   ├── epstein_doc_abc123.md
│   │   │   │   └── epstein_doc_def456.md
│   │   │   ├── 2007/
│   │   │   └── ...
│   │   │
│   │   ├── court_filings/
│   │   │   ├── giuffre_v_maxwell/
│   │   │   ├── sdny_criminal/
│   │   │   └── jpmorgan_usvi/
│   │   │
│   │   ├── financial/
│   │   │   ├── bank_records/
│   │   │   ├── invoices/
│   │   │   └── transactions/
│   │   │
│   │   ├── flight_logs/
│   │   │
│   │   ├── address_books/
│   │   │
│   │   ├── fbi_reports/
│   │   │
│   │   └── other/
│   │
│   └── metadata/                             # Tracking and analysis databases
│       ├── deduplication_index.db            # SQLite database (schema above)
│       ├── source_manifest.json              # All source metadata
│       ├── quality_report.json               # Quality metrics by source
│       ├── duplicate_map.json                # Duplicate relationships
│       ├── processing_stats.json             # Statistics
│       └── timeline_index.json               # Chronological index
│
├── scripts/                                  # Python processing scripts
│   ├── core/                                 # Core library modules
│   │   ├── __init__.py
│   │   ├── hasher.py                         # Hashing utilities
│   │   ├── deduplicator.py                   # Deduplication engine
│   │   ├── ocr_quality.py                    # OCR quality assessment
│   │   ├── metadata_extractor.py             # Metadata extraction
│   │   └── database.py                       # SQLite interface
│   │
│   ├── downloaders/                          # Source-specific downloaders
│   │   ├── download_documentcloud.py
│   │   ├── download_house_oversight.py
│   │   ├── download_internet_archive.py
│   │   └── download_fbi_vault.py
│   │
│   ├── download_collection.py                # Generic download orchestrator
│   ├── hash_documents.py                     # Hash generation
│   ├── deduplicate.py                        # Main deduplication script
│   ├── canonicalize.py                       # Canonical version creation
│   ├── verify_completeness.py                # Quality verification
│   └── quality_report.py                     # Statistics generation
│
└── config/                                   # Configuration files
    ├── source_definitions.yaml               # Source configurations
    ├── canonicalization_rules.yaml           # Deduplication rules
    └── document_types.yaml                   # Document type definitions
```

---

## Processing Pipeline

### Step 1: Download Collection
```bash
python scripts/download_collection.py \
    --source "house_oversight_nov2025" \
    --url "https://oversight.house.gov/..." \
    --output "data/sources/house_oversight_nov2025"
```

**Creates:**
- `data/sources/house_oversight_nov2025/manifest.json`
- All downloaded files
- Processing log entries

### Step 2: Hash Documents
```bash
python scripts/hash_documents.py \
    --source-dir "data/sources/house_oversight_nov2025" \
    --update-db
```

**Creates:**
- Content hashes for all documents
- File hashes
- Fuzzy hashes (ssdeep)
- Extracts basic metadata
- Updates `deduplication_index.db`

### Step 3: Deduplicate
```bash
python scripts/deduplicate.py \
    --all-sources \
    --threshold 0.90 \
    --update-db
```

**Creates:**
- Identifies all duplicate groups
- Performs fuzzy matching
- Detects partial overlaps
- Updates `duplicate_groups` table
- Generates `duplicate_map.json`

### Step 4: Canonicalize
```bash
python scripts/canonicalize.py \
    --source "house_oversight_nov2025" \
    --output "data/canonical" \
    --format markdown
```

**Creates:**
- Selects best version for each duplicate group
- Generates YAML frontmatter with full provenance
- Converts to markdown
- Saves to appropriate canonical directory
- Updates `canonical_documents` table

### Step 5: Verify
```bash
python scripts/verify_completeness.py \
    --report "data/metadata/quality_report.json"
```

**Outputs:**
- Missing documents report
- Quality metrics by source
- Deduplication statistics
- Coverage analysis

### Step 6: Generate Report
```bash
python scripts/quality_report.py \
    --output "data/metadata/processing_stats.json"
```

---

## Edge Case Handling

### 1. Partial Overlaps
**Scenario:** Doc A has pages 1-10, Doc B has pages 5-15

**Solution:**
- Store in `partial_overlaps` table
- Keep both as separate canonical documents
- Cross-reference in frontmatter
- Note: "This document overlaps with epstein_doc_xyz456 (pages 5-10)"

### 2. OCR Variations
**Scenario:** Same document, different OCR engines produce different text

**Solution:**
- Use fuzzy hashing (ssdeep) with 90% threshold
- Metadata matching for emails (from/to/date/subject)
- Visual hash for scanned images
- Select version with highest OCR quality score

### 3. Redaction Differences
**Scenario:** Same document released by multiple sources with different redaction levels

**Solution:**
- Prioritize least redacted version
- Track all redaction levels in `document_sources`
- Note redaction differences in selection_reason
- Cross-reference redacted versions

### 4. Format Differences
**Scenario:** Same content in PDF, TXT, DOCX formats

**Solution:**
- Normalize to text for content hashing
- Prefer searchable PDF > text > scanned PDF > images
- Store original format in `document_sources`
- Convert all to markdown for canonical version

### 5. Metadata Conflicts
**Scenario:** Different sources report different dates/subjects

**Solution:**
- Use most authoritative source (court > government > media)
- Note conflicts in frontmatter:
  ```yaml
  metadata_conflicts:
    - field: "date"
      values:
        - source: "Source A"
          value: "2008-05-15"
        - source: "Source B"
          value: "2008-05-16"
      resolution: "Used Source A (official court record)"
  ```

### 6. Missing Pages
**Scenario:** Source A has pages 1,2,4,5 (missing page 3), Source B has all pages

**Solution:**
- Mark Source A as completeness: "partial"
- Select Source B as canonical (complete)
- Track missing pages in frontmatter:
  ```yaml
  completeness_notes:
    - source: "Source A"
      missing_pages: [3]
      reason: "Page 3 withheld in original release"
  ```

---

## Quality Metrics

### OCR Quality Calculation
```python
def calculate_ocr_quality(document):
    """
    Calculate OCR quality score (0.0-1.0).

    Metrics:
    - Dictionary word match rate
    - Character corruption rate (mojibake detection)
    - Line break consistency
    - Whitespace normalization
    """
    text = extract_text(document)

    # Word dictionary matching
    words = text.split()
    valid_words = count_dictionary_words(words)
    word_score = valid_words / max(len(words), 1)

    # Character corruption detection
    corruption_rate = detect_mojibake(text)
    corruption_score = 1.0 - corruption_rate

    # Line break consistency
    line_score = assess_line_breaks(text)

    # Combined score
    quality = (word_score * 0.5 +
               corruption_score * 0.3 +
               line_score * 0.2)

    return quality
```

### Completeness Assessment
```python
def assess_completeness(document):
    """
    Determine if document is complete, partial, or fragment.
    """
    # Check for missing page indicators
    if has_missing_page_markers(document):
        return 'partial'

    # Check page numbering continuity
    page_numbers = extract_page_numbers(document)
    if not is_continuous(page_numbers):
        return 'partial'

    # Check for truncation indicators
    if is_truncated(document):
        return 'fragment'

    return 'complete'
```

---

## Configuration Files

### `source_definitions.yaml`
```yaml
sources:
  documentcloud_6506732:
    name: "DocumentCloud 6506732"
    type: "documentcloud"
    url: "https://www.documentcloud.org/documents/6506732-Epstein-Emails-Doc-Dump/"
    collection: "Florida Public Records 2019"
    authority: "government_foia"
    expected_count: 87

  house_oversight_nov2025:
    name: "House Oversight Nov 2025"
    type: "congressional"
    url: "https://oversight.house.gov/..."
    collection: "Estate Document Release"
    authority: "official_release"
    expected_count: 20000

  giuffre_maxwell:
    name: "Giuffre v. Maxwell"
    type: "court_record"
    case_number: "1:15-cv-07433-LAP"
    court: "SDNY"
    authority: "court_record"
    expected_count: 4553
```

### `canonicalization_rules.yaml`
```yaml
deduplication:
  thresholds:
    exact_match: 1.0
    fuzzy_match: 0.90
    metadata_match: 0.95
    partial_overlap: 0.30

  methods:
    - file_hash       # Exact binary match
    - content_hash    # Normalized text match
    - fuzzy_hash      # ssdeep for OCR variations
    - metadata        # from/to/date/subject for emails

  selection_priority:
    - ocr_quality: 0.40
    - redactions: 0.25
    - completeness: 0.20
    - source_authority: 0.10
    - file_quality: 0.05

quality:
  min_ocr_quality: 0.70
  max_corruption_rate: 0.05
  require_complete: false
```

---

## Success Criteria

### Functional Requirements
- ✅ Handles 100,000+ documents
- ✅ Accurately identifies duplicates (>95% precision)
- ✅ Preserves full provenance for every document
- ✅ Selects best version based on quality metrics
- ✅ Generates comprehensive source tracking
- ✅ Produces clean, searchable canonical collection

### Performance Requirements
- ✅ Process 1,000 documents in < 5 minutes
- ✅ Deduplication completes in < 30 minutes for 100,000 docs
- ✅ Database queries return results in < 1 second
- ✅ Memory usage < 4 GB for processing pipeline

### Quality Requirements
- ✅ Zero data loss (all sources preserved)
- ✅ Duplicate detection accuracy > 95%
- ✅ OCR quality scoring accuracy > 90%
- ✅ Metadata extraction accuracy > 98%

### Statistics Reporting
- ✅ Total documents processed
- ✅ Duplicate groups identified
- ✅ Deduplication rate by source
- ✅ Quality distribution (high/medium/low OCR)
- ✅ Coverage by time period
- ✅ Coverage by document type

---

## Next Steps

### Immediate Implementation
1. ✅ Create directory structure
2. ✅ Initialize SQLite database
3. ✅ Implement core hashing module
4. ✅ Implement deduplication engine
5. ✅ Create first downloader (DocumentCloud)
6. ✅ Test on existing 87-page collection

### Week 1
- Implement fuzzy matching
- Build OCR quality assessor
- Create canonicalization script
- Process 2-3 additional collections

### Month 1
- Process top 3 collections (25,000+ pages)
- Generate comprehensive quality reports
- Optimize deduplication performance
- Build web interface for browsing

---

**Document Version**: 1.0
**Last Updated**: November 16, 2025
**Status**: Ready for Implementation
