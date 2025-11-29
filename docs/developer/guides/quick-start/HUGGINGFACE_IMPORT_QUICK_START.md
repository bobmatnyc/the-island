# Hugging Face Import - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Dataset**: `tensonaut/EPSTEIN_FILES_20K`
- **Records Imported**: 25,793 / 25,800 (99.97%)
- **Total Text**: 103.5 million characters
- **Average Document**: 4,014 characters / 624 words

---

## 📊 Import Summary

**Status**: ✅ **COMPLETE**

- **Dataset**: `tensonaut/EPSTEIN_FILES_20K`
- **Records Imported**: 25,793 / 25,800 (99.97%)
- **Total Text**: 103.5 million characters
- **Average Document**: 4,014 characters / 624 words

## 🗂️ What Was Imported

This dataset contains **OCR-extracted text from House Oversight Committee documents** related to the Epstein investigation. These are **NOT structured emails** - they are scanned documents processed through Tesseract OCR.

### Content Breakdown

| Category | Count | Description |
|----------|-------|-------------|
| IMAGES-* | 21,796 | Image-based OCR extractions |
| TEXT-* | 2,897 | Text-based extractions |
| **Total** | **25,793** | All documents |

## 📁 File Location

```
data/sources/house_oversight_nov2025/documents/huggingface_imported/
├── text/
│   ├── HOUSE_OVERSIGHT_020367.json  # JSON with metadata
│   ├── HOUSE_OVERSIGHT_020367.txt   # Plain text
│   └── ... (25,793 document pairs)
├── document_index.json              # Master index
├── import_metadata.json             # Import statistics
└── import_errors.log                # 7 error records
```

## 🚀 Quick Access Examples

### Load a Single Document

```python
import json
from pathlib import Path

# Load JSON with metadata
doc_path = Path("data/sources/house_oversight_nov2025/documents/huggingface_imported/text/HOUSE_OVERSIGHT_020367.json")
with open(doc_path) as f:
    doc = json.load(f)

print(f"Document: {doc['document_id']}")
print(f"Words: {doc['metadata']['word_count']}")
print(f"Text preview: {doc['text'][:200]}...")
```

### Search All Documents

```python
import json
from pathlib import Path

# Load index
index_path = Path("data/sources/house_oversight_nov2025/documents/huggingface_imported/document_index.json")
with open(index_path) as f:
    documents = json.load(f)

# Find large documents
large_docs = [d for d in documents if d['word_count'] > 1000]
print(f"Found {len(large_docs)} documents with >1,000 words")

# Find by filename pattern
images_005 = [d for d in documents if "IMAGES-005" in d['filename']]
print(f"Found {len(images_005)} documents from IMAGES-005 batch")
```

### Run Verification Test

```bash
source .venv/bin/activate
python scripts/import/test_import.py
```

## 📝 Sample Document

**Document ID**: HOUSE_OVERSIGHT_020367
**Source File**: IMAGES-005-HOUSE_OVERSIGHT_020367.txt
**Length**: 688 words / 3,875 characters

**Preview**:
```
The final choice he was made to board a non-stop flight to Moscow
on June 23, 2013. To remain in Hong Kong once a criminal complaint
was leveled against him would have meant that, at the very minimum,
Hong Kong authorities would seize him and the alleged stolen property
of the US government in his possession...
```

## 📈 Document Statistics

| Metric | Value |
|--------|-------|
| **Smallest Document** | 1 word |
| **Largest Document** | 280,884 words |
| **Average Document** | 624 words |
| **Documents > 1,000 words** | 1,100 |

## 🔧 Scripts Available

### Import Script
```bash
source .venv/bin/activate
python scripts/import/import_huggingface_documents.py
```

### Test Script
```bash
source .venv/bin/activate
python scripts/import/test_import.py
```

## 📖 Documentation

- **Full Summary**: `/Users/masa/Projects/epstein/HUGGINGFACE_IMPORT_SUMMARY.md`
- **Script README**: `/Users/masa/Projects/epstein/scripts/import/README.md`
- **Import Log**: `import_huggingface_documents.log`

## ⚠️ Important Notes

1. **OCR Quality**: Text may contain OCR errors, formatting issues, or artifacts
2. **Not Emails**: These are document extractions, not structured email data
3. **Duplicate IDs**: Some source files map to same HOUSE_OVERSIGHT_* ID (~22,927 unique files vs. 25,793 index entries)
4. **Research Use**: Dataset license restricts to research use only

## 🎯 Next Steps

### For Analysis
1. **Text Search**: Use grep or full-text search on .txt files
2. **Entity Extraction**: Run NER to find people, organizations, dates
3. **Topic Modeling**: Cluster documents by content
4. **Timeline Creation**: Extract dates and events

### For Email Extraction
1. Parse OCR text for email headers (From:, To:, Subject:, Date:)
2. Use regex to extract structured email data
3. Validate extracted emails against known formats

### For Data Quality
1. **OCR Correction**: Fix common OCR errors (l→I, 0→O, etc.)
2. **Text Normalization**: Clean formatting and whitespace
3. **Deduplication**: Identify and merge duplicate documents

## 📞 Support

- **Import Issues**: Check `import_errors.log` for error details
- **Missing Data**: Verify 7 records were skipped (empty text fields)
- **Memory Issues**: Process documents in batches if needed

---

**✅ Import Complete**: 25,793 documents ready for analysis

**📁 Location**: `data/sources/house_oversight_nov2025/documents/huggingface_imported/`

**🔍 Verify**: Run `python scripts/import/test_import.py`
