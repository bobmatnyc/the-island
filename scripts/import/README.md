# Import Scripts Documentation

This directory contains scripts for importing external datasets into the Epstein Files project.

## Available Scripts

### `import_huggingface_documents.py`

Import OCR-extracted documents from Hugging Face dataset `tensonaut/EPSTEIN_FILES_20K`.

**Usage**:
```bash
source ../../.venv/bin/activate
python import_huggingface_documents.py
```

**Output**:
- `data/sources/house_oversight_nov2025/documents/huggingface_imported/`
- Creates JSON + TXT files for each document
- Generates document index and metadata

**Status**: ✅ Complete (25,793 documents imported)

### `import_huggingface_emails.py` (Deprecated)

Initial version that assumed email structure. Replaced by `import_huggingface_documents.py` when we discovered the dataset contains OCR text from documents, not structured emails.

## Dataset Information

**Dataset**: `tensonaut/EPSTEIN_FILES_20K`
- **Content**: OCR-extracted text from House Oversight Committee documents
- **Format**: Parquet (fields: `filename`, `text`)
- **Records**: 25,800 documents
- **Processing**: Tesseract OCR
- **License**: Research use only

## Import Results

| Metric | Value |
|--------|-------|
| Total Records | 25,800 |
| Successfully Imported | 25,793 |
| Skipped (Empty) | 7 |
| Total Characters | 103,557,290 |
| Avg Document Length | 4,014 chars |

## Quick Access

### Load Document Index
```python
import json
from pathlib import Path

index_path = Path("data/sources/house_oversight_nov2025/documents/huggingface_imported/document_index.json")
with open(index_path) as f:
    documents = json.load(f)

print(f"Total documents: {len(documents)}")
```

### Load Specific Document
```python
# JSON with metadata
doc_path = Path("data/sources/house_oversight_nov2025/documents/huggingface_imported/text/HOUSE_OVERSIGHT_020367.json")
with open(doc_path) as f:
    doc = json.load(f)

print(f"Document ID: {doc['document_id']}")
print(f"Word count: {doc['metadata']['word_count']}")
print(doc['text'][:500])  # First 500 chars
```

### Search Documents
```python
import json
from pathlib import Path

# Load index
index_path = Path("data/sources/house_oversight_nov2025/documents/huggingface_imported/document_index.json")
with open(index_path) as f:
    index = json.load(f)

# Search by filename pattern
matching = [doc for doc in index if "IMAGES-005" in doc['filename']]
print(f"Found {len(matching)} documents from IMAGES-005")

# Search by word count
large_docs = [doc for doc in index if doc['word_count'] > 1000]
print(f"Found {len(large_docs)} documents with >1000 words")
```

## Dependencies

Required Python packages:
```
datasets>=4.0.0
huggingface-hub>=0.20.0
```

Install via:
```bash
pip install datasets
```

## Output Structure

```
data/sources/house_oversight_nov2025/documents/huggingface_imported/
├── text/
│   ├── HOUSE_OVERSIGHT_010477.json
│   ├── HOUSE_OVERSIGHT_010477.txt
│   ├── HOUSE_OVERSIGHT_010478.json
│   ├── HOUSE_OVERSIGHT_010478.txt
│   └── ... (25,793 document pairs)
├── document_index.json         # Master index
├── import_metadata.json        # Import statistics
└── import_errors.log           # Error log (7 records)
```

## Document Schema

### JSON File Schema
```json
{
  "document_id": "HOUSE_OVERSIGHT_XXXXXX",
  "filename": "IMAGES-XXX-HOUSE_OVERSIGHT_XXXXXX.txt",
  "text": "Full OCR-extracted text...",
  "metadata": {
    "original_filename": "...",
    "source_dataset": "huggingface:tensonaut/EPSTEIN_FILES_20K",
    "character_count": 3875,
    "word_count": 688,
    "line_count": 54,
    "import_date": "2025-11-19T21:47:43.981264",
    "prefix": "IMAGES-005"
  }
}
```

### Index Entry Schema
```json
{
  "document_id": "HOUSE_OVERSIGHT_XXXXXX",
  "filename": "IMAGES-XXX-HOUSE_OVERSIGHT_XXXXXX.txt",
  "json_file": "text/HOUSE_OVERSIGHT_XXXXXX.json",
  "text_file": "text/HOUSE_OVERSIGHT_XXXXXX.txt",
  "character_count": 3875,
  "word_count": 688
}
```

## Troubleshooting

### Import Fails with "Module not found: datasets"
```bash
# Activate virtual environment
source ../../.venv/bin/activate

# Install datasets
pip install datasets
```

### Memory Issues During Import
The script processes documents one at a time to minimize memory usage. If you still encounter issues:
- Reduce batch size in code
- Process in chunks (modify script to process ranges)

### Missing Documents
Some source files may have duplicate HOUSE_OVERSIGHT IDs. Check `import_metadata.json` for statistics.

## Next Steps

1. **Email Extraction**: Parse OCR text to identify email headers
2. **Entity Recognition**: Extract names, dates, organizations
3. **Text Cleaning**: Correct OCR errors
4. **Indexing**: Create full-text search index
5. **Categorization**: Classify document types

## References

- **Dataset**: https://huggingface.co/datasets/tensonaut/EPSTEIN_FILES_20K
- **Import Summary**: `/Users/masa/Projects/epstein/HUGGINGFACE_IMPORT_SUMMARY.md`
- **Log File**: `import_huggingface_documents.log`
