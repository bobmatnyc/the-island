# Document Data Integrity Verification Suite

Comprehensive verification suite for validating document data transformations in the Epstein archive project.

## Overview

This verification suite ensures data integrity across 38,482 documents by validating:
- UUID/SHA256 format compliance
- Classification type validity against schema
- Required field presence
- Data consistency (paths, confidence scores, etc.)
- Schema compliance
- File existence

## Quick Start

```bash
# Run verification with detailed output
python3 scripts/verification/verify_documents.py --verbose

# Generate report to specific location
python3 scripts/verification/verify_documents.py --output path/to/report.md

# Check exit code for CI/CD integration
python3 scripts/verification/verify_documents.py
echo $?  # 0=pass, 1=fail, 2=critical error
```

## Files

### Verification Script
- **Path:** `scripts/verification/verify_documents.py`
- **Purpose:** Main verification suite with 6 comprehensive checks
- **Runtime:** ~5-10 seconds for 38,482 documents
- **Output:** Exit code + optional report file

### Reports
- **Detailed Report:** `docs/qa-reports/document-integrity-report.md`
  - Full verification results with all errors
  - Statistics and distributions
  - Sample violations for each issue

- **Executive Summary:** `docs/qa-reports/document-integrity-summary.md`
  - High-level findings
  - Prioritized recommendations
  - Process improvement suggestions

- **Checklist:** `docs/qa-reports/document-verification-checklist.md`
  - Quick reference for QA sign-off
  - Fix requirements
  - Success criteria

## Verification Checks

### 1. UUID Integrity
Validates that all document IDs follow SHA256 format (64 hex characters).

**Checks:**
- Valid SHA256 format: `^[a-f0-9]{64}$`
- No duplicate IDs across documents
- All IDs are unique and well-formed

**Current Status:** ✗ FAIL
- 305 email documents use DOJ control numbers instead of SHA256
- Fix required: Generate SHA256 from email metadata paths

### 2. Classification Coverage
Ensures all documents have valid classification types from schema enum.

**Valid Types:**
```
email, court_record, flight_log, fbi_report, deposition,
correspondence, financial, administrative, contact_directory,
government_document, media_article, other
```

**Current Status:** ✗ FAIL
- 278 documents use invalid 'court_filing' classification
- Fix required: Remap 'court_filing' → 'court_record'

### 3. Required Fields
Verifies presence of all required fields in current document format.

**Required Fields:**
- `id` - Document identifier (SHA256)
- `filename` - Source filename
- `path` - Relative path to source file
- `source` - Source collection identifier
- `new_classification` - Document classification type

**Current Status:** ✓ PASS
- All 38,482 documents have all required fields

### 4. Data Consistency
Validates data format consistency and value ranges.

**Checks:**
- Confidence scores: 0.0 ≤ confidence ≤ 1.0
- Path format: Relative paths starting with `data/sources/`
- Classification methods: Known values (existing, path_source, content_analysis)

**Current Status:** ✗ FAIL
- 305 email documents use absolute paths
- Fix required: Convert to relative paths

### 5. Schema Compliance
Validates document structure against canonical schema.

**Current Status:** ✓ PASS
- Documents use interim classification format
- Full compliance will be verified after canonical transformation

### 6. File Existence
Samples documents to verify source files exist at specified paths.

**Sample Size:** 100 random documents
**Current Status:** ✓ PASS
- All sampled files exist (100/100)

## Data Quality Metrics

### Classification Distribution
```
government_document:  37,469 (97.37%)
court_record:            362 (0.94%)
email:                   305 (0.79%)
court_filing (invalid):  278 (0.72%)  ← Fix required
media_article:            45 (0.12%)
fbi_report:               22 (0.06%)
contact_directory:         1 (0.00%)
```

### Confidence Distribution
```
High (≥0.8):      1,011 (2.63%)
Medium (0.5-0.8): 37,471 (97.37%)
Low (<0.5):           0 (0.00%)
```

### Classification Methods
```
existing:          37,770 (98.15%)
path_source:          707 (1.84%)
content_analysis:       5 (0.01%)
```

## Exit Codes

- **0:** All checks passed, data integrity verified
- **1:** One or more checks failed, issues found
- **2:** Critical error (file not found, invalid JSON, etc.)

## Usage Examples

### Basic Verification
```bash
python3 scripts/verification/verify_documents.py
```

### Verbose Output
```bash
python3 scripts/verification/verify_documents.py --verbose
```

### Custom Report Location
```bash
python3 scripts/verification/verify_documents.py \
  --output reports/verification-$(date +%Y%m%d).md
```

### CI/CD Integration
```bash
#!/bin/bash
# Run verification and fail pipeline on issues
python3 scripts/verification/verify_documents.py || {
  echo "Document verification failed!"
  exit 1
}
```

## Fixing Issues

See `docs/qa-reports/document-verification-checklist.md` for detailed fix requirements.

### Quick Fix Example
```python
import json
import hashlib

# Load documents
with open('data/transformed/document_classifications.json') as f:
    data = json.load(f)

# Fix email document IDs and paths
for doc in data['documents']:
    if doc['source'] == 'house_oversight_nov2025_emails':
        # Normalize path
        path = doc['path']
        if path.startswith('/Users/masa/Projects/epstein/'):
            path = path[len('/Users/masa/Projects/epstein/'):]
            doc['path'] = path

        # Generate SHA256 ID
        doc_id = hashlib.sha256(path.encode()).hexdigest()
        doc['id'] = doc_id

# Fix court filing classification
for doc in data['documents']:
    if doc.get('new_classification') == 'court_filing':
        doc['original_classification'] = 'court_filing'
        doc['new_classification'] = 'court_record'

# Save
with open('data/transformed/document_classifications.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Related Documentation

- **Schema:** `data/schemas/document_schema.json`
- **Detailed Report:** `docs/qa-reports/document-integrity-report.md`
- **Summary:** `docs/qa-reports/document-integrity-summary.md`
- **Checklist:** `docs/qa-reports/document-verification-checklist.md`
- **Linear Issue:** #29

---

**Version:** 1.0
**Last Updated:** 2025-12-06
**Status:** Active - Issues identified, fixes required
