# Data Quality Scripts

Scripts for maintaining and improving document data quality in the Epstein investigation project.

## Overview

This directory contains Python scripts for categorizing, validating, and maintaining the document index.

## Scripts

### 1. `categorize_documents.py`

**Purpose**: Categorize documents based on filename patterns and source directories.

**What it does**:
- Loads master_document_index.json
- Applies pattern-based categorization logic
- Assigns classifications with confidence scores
- Saves categorized index

**Usage**:
```bash
python3 scripts/data_quality/categorize_documents.py
```

**Output**:
- `data/metadata/master_document_index_categorized.json`
- Backup: `master_document_index.json.backup`

**Categories**:
- `government_document` - House Oversight, DOJ, FBI documents
- `court_filing` - Legal documents, exhibits, depositions
- `email` - Email correspondence
- `media_article` - News articles and reports
- `contact_directory` - Birthday/Black book
- `administrative` - Miscellaneous documents

**Confidence Levels**:
- 0.95 - High-priority pattern match (court dockets, exhibits)
- 0.90 - Source-based classification
- 0.70 - General pattern match
- 0.80 - Filename-based rules
- 0.30 - Default fallback

---

### 2. `validate_categorization.py`

**Purpose**: Validate categorization results and identify issues.

**What it does**:
- Loads categorized document index
- Applies validation rules
- Identifies misclassifications and low-confidence assignments
- Generates validation report

**Usage**:
```bash
python3 scripts/data_quality/validate_categorization.py
```

**Output**:
- `data/metadata/categorization_validation_report.json`
- Console output with statistics

**Validation Rules**:
1. Email files (`.eml`) must be classified as `email`
2. Court docket numbers (`1320-*`) must be `court_filing`
3. Giuffre/Maxwell documents must be `court_filing`
4. House Oversight documents should be `government_document`
5. Classifications must have confidence >0.5
6. No documents should remain `unknown`

**Sample Output**:
```
Total Documents: 38,177
Unknown: 0 (0.0%) ✅ EXCELLENT
Issues Found: 6 (0.02%)
```

---

### 3. `rebuild_all_documents_index.py`

**Purpose**: Combine categorized PDFs with email documents into unified index.

**What it does**:
- Loads categorized PDFs from master_document_index_categorized.json
- Extracts emails from old all_documents_index.json
- Combines into single comprehensive index
- Recalculates statistics

**Usage**:
```bash
python3 scripts/data_quality/rebuild_all_documents_index.py
```

**Output**:
- `data/metadata/all_documents_index.json` (v2.0)
- Backup: `all_documents_index.json.rebuild_backup`

**Result**:
- Unified index with 38,482 documents (38,177 PDFs + 305 emails)
- Proper classifications for all documents
- Updated statistics

---

## Workflow

### Complete Categorization Pipeline

Run all three scripts in sequence:

```bash
cd /Users/masa/Projects/epstein

# Step 1: Categorize PDFs
python3 scripts/data_quality/categorize_documents.py

# Step 2: Validate results
python3 scripts/data_quality/validate_categorization.py

# Step 3: Rebuild unified index
python3 scripts/data_quality/rebuild_all_documents_index.py
```

### Quick Status Check

```bash
python3 test_document_categories.py
```

---

## Adding New Patterns

### Add Classification Pattern

Edit `categorize_documents.py` around line 50:

```python
self.patterns = {
    'your_new_classification': [
        r'pattern1',
        r'pattern2',
    ],
    # ... existing patterns
}
```

### Add Source Classification

Edit `categorize_documents.py` around line 104:

```python
self.source_classifications = {
    'your_source_directory': 'your_classification',
    # ... existing sources
}
```

### Add High-Priority Pattern

Edit `categorize_documents.py` around line 155:

```python
high_priority_patterns = {
    'court_filing': [r'1320[-\.]', r'exhibit', ...],
    'your_classification': [r'high_priority_pattern'],
}
```

---

## File Structure

```
scripts/data_quality/
├── README.md                          # This file
├── categorize_documents.py            # Main categorization engine
├── validate_categorization.py         # Validation script
└── rebuild_all_documents_index.py     # Index rebuilding script

data/metadata/
├── master_document_index.json                    # Original PDF index
├── master_document_index_categorized.json        # Categorized PDFs
├── all_documents_index.json                      # Unified index (v2.0)
└── categorization_validation_report.json         # Validation results
```

---

## Classification Logic

### Priority Hierarchy

1. **High-Priority Patterns** (Confidence: 0.95)
   - Court docket numbers, exhibits, unsealed documents
   - Takes precedence over source-based classification

2. **Source-Based** (Confidence: 0.90)
   - Classification based on source directory
   - Example: `house_oversight_nov2025` → `government_document`

3. **General Patterns** (Confidence: 0.70)
   - Pattern matching in filename/path
   - Example: `.eml` extension → `email`

4. **Filename Rules** (Confidence: 0.80)
   - Special filename detection
   - Example: "birthday-book" → `contact_directory`

5. **Default Fallback** (Confidence: 0.30)
   - `administrative` for unmatched documents

### Example Pattern Matching

```
File: data/sources/404media/1320-30.pdf
  1. Check high-priority: "1320-" found → court_filing (0.95) ✅
  2. Skip source check (already matched)
  Result: court_filing, confidence 0.95

File: data/sources/house_oversight_nov2025/DOJ-OGR-00011252.pdf
  1. Check high-priority: No match
  2. Check source: house_oversight_nov2025 → government_document (0.90) ✅
  Result: government_document, confidence 0.90

File: metadata/email.eml
  1. Check high-priority: No match
  2. Check source: No match
  3. Check patterns: .eml extension → email (0.70) ✅
  Result: email, confidence 0.70
```

---

## Performance

- **Categorization Speed**: 7,600+ documents/second
- **Validation Speed**: 7,600+ documents/second
- **Total Runtime**: ~5 seconds for 38,482 documents
- **Memory Usage**: ~150MB peak

---

## Success Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Unknown % | <5% | 0% | ✅ Excellent |
| Validation Pass | >95% | 99.98% | ✅ Excellent |
| Emails Classified | 100% | 100% | ✅ Complete |
| Court Docs Found | - | 637 | ✅ Complete |
| Processing Time | <30s | ~5s | ✅ Fast |
| High Confidence | >80% | 99.2% | ✅ Excellent |

---

## Troubleshooting

### Issue: New documents not categorized

**Solution**: Run the complete pipeline:
```bash
python3 scripts/data_quality/categorize_documents.py
python3 scripts/data_quality/rebuild_all_documents_index.py
```

### Issue: Wrong classification

**Solution**:
1. Add/update pattern in `categorize_documents.py`
2. Re-run categorization pipeline
3. Validate results

### Issue: Low confidence scores

**Solution**:
- Add source-based classification for better confidence
- Add high-priority pattern if appropriate
- Consider if `administrative` is acceptable fallback

### Issue: Validation errors

**Solution**:
1. Check `categorization_validation_report.json` for details
2. Review validation rules in `validate_categorization.py`
3. Update patterns if needed

---

## Dependencies

```python
# Standard library only
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
import logging
from datetime import datetime
```

No external dependencies required!

---

## Related Documentation

- `DOCUMENT_CATEGORIZATION_COMPLETE.md` - Full implementation summary
- `DOCUMENT_CATEGORIZATION_QUICK_REF.md` - Quick reference guide
- `DOCUMENT_CATEGORIZATION_VISUAL_GUIDE.txt` - Visual before/after guide
- `test_document_categories.py` - Visual test script

---

### 4. `fix_biography_names_v3.py`

**Purpose**: Fix biography name format mismatch to enable entity → biography lookups.

**What it does**:
- Loads entity names from ENTITIES_INDEX.json (source of truth)
- Converts biography keys to match entity names exactly
- Uses manual mappings for special cases (nicknames, maiden names)
- Validates no data loss
- Creates backup before modification

**Usage**:
```bash
python3 scripts/data_quality/fix_biography_names_v3.py
```

**Output**:
- `data/metadata/entity_biographies.json` (updated)
- `biography_name_conversion_log_final.json` (conversion log)
- Backup: `entity_biographies.backup_TIMESTAMP.json`

**Manual Mappings**:
```python
{
    "Marcinkova, Nadia": "Nadia",               # First name only
    "Wexner, Les": "Leslie Wexner",             # Full first name
    "Giuffre, Virginia": "Roberts, Virginia",   # Maiden name
    "Richardson, Bill": "William Richardson",   # Full first name
    "Ross, Adriana": "Mucinska, Adriana"        # Different last name
}
```

**Results**:
- ✅ 18/21 biographies matched to entities (85.7%)
- ✅ 3 biography-only entries (no entity match, expected)
- ✅ 100% data integrity maintained
- ✅ Biography lookups now working

**Quick Test**:
```bash
# Run quick test
./test_bio_quick.sh

# Or full test
python3 test_biography_lookup.py
```

**Documentation**:
- `BIOGRAPHY_NAME_FIX_COMPLETE.md` - Full documentation
- `BIOGRAPHY_FIX_QUICK_REF.md` - Quick reference
- `BIOGRAPHY_FIX_VISUAL_SUMMARY.md` - Before/after visual guide

---

## File Structure (Updated)

```
scripts/data_quality/
├── README.md                             # This file
├── categorize_documents.py               # Document categorization
├── validate_categorization.py            # Categorization validation
├── rebuild_all_documents_index.py        # Index rebuilding
├── fix_biography_names_v3.py             # Biography name fixer ✨ NEW
├── generate_entity_mappings.py           # Entity mapping generator
├── normalize_entity_names.py             # Entity name normalizer
├── normalize_raw_flight_logs.py          # Flight log normalizer
└── verify_normalization.py               # Normalization verification

data/metadata/
├── master_document_index.json                    # Original PDF index
├── master_document_index_categorized.json        # Categorized PDFs
├── all_documents_index.json                      # Unified index (v2.0)
├── categorization_validation_report.json         # Validation results
├── entity_biographies.json                       # Entity biographies ✨ FIXED
└── biography_name_conversion_log_final.json      # Biography conversion log ✨ NEW
```

---

**Last Updated**: 2025-11-18
**Version**: 1.1
**Status**: Production Ready ✅
