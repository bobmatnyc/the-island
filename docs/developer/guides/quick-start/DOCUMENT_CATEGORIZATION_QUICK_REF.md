# Document Categorization Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Total Documents**: 38,482
- **Unknown**: 0 (0.0%) ✅
- **Classified**: 38,482 (100%) ✅
- **Validation Issues**: 6 (0.02%) ✅

---

## Current Status

- **Total Documents**: 38,482
- **Unknown**: 0 (0.0%) ✅
- **Classified**: 38,482 (100%) ✅
- **Validation Issues**: 6 (0.02%) ✅

## Classification Categories

| Category | Count | % | Description |
|----------|-------|---|-------------|
| `government_document` | 37,492 | 97.4% | House Oversight, DOJ, FBI |
| `court_filing` | 637 | 1.7% | Legal documents, exhibits |
| `email` | 305 | 0.8% | Email correspondence |
| `media_article` | 45 | 0.1% | News/media articles |
| `administrative` | 2 | <0.1% | Misc documents |
| `contact_directory` | 1 | <0.1% | Birthday/Black book |

## Quick Commands

### Check Status
```bash
python3 -c "
import json
data = json.load(open('data/metadata/all_documents_index.json'))
stats = data.get('statistics', {})
print('Total:', data.get('total_documents'))
print('By Classification:', stats.get('by_classification'))
"
```

### Re-run Categorization
```bash
cd /Users/masa/Projects/epstein

# 1. Categorize PDFs
python3 scripts/data_quality/categorize_documents.py

# 2. Validate
python3 scripts/data_quality/validate_categorization.py

# 3. Rebuild all_documents_index
python3 scripts/data_quality/rebuild_all_documents_index.py
```

### View Sample Documents
```bash
python3 -c "
import json
data = json.load(open('data/metadata/all_documents_index.json'))
docs = data.get('documents', [])

# Show one of each classification
from collections import defaultdict
by_class = defaultdict(list)
for doc in docs:
    c = doc.get('classification')
    if len(by_class[c]) < 1:
        by_class[c].append(doc)

for classification, samples in sorted(by_class.items()):
    print(f'\n{classification}:')
    for doc in samples:
        print(f'  {doc.get(\"filename\", \"N/A\")[:50]}')
        print(f'  Confidence: {doc.get(\"classification_confidence\", 0):.2f}')
"
```

## File Locations

### Data Files
```
data/metadata/all_documents_index.json                     # Main index (use this)
data/metadata/master_document_index_categorized.json       # PDFs only
data/metadata/categorization_validation_report.json        # Validation results
```

### Scripts
```
scripts/data_quality/categorize_documents.py       # Main categorizer
scripts/data_quality/validate_categorization.py    # Validator
scripts/data_quality/rebuild_all_documents_index.py # Index rebuilder
```

### Backups
```
data/metadata/master_document_index.json.backup
data/metadata/all_documents_index.json.rebuild_backup
```

## Adding New Patterns

### Edit `categorize_documents.py`

#### Add Classification Pattern
```python
# Line ~50-100
self.patterns = {
    'your_classification': [
        r'pattern1',
        r'pattern2',
    ],
    # ... existing
}
```

#### Add Source Classification
```python
# Line ~104-117
self.source_classifications = {
    'your_source': 'classification',
    # ... existing
}
```

#### Add High-Priority Pattern
```python
# Line ~155-165
high_priority_patterns = {
    'court_filing': [r'1320[-\.]', r'exhibit', ...],
    'your_classification': [r'high_priority_pattern'],
}
```

## API Integration

### Document Object Structure
```json
{
  "id": "doc_hash_or_id",
  "type": "pdf|email",
  "source": "house_oversight_nov2025",
  "classification": "government_document",
  "classification_confidence": 0.90,
  "path": "data/sources/.../file.pdf",
  "filename": "file.pdf",
  "file_size": 12345,
  "doc_type": "pdf"
}
```

### Filter by Classification
```python
# In document service
def get_documents_by_classification(classification: str):
    return [
        doc for doc in documents
        if doc.get('classification') == classification
    ]
```

### Filter by Confidence
```python
def get_high_confidence_documents(min_confidence: float = 0.8):
    return [
        doc for doc in documents
        if doc.get('classification_confidence', 0) >= min_confidence
    ]
```

## Common Issues

### Issue: New documents not categorized
**Solution**: Run categorization pipeline:
```bash
python3 scripts/data_quality/categorize_documents.py
python3 scripts/data_quality/rebuild_all_documents_index.py
```

### Issue: Wrong classification
**Solution**: Add/update patterns in `categorize_documents.py`, then re-run

### Issue: Low confidence
**Solution**: Add source-based or high-priority pattern for better confidence

### Issue: Validation errors
**Solution**: Check `categorization_validation_report.json` for details

## Pattern Matching Examples

### Court Docket Numbers
- `1320-30.pdf` → `court_filing` (confidence: 0.95)
- Pattern: `r'1320[-\.]'`

### House Oversight Documents
- `DOJ-OGR-00011252.pdf` → `government_document` (confidence: 0.90)
- Source: `house_oversight_nov2025`

### Emails
- `*.eml` → `email` (confidence: 0.99)
- Pattern: `r'\.eml$'`

### Court Filings
- `exhibit_*.pdf` → `court_filing` (confidence: 0.95)
- Pattern: `r'exhibit'`

### Birthday/Black Book
- `birthday-book.pdf` → `contact_directory` (confidence: 0.80)
- Pattern: `r'birthday.*book'`

## Validation Rules

1. **Email files must be classified as email** (`.eml` extension)
2. **Court docket numbers must be court_filing** (`1320-*`)
3. **Giuffre/Maxwell must be court_filing** (case documents)
4. **House Oversight source must be government_document** (unless court docket)
5. **Classification confidence >0.5** (warn if lower)
6. **No unknown classifications** (zero tolerance)

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unknown % | <5% | 0% | ✅ Excellent |
| Validation Pass | >95% | 99.98% | ✅ Excellent |
| Emails Classified | 100% | 100% | ✅ Complete |
| Court Docs Found | Manual | 637 | ✅ Complete |
| Runtime | <30s | ~5s | ✅ Fast |

---

**Last Updated**: 2025-11-18
**Version**: 2.0
