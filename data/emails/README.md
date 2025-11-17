# Epstein Emails - DocumentCloud Extract

This directory contains the complete extraction of the Epstein Emails document from DocumentCloud (Document ID: 6506732).

## Quick Start

- **Full PDF**: `epstein-emails-complete.pdf` (87 pages, 6.4 MB)
- **Structured Data**: `epstein-emails-structured.json` (73 pages, machine-readable)
- **Individual Pages**: `pages/page-001.txt` through `pages/page-087.txt` (87 text files)
- **Document Notes**: `notes/notes-summary.md` (3 annotations)

## What's Included

### Primary Documents
1. **Complete PDF** - Full 87-page document as originally published
2. **Structured JSON** - 73 pages of text content with metadata
3. **Individual Text Files** - OCR-extracted text for each of the 87 pages

### Annotations
- **Raw JSON** - API response with all note metadata
- **Formatted Summary** - Human-readable version with:
  - "Goldberger calling Krischer" (Page 70)
  - "Villafana on DNP" (Page 68)
  - "Fortunate to get the 'deal of the century'" (Page 2)

## Usage Examples

### Search Across All Pages
```bash
# Find mentions of a specific name
grep -i "goldberger" pages/*.txt

# Case-insensitive search with line numbers
grep -in "community control" pages/*.txt

# Count occurrences
grep -c "epstein" pages/*.txt | grep -v ":0"
```

### Working with Structured JSON
```python
import json

with open('epstein-emails-structured.json', 'r') as f:
    data = json.load(f)

# Access page content
for page in data['pages']:
    print(f"Page {page['page']}: {page['text'][:100]}...")
```

### Analyze Notes
```python
import json

with open('notes/epstein-emails-notes.json', 'r') as f:
    notes = json.load(f)

for note in notes['results']:
    print(f"Page {note['page_number']}: {note['title']}")
```

## Data Sources

- **DocumentCloud**: https://www.documentcloud.org/documents/6506732
- **S3 Bucket**: https://s3.documentcloud.org/documents/6506732/
- **API**: https://api.www.documentcloud.org/api/documents/6506732/

## Extraction Details

- **Date**: 2025-11-16
- **Total Files**: 92
- **Total Size**: 6.8 MB
- **Success Rate**: 100%
- **Method**: Python script using DocumentCloud API and S3

See `MANIFEST.md` for complete documentation of all files and sources.

## Important Notes

1. **Page Count Discrepancy**: The structured JSON contains 73 pages, while the PDF has 87 pages. Individual text files cover all 87 pages.

2. **Page Numbering**: All page files use zero-padded 3-digit numbers (page-001.txt, not page-1.txt).

3. **Text Quality**: OCR quality varies by page. Some pages may contain scanning artifacts or errors.

4. **Public Access**: All notes are marked as "public" access level.

## Re-running the Extraction

To re-extract the data or update:

```bash
python3 scripts/extract_emails.py
```

The script will:
- Download all files fresh
- Apply rate limiting (0.1s between requests)
- Create updated manifest
- Report any errors or missing data

## File Sizes

- PDF: 6.4 MB
- Structured JSON: 115 KB
- Individual pages: 348 KB total
- Notes: 8 KB

---

*Extracted using `scripts/extract_emails.py`*
*Last updated: 2025-11-16*
