# Epstein Document Archive - Data Organization

## Directory Structure

```
data/
├── raw/              # Raw source files (PDFs, CSVs, original downloads)
│   ├── entities/    # Contact books, flight logs, birthday book
│   ├── house_oversight_nov2025/
│   ├── giuffre_maxwell/
│   ├── documentcloud_6506732/
│   └── documentcloud_6250471/
│
├── md/               # Markdown extractions (structured data from raw files)
│   ├── entities/    # Entity extractions (black_book.md, flight_logs.md, etc.)
│   ├── house_oversight_nov2025/  # OCR-extracted text from PDFs
│   ├── giuffre_maxwell/          # Extracted text and metadata
│   ├── documentcloud_6506732/
│   └── documentcloud_6250471/
│
├── canonical/        # Deduplicated, canonicalized documents
│   ├── emails/
│   ├── court_filings/
│   ├── financial/
│   ├── investigative/
│   └── ...
│
├── metadata/         # Databases, indexes, processing logs
│   └── deduplication.db
│
└── sources/          # Original download directories (legacy, being phased out)
```

## Principles

1. **Raw files in /raw**: All original downloads (PDFs, CSVs, ZIPs) go in /raw/{source}/
2. **Extractions in /md**: All markdown extractions, OCR text, structured data go in /md/{source}/
3. **Organized by source**: Each source collection has matching directories in both /raw and /md
4. **Provenance tracking**: All .md files have YAML frontmatter with source information
5. **Canonical in /canonical**: Final deduplicated versions organized by document type

## Current Sources

### Entities (Contact Books & Flight Logs)
- **Raw**: Birthday book PDF, flight logs PDF, raw text extractions
- **MD**: black_book.md, birthday_book.md, flight_logs.md, ENTITIES_INDEX.json
- **Status**: Complete - 1,773 unique entities indexed

### House Oversight Nov 2025
- **Raw**: 67,144 PDFs (13GB download)
- **MD**: OCR text extraction in progress (expected: 2,322 emails + 64,822 other docs)
- **Status**: OCR processing (ETA: 22:15 EST)

### Giuffre v. Maxwell
- **Raw**: 43 PDFs from litigation
- **MD**: Extracted 5 emails, metadata
- **Status**: Complete

### DocumentCloud Collections
- **6506732**: Florida legal emails 2006-2010 (87 pages, 3 emails)
- **6250471**: Court documents (2,024 pages, 0 emails)
- **Status**: Complete

## Migration Status

- [x] Created /raw and /md directory structure
- [x] Moved entity files to new structure
- [ ] Move House Oversight extractions (awaiting OCR completion)
- [ ] Move DocumentCloud extractions
- [ ] Update all scripts to use new paths
- [ ] Phase out /sources directory (keep for OCR processing)
