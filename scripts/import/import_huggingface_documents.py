#!/usr/bin/env python3
"""
Import Epstein documents from Hugging Face dataset.

Dataset: tensonaut/EPSTEIN_FILES_20K
URL: https://huggingface.co/datasets/tensonaut/EPSTEIN_FILES_20K

This dataset contains OCR-extracted text from House Oversight Committee documents,
NOT structured emails. This script imports them as document text files.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from datasets import load_dataset


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("import_huggingface_documents.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "sources"
    / "house_oversight_nov2025"
    / "documents"
    / "huggingface_imported"
)
DOCS_DIR = OUTPUT_DIR / "text"
ERROR_LOG = OUTPUT_DIR / "import_errors.log"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


class DocumentImporter:
    """Import and convert Hugging Face document dataset to project format."""

    def __init__(self):
        """Initialize importer with statistics tracking."""
        self.stats = {
            "total_records": 0,
            "successful_imports": 0,
            "parsing_errors": 0,
            "skipped_records": 0,
            "total_characters": 0,
            "avg_document_length": 0,
            "documents_by_prefix": {},
        }
        self.document_index = []
        self.error_log = []

    def extract_document_id(self, filename: str) -> str:
        """Extract document ID from filename.

        Args:
            filename: Original filename from dataset

        Returns:
            Cleaned document ID
        """
        # Extract ID from filename like "IMAGES-005-HOUSE_OVERSIGHT_020367.txt"
        match = re.search(r"HOUSE_OVERSIGHT_(\d+)", filename)
        if match:
            return f"HOUSE_OVERSIGHT_{match.group(1)}"

        # Fallback: use filename without extension
        return Path(filename).stem

    def extract_metadata(self, filename: str, text: str) -> dict[str, Any]:
        """Extract metadata from filename and text content.

        Args:
            filename: Original filename
            text: Document text content

        Returns:
            Metadata dictionary
        """
        metadata = {
            "original_filename": filename,
            "source_dataset": "huggingface:tensonaut/EPSTEIN_FILES_20K",
            "character_count": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split("\n")),
            "import_date": datetime.now().isoformat(),
        }

        # Extract prefix for categorization (e.g., "IMAGES-005")
        match = re.match(r"^([A-Z]+-\d+)-", filename)
        if match:
            metadata["prefix"] = match.group(1)

        return metadata

    def convert_record(self, record: dict[str, Any], index: int) -> dict[str, Any] | None:
        """Convert Hugging Face record to project document format.

        Args:
            record: Raw record from dataset
            index: Record index for tracking

        Returns:
            Converted document dict or None if conversion fails
        """
        try:
            filename = record.get("filename", f"document_{index}")
            text = record.get("text", "").strip()

            # Skip empty documents
            if not text:
                return None

            # Extract document ID
            doc_id = self.extract_document_id(filename)

            # Extract metadata
            metadata = self.extract_metadata(filename, text)

            # Track statistics
            self.stats["total_characters"] += metadata["character_count"]
            prefix = metadata.get("prefix", "unknown")
            self.stats["documents_by_prefix"][prefix] = (
                self.stats["documents_by_prefix"].get(prefix, 0) + 1
            )

            # Build document object
            document = {
                "document_id": doc_id,
                "filename": filename,
                "text": text,
                "metadata": metadata,
            }

            return document

        except Exception as e:
            error_msg = f"Error converting record {index}: {e!s}"
            logger.error(error_msg)
            self.error_log.append(
                {
                    "index": index,
                    "error": str(e),
                    "filename": record.get("filename", "unknown"),
                }
            )
            return None

    def save_document(self, document: dict[str, Any]) -> bool:
        """Save individual document to JSON and text file.

        Args:
            document: Document dict to save

        Returns:
            True if saved successfully
        """
        try:
            doc_id = document["document_id"]
            # Sanitize filename
            safe_id = re.sub(r"[^\w\-]", "_", doc_id)

            # Save JSON metadata
            json_path = DOCS_DIR / f"{safe_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(document, f, indent=2, ensure_ascii=False)

            # Save plain text for easy reading
            txt_path = DOCS_DIR / f"{safe_id}.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(document["text"])

            # Add to index
            self.document_index.append(
                {
                    "document_id": doc_id,
                    "filename": document["filename"],
                    "json_file": f"text/{safe_id}.json",
                    "text_file": f"text/{safe_id}.txt",
                    "character_count": document["metadata"]["character_count"],
                    "word_count": document["metadata"]["word_count"],
                }
            )

            return True

        except Exception as e:
            logger.error(f"Error saving document {document.get('document_id')}: {e}")
            return False

    def save_metadata(self) -> None:
        """Save import metadata and index files."""
        # Calculate average document length
        if self.stats["successful_imports"] > 0:
            self.stats["avg_document_length"] = (
                self.stats["total_characters"] // self.stats["successful_imports"]
            )

        metadata = {
            "import_date": datetime.now().isoformat(),
            "source_dataset": "huggingface:tensonaut/EPSTEIN_FILES_20K",
            "description": "OCR-extracted text from House Oversight Committee documents",
            "statistics": {
                "total_records": self.stats["total_records"],
                "successful_imports": self.stats["successful_imports"],
                "parsing_errors": self.stats["parsing_errors"],
                "skipped_records": self.stats["skipped_records"],
                "total_characters": self.stats["total_characters"],
                "avg_document_length": self.stats["avg_document_length"],
                "documents_by_prefix": self.stats["documents_by_prefix"],
            },
        }

        # Save metadata
        metadata_path = OUTPUT_DIR / "import_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved metadata to {metadata_path}")

        # Save document index
        index_path = OUTPUT_DIR / "document_index.json"
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self.document_index, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved document index to {index_path}")

        # Save error log if there are errors
        if self.error_log:
            with open(ERROR_LOG, "w", encoding="utf-8") as f:
                json.dump(self.error_log, f, indent=2, ensure_ascii=False)
            logger.warning(f"Saved {len(self.error_log)} errors to {ERROR_LOG}")

    def run(self) -> None:
        """Execute the import process."""
        logger.info("Starting Hugging Face document dataset import...")
        logger.info(f"Output directory: {OUTPUT_DIR}")

        # Load dataset
        logger.info("Loading dataset from Hugging Face...")
        try:
            dataset = load_dataset("tensonaut/EPSTEIN_FILES_20K", split="train")
            logger.info(f"Loaded {len(dataset)} records from dataset")
        except Exception as e:
            logger.error(f"Failed to load dataset: {e}")
            raise

        # Process records
        self.stats["total_records"] = len(dataset)
        logger.info(f"Processing {self.stats['total_records']} records...")

        for idx, record in enumerate(dataset):
            if idx % 1000 == 0:
                logger.info(f"Processing record {idx}/{self.stats['total_records']}...")

            # Convert record
            document = self.convert_record(record, idx)
            if document is None:
                self.stats["skipped_records"] += 1
                continue

            # Save document
            if self.save_document(document):
                self.stats["successful_imports"] += 1
            else:
                self.stats["parsing_errors"] += 1

        # Save metadata and index
        self.save_metadata()

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print import summary to console."""
        print("\n" + "=" * 60)
        print("DOCUMENT IMPORT SUMMARY")
        print("=" * 60)
        print(f"Total records processed: {self.stats['total_records']}")
        print(f"Successfully imported: {self.stats['successful_imports']}")
        print(f"Parsing errors: {self.stats['parsing_errors']}")
        print(f"Skipped (empty): {self.stats['skipped_records']}")
        print(f"\nTotal characters: {self.stats['total_characters']:,}")
        print(f"Average document length: {self.stats['avg_document_length']:,} characters")
        print("\nDocuments by prefix:")
        for prefix, count in sorted(self.stats["documents_by_prefix"].items()):
            print(f"  {prefix}: {count}")
        print(f"\nOutput directory: {OUTPUT_DIR}")
        print(f"Document files: {DOCS_DIR}")
        print(f"Index file: {OUTPUT_DIR / 'document_index.json'}")
        print(f"Metadata file: {OUTPUT_DIR / 'import_metadata.json'}")
        if self.error_log:
            print(f"Error log: {ERROR_LOG}")
        print("=" * 60 + "\n")


def main():
    """Main entry point."""
    importer = DocumentImporter()
    importer.run()


if __name__ == "__main__":
    main()
