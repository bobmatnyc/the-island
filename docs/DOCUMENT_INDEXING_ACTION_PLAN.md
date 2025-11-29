# Document Indexing Action Plan

**Generated**: 2025-11-26
**Status**: Investigation Complete - Ready for Implementation

## Executive Summary

Out of 38,177 total documents, 4,848 (12.7%) are not searchable through the web interface. Investigation reveals a two-tier problem:

1. **Missing OCR Processing**: 708 documents from non-house_oversight sources lack text extraction
2. **Missing Vector Embeddings**: 4,140 house_oversight documents have OCR text but aren't indexed in ChromaDB

## Root Cause Analysis

### Issue 1: Hardcoded Scripts
Both OCR and indexing scripts are hardcoded to process only `house_oversight_nov2025`:

**OCR Script** (`scripts/extraction/ocr_house_oversight.py`):
```python
# Lines 37-38 - Hardcoded paths
SOURCE_DIR = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/epstein-pdf")
OUTPUT_DIR = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_text")
```

**Vector Store Script** (`scripts/rag/build_vector_store.py`):
```python
# Line 35 - Hardcoded path
OCR_TEXT_DIR = PROJECT_ROOT / "data/sources/house_oversight_nov2025/ocr_text"
```

### Issue 2: Missing OCR Text for Other Sources

Source directories structure comparison:

**house_oversight_nov2025** (✅ Complete):
```
house_oversight_nov2025/
├── epstein-pdf/        # 37,469 PDF files
└── ocr_text/          # 33,329 text files (4,140 missing)
```

**courtlistener_giuffre_maxwell** (❌ No OCR):
```
courtlistener_giuffre_maxwell/
├── giuffre_maxwell_1.0.pdf
├── giuffre_maxwell_2.0.pdf
...
└── giuffre_maxwell_358.0.pdf
```
- 358 PDF files, **0 text files**

**404media** (❌ No OCR):
```
404media/
├── 1.4.23 Epstein Docs/
├── Epstein Docs 1.5.24/
└── Epstein docs 2/
```
- 319 documents, **0 text files**

**fbi_vault** (❌ No OCR):
```
fbi_vault/
├── jeffrey_epstein_part_01.pdf
├── jeffrey_epstein_part_02.pdf
...
└── jeffrey_epstein_part_21.pdf
```
- 21 PDF files, **0 text files**

## Implementation Strategy

### Phase 1: Index Missing house_oversight Documents (Priority 1)

**Goal**: Index 4,140 documents that have OCR text but aren't in ChromaDB

**Status**: ✅ **READY TO EXECUTE** - Text files exist, script exists, no modifications needed

**Steps**:
1. Investigate why 4,140 documents were skipped during initial indexing
2. Check if text files exist for these doc_ids
3. Run `build_vector_store.py` with resume=True to process remaining documents

**Expected Duration**: ~10-15 minutes
**Impact**: 11% more house_oversight documents become searchable

**Command**:
```bash
cd /Users/masa/Projects/epstein/scripts/rag
python3 build_vector_store.py --batch-size 100
```

**Verification**:
```bash
# Check if all 37,469 documents are now indexed
python3 -c "
import chromadb
from pathlib import Path

client = chromadb.PersistentClient(path=str(Path('../../data/vector_store/chroma')))
collection = client.get_collection(name='epstein_documents')
results = collection.get(where={'source': 'house_oversight_nov2025'})
print(f'Indexed: {len(results[\"ids\"])} / 37,469')
"
```

### Phase 2: OCR Processing for Other Sources (Priority 2)

**Goal**: Extract text from 708 documents across 8 other sources

**Status**: ⚠️ **REQUIRES SCRIPT MODIFICATION** - Script is hardcoded to house_oversight

**Option A: Modify Existing Script (Recommended)**

Create parameterized version of `ocr_house_oversight.py`:

```python
#!/usr/bin/env python3
"""
Generic OCR Processing Script
Processes PDFs from any source directory
"""

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="OCR processing for document sources")
    parser.add_argument("--source", required=True, help="Source directory name")
    parser.add_argument("--pdf-dir", help="PDF subdirectory name (default: auto-detect)")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    return parser.parse_args()

# Replace hardcoded paths with:
args = parse_args()
SOURCE_BASE = Path("/Users/masa/Projects/Epstein/data/sources")
SOURCE_DIR = SOURCE_BASE / args.source
PDF_DIR = SOURCE_DIR / (args.pdf_dir or detect_pdf_directory())
OUTPUT_DIR = SOURCE_DIR / "ocr_text"
PROGRESS_FILE = SOURCE_DIR / "ocr_progress.json"
```

**Option B: Create Wrapper Script (Faster)**

Create `scripts/extraction/ocr_all_sources.sh`:
```bash
#!/bin/bash
# OCR processing for all sources

SOURCES=(
  "courtlistener_giuffre_maxwell"
  "404media"
  "fbi_vault"
)

for source in "${SOURCES[@]}"; do
  echo "Processing $source..."
  python3 ocr_house_oversight.py --source "$source"
done
```

**Expected Duration**:
- courtlistener: ~2-3 hours (358 PDFs)
- 404media: ~2-3 hours (319 documents)
- fbi_vault: ~30 minutes (21 PDFs)
- **Total**: ~5-7 hours

**Impact**: 708 documents ready for vector embedding

### Phase 3: Vector Embedding for New Sources (Priority 3)

**Goal**: Index newly OCR'd documents into ChromaDB

**Status**: ⚠️ **REQUIRES SCRIPT MODIFICATION** - Script is hardcoded to house_oversight

**Modify `build_vector_store.py`**:

```python
def build_vector_store(source_name: str = "house_oversight_nov2025"):
    """Build vector store for specified source."""

    # Make paths dynamic
    ocr_text_dir = PROJECT_ROOT / f"data/sources/{source_name}/ocr_text"

    # Update metadata to include actual source
    metadata = {
        "filename": file_path.name,
        "doc_id": doc_id,
        "source": source_name,  # Use actual source name
        "file_size": len(text),
        "date_extracted": date if date else "",
        "entity_mentions": ", ".join(entities) if entities else "",
    }
```

**Commands**:
```bash
# After OCR completes for each source
python3 build_vector_store.py --source courtlistener_giuffre_maxwell
python3 build_vector_store.py --source 404media
python3 build_vector_store.py --source fbi_vault
```

**Expected Duration**: ~10-15 minutes per source
**Impact**: All 4,848 missing documents become searchable

## Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Index missing house_oversight | 10-15 min | None - READY NOW |
| 2 | Modify OCR script | 30 min | None |
| 2 | OCR courtlistener | 2-3 hours | Modified script |
| 2 | OCR 404media | 2-3 hours | Modified script |
| 2 | OCR fbi_vault | 30 min | Modified script |
| 3 | Modify vector store script | 30 min | None |
| 3 | Index courtlistener | 10 min | Phase 2 complete |
| 3 | Index 404media | 10 min | Phase 2 complete |
| 3 | Index fbi_vault | 5 min | Phase 2 complete |

**Total Estimated Time**: 8-10 hours (mostly OCR processing)

## Immediate Next Steps

### Step 1: Index Missing house_oversight Documents (DO THIS FIRST)

This can be done immediately without any modifications:

```bash
cd /Users/masa/Projects/epstein/scripts/rag
python3 build_vector_store.py --batch-size 100
```

Expected result: 4,140 additional documents become searchable

### Step 2: Investigate Missing Documents

Before proceeding with other sources, understand why 4,140 documents were skipped:

```bash
# Check if OCR text files exist for missing doc_ids
cd /Users/masa/Projects/epstein
python3 -c "
import json
from pathlib import Path

# Load viewability report
with open('data/metadata/documents_not_viewable_report.json') as f:
    report = json.load(f)

# Get missing house_oversight docs
missing = [d for d in report['not_viewable_documents']
           if d['source'] == 'house_oversight_nov2025'][:10]

# Check if OCR files exist
ocr_dir = Path('data/sources/house_oversight_nov2025/ocr_text')
for doc in missing:
    doc_id = doc['doc_id']
    txt_file = ocr_dir / f'{doc_id}.txt'
    exists = 'EXISTS' if txt_file.exists() else 'MISSING'
    print(f'{doc_id}: OCR file {exists}')
"
```

### Step 3: Create Modified Scripts

See Phase 2 and Phase 3 above for script modifications needed.

## Expected Outcomes

After completing all phases:

- **Total Documents Indexed**: 38,177 (100%)
- **ChromaDB Coverage**: 100% (up from 87.3%)
- **Search Coverage**: All document sources fully searchable
- **User Impact**: Complete document collection accessible through web interface

## Files Referenced

- `/Users/masa/Projects/epstein/scripts/rag/build_vector_store.py`
- `/Users/masa/Projects/epstein/scripts/extraction/ocr_house_oversight.py`
- `/Users/masa/Projects/epstein/data/sources/*/ocr_text/`
- `/Users/masa/Projects/epstein/data/vector_store/chroma/`
- `/Users/masa/Projects/epstein/data/metadata/documents_not_viewable_report.json`

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OCR takes longer than estimated | Delayed completion | Run overnight, use parallel processing |
| Some PDFs fail OCR | Incomplete coverage | Error handling, retry logic exists |
| ChromaDB storage fills up | Indexing fails | Monitor disk space (~2GB needed) |
| Different PDF structures | OCR quality issues | Test with sample first |

## Success Criteria

- [ ] All 37,469 house_oversight documents indexed (currently 33,329)
- [ ] OCR text files created for courtlistener (358 docs)
- [ ] OCR text files created for 404media (319 docs)
- [ ] OCR text files created for fbi_vault (21 docs)
- [ ] All 38,177 documents searchable in web interface
- [ ] Viewability analysis shows 100% coverage

---

*This plan was created based on investigation of the indexing pipeline on 2025-11-26. See `docs/DOCUMENT_VIEWABILITY_ANALYSIS.md` for the original analysis.*
