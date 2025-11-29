#!/usr/bin/env python3
"""
Reorganize Epstein data into /raw and /md structure
Organize by source, maintain provenance
"""

import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
SOURCES_DIR = DATA_DIR / "sources"
RAW_DIR = DATA_DIR / "raw"
MD_DIR = DATA_DIR / "md"

# Define source mappings
SOURCES = {
    "entities": {
        "raw_files": [
            "raw_entities/epstein-birthday-book.pdf",
            "raw_entities/birthday_book_raw.txt",
            "raw_entities/flight_logs_raw.txt",
        ],
        "md_files": [
            "raw_entities/black_book.md",
            "raw_entities/birthday_book.md",
            "raw_entities/flight_logs.md",
            "raw_entities/little_black_book.md",
            "raw_entities/ENTITIES_INDEX.json",
            "raw_entities/flight_logs_stats.json",
            "raw_entities/EXTRACTION_SUMMARY.md",
            "raw_entities/README.md",
        ],
    },
    "house_oversight_nov2025": {
        "description": "House Oversight Nov 2025 release (67,144 PDFs)",
        # PDFs stay in sources for OCR processing
    },
    "giuffre_maxwell": {"description": "Giuffre v. Maxwell documents"},
    "documentcloud_6506732": {
        "description": "DocumentCloud 6506732 - Florida legal emails 2006-2010"
    },
    "documentcloud_6250471": {"description": "DocumentCloud 6250471 - Court documents"},
}


def create_directory_structure():
    """Create the new /raw and /md directory structure"""
    print("Creating directory structure...")

    # Create main directories
    RAW_DIR.mkdir(exist_ok=True)
    MD_DIR.mkdir(exist_ok=True)

    # Create source subdirectories
    for source in SOURCES:
        (RAW_DIR / source).mkdir(exist_ok=True)
        (MD_DIR / source).mkdir(exist_ok=True)
        print(f"  Created: raw/{source} and md/{source}")


def move_entity_files():
    """Move entity extraction files to new structure"""
    print("\nMoving entity files...")

    source_map = SOURCES["entities"]

    # Move raw files
    for raw_file in source_map["raw_files"]:
        src = SOURCES_DIR / raw_file
        if src.exists():
            dest = RAW_DIR / "entities" / src.name
            shutil.copy2(src, dest)
            print(f"  ✓ Copied {src.name} -> raw/entities/")

    # Move markdown files
    for md_file in source_map["md_files"]:
        src = SOURCES_DIR / md_file
        if src.exists():
            dest = MD_DIR / "entities" / src.name
            shutil.copy2(src, dest)
            print(f"  ✓ Copied {src.name} -> md/entities/")


def create_readme():
    """Create README explaining the new structure"""
    readme_content = """# Epstein Document Archive - Data Organization

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
"""

    readme_path = DATA_DIR / "DATA_ORGANIZATION.md"
    readme_path.write_text(readme_content)
    print(f"\n✓ Created {readme_path}")


def create_source_index():
    """Create a JSON index of all sources and their contents"""
    index = {"generated": "2025-11-16T23:30:00", "sources": {}}

    for source_name, source_info in SOURCES.items():
        raw_dir = RAW_DIR / source_name
        md_dir = MD_DIR / source_name

        raw_files = list(raw_dir.glob("*")) if raw_dir.exists() else []
        md_files = list(md_dir.glob("*")) if md_dir.exists() else []

        index["sources"][source_name] = {
            "description": source_info.get("description", ""),
            "raw_files": [f.name for f in raw_files],
            "md_files": [f.name for f in md_files],
            "raw_count": len(raw_files),
            "md_count": len(md_files),
        }

    index_path = DATA_DIR / "metadata" / "source_index.json"
    index_path.parent.mkdir(exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"✓ Created source index: {index_path}")


def main():
    """Run the reorganization"""
    print("=" * 70)
    print("EPSTEIN DATA REORGANIZATION")
    print("=" * 70)

    create_directory_structure()
    move_entity_files()
    create_readme()
    create_source_index()

    print("\n" + "=" * 70)
    print("REORGANIZATION COMPLETE")
    print("=" * 70)
    print("\nNew structure:")
    print(f"  Raw files:      {RAW_DIR}")
    print(f"  MD extractions: {MD_DIR}")
    print(f"  Documentation:  {DATA_DIR / 'DATA_ORGANIZATION.md'}")
    print(f"  Source index:   {DATA_DIR / 'metadata' / 'source_index.json'}")
    print("\nNext steps:")
    print("  1. Complete House Oversight OCR processing")
    print("  2. Move OCR extractions to md/house_oversight_nov2025/")
    print("  3. Update scripts to use new paths")
    print("  4. Run classification on all documents")


if __name__ == "__main__":
    main()
