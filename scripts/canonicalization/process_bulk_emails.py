#!/usr/bin/env python3
"""
Bulk Email Processing Pipeline

Processes large collections of emails through deduplication pipeline.

Usage:
    python scripts/process_bulk_emails.py <input_directory> [options]

    Options:
        --source-name <name>       Source collection name (default: bulk_import)
        --collection <name>        Collection identifier (default: house_oversight)
        --format <pdf|markdown>    Input format (default: pdf)
        --batch-size <n>          Batch size for commits (default: 100)
        --skip-duplicates         Skip duplicate detection (faster)
        --report <file>           Save processing report to file

Pipeline:
    Input Directory → Extract Text → Calculate Hashes → Check Duplicates →
    Store Canonical → Track Sources → Generate Report
"""

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import CanonicalDatabase
from core.deduplicator import Deduplicator
from core.hasher import DocumentHasher, generate_canonical_id


@dataclass
class ProcessingStats:
    """Track processing statistics."""
    total_files: int = 0
    processed: int = 0
    duplicates: int = 0
    errors: int = 0
    skipped: int = 0
    start_time: float = 0
    end_time: float = 0

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time == 0:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def emails_per_second(self) -> float:
        """Calculate processing speed."""
        if self.elapsed == 0:
            return 0
        return self.processed / self.elapsed

    @property
    def duplicate_rate(self) -> float:
        """Calculate duplicate rate."""
        total = self.processed + self.duplicates
        if total == 0:
            return 0
        return self.duplicates / total


class EmailProcessor:
    """
    Bulk email processing pipeline.

    Design Decision: Batch Processing with Commits
    Rationale: Process documents in batches to balance performance and safety.
    - Small batches (100): Frequent commits, less data loss on crash
    - Large batches (1000+): Faster processing, more risk
    - Current default (100): Good balance for 20,000+ emails

    Performance:
    - Expected: 100-500 emails/second depending on file size
    - Bottleneck: Hash calculation for large PDFs
    - Optimization: Parallel processing (future enhancement)
    """

    def __init__(
        self,
        db: CanonicalDatabase,
        source_name: str,
        collection: str,
        batch_size: int = 100,
        skip_duplicates: bool = False
    ):
        """
        Initialize processor.

        Args:
            db: Database instance
            source_name: Name of data source
            collection: Collection identifier
            batch_size: Number of emails per batch
            skip_duplicates: Skip duplicate detection (faster)
        """
        self.db = db
        self.source_name = source_name
        self.collection = collection
        self.batch_size = batch_size
        self.skip_duplicates = skip_duplicates

        self.hasher = DocumentHasher()
        self.dedup = Deduplicator() if not skip_duplicates else None

        self.stats = ProcessingStats()

    def process_directory(self, input_dir: Path, file_format: str = "markdown"):
        """
        Process all files in directory.

        Args:
            input_dir: Input directory path
            file_format: File format (pdf, markdown)
        """
        print("\n=== Bulk Email Processing ===")
        print(f"Input directory: {input_dir}")
        print(f"Source: {self.source_name}")
        print(f"Collection: {self.collection}")
        print(f"Format: {file_format}")
        print(f"Batch size: {self.batch_size}")

        # Find all files
        if file_format == "markdown":
            files = sorted(input_dir.glob("**/*.md"))
        elif file_format == "pdf":
            files = sorted(input_dir.glob("**/*.pdf"))
        else:
            print(f"Error: Unsupported format '{file_format}'")
            return

        self.stats.total_files = len(files)
        self.stats.start_time = time.time()

        print(f"Found {self.stats.total_files} files")

        if self.stats.total_files == 0:
            print("No files to process")
            return

        # Process in batches
        batch = []

        for i, file_path in enumerate(files, 1):
            batch.append(file_path)

            # Process batch when full
            if len(batch) >= self.batch_size:
                self._process_batch(batch)
                batch = []
                self._print_progress(i)

        # Process remaining files
        if batch:
            self._process_batch(batch)

        self.stats.end_time = time.time()

        print()  # Newline after progress
        self._print_summary()

    def _process_batch(self, files: List[Path]):
        """
        Process batch of files.

        Args:
            files: List of file paths
        """
        for file_path in files:
            try:
                self._process_file(file_path)
            except Exception as e:
                self._handle_error(file_path, e)

    def _process_file(self, file_path: Path):
        """
        Process single file through pipeline.

        Pipeline:
        1. Read file
        2. Extract text and metadata
        3. Calculate hashes
        4. Check for duplicates
        5. Insert or update database

        Args:
            file_path: Path to file
        """
        # Read file
        if file_path.suffix == ".md":
            text = file_path.read_text(encoding="utf-8")
            metadata = self._extract_markdown_metadata(text)
        elif file_path.suffix == ".pdf":
            # TODO: Implement PDF extraction
            raise NotImplementedError("PDF extraction not yet implemented")
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Calculate hashes
        file_hash = self.hasher.hash_file(file_path)
        content_hash = self.hasher.hash_content(text)
        fuzzy_hash = self.hasher.hash_fuzzy(text) if not self.skip_duplicates else None

        # Check for duplicates
        existing = self.db.find_by_content_hash(content_hash)

        if existing:
            # Duplicate found
            self.stats.duplicates += 1

            # Add as additional source
            self.db.insert_source({
                "canonical_id": existing["canonical_id"],
                "source_name": self.source_name,
                "collection": self.collection,
                "file_path": str(file_path),
                "format": file_path.suffix[1:],
                "download_date": datetime.now().isoformat()
            })

            self.db.log(
                operation="import",
                source=self.source_name,
                status="duplicate",
                message=f"Duplicate: {file_path.name}",
                details={"canonical_id": existing["canonical_id"]}
            )

            return

        # Generate canonical ID
        canonical_id = generate_canonical_id(content_hash)

        # Create document
        doc = {
            "canonical_id": canonical_id,
            "content_hash": content_hash,
            "file_hash": file_hash,
            "document_type": metadata.get("document_type", "email"),
            "title": metadata.get("title"),
            "date": metadata.get("date"),
            "from_person": metadata.get("from"),
            "to_persons": metadata.get("to", []),
            "subject": metadata.get("subject"),
            "ocr_quality": metadata.get("ocr_quality"),
            "has_redactions": metadata.get("has_redactions", False),
            "completeness": metadata.get("completeness", "unknown"),
            "page_count": metadata.get("page_count", 1),
            "primary_source": self.source_name,
            "selection_reason": "bulk_import"
        }

        # Insert into database
        self.db.insert_canonical_document(doc)

        # Add source
        self.db.insert_source({
            "canonical_id": canonical_id,
            "source_name": self.source_name,
            "collection": self.collection,
            "file_path": str(file_path),
            "format": file_path.suffix[1:],
            "download_date": datetime.now().isoformat()
        })

        # Log processing
        self.db.log(
            operation="import",
            source=self.source_name,
            status="success",
            message=f"Imported {file_path.name}",
            details={"canonical_id": canonical_id}
        )

        self.stats.processed += 1

    def _extract_markdown_metadata(self, text: str) -> dict:
        """
        Extract metadata from markdown frontmatter.

        Args:
            text: Markdown content

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Simple frontmatter parser
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip()
                        value = value.strip()

                        # Handle lists
                        if value.startswith("[") and value.endswith("]"):
                            value = [v.strip().strip('"\'') for v in value[1:-1].split(",")]

                        metadata[key] = value

        return metadata

    def _handle_error(self, file_path: Path, error: Exception):
        """
        Handle processing error.

        Args:
            file_path: Path to file that failed
            error: Exception that occurred
        """
        self.stats.errors += 1

        self.db.log(
            operation="import",
            source=self.source_name,
            status="error",
            message=f"Failed to import {file_path.name}",
            details={"error": str(error)}
        )

        print(f"\n✗ Error processing {file_path.name}: {error}")

    def _print_progress(self, current: int):
        """
        Print progress bar.

        Args:
            current: Current file number
        """
        percentage = (current / self.stats.total_files) * 100
        emails_per_sec = self.stats.emails_per_second

        print(
            f"\rProgress: {current}/{self.stats.total_files} "
            f"({percentage:.1f}%) | "
            f"{emails_per_sec:.1f} emails/sec | "
            f"Duplicates: {self.stats.duplicates} | "
            f"Errors: {self.stats.errors}",
            end="",
            flush=True
        )

    def _print_summary(self):
        """Print processing summary."""
        print(f"\n{'=' * 60}")
        print("PROCESSING COMPLETE")
        print(f"{'=' * 60}")

        print("\nResults:")
        print(f"  Total files: {self.stats.total_files}")
        print(f"  Processed (new): {self.stats.processed}")
        print(f"  Duplicates: {self.stats.duplicates}")
        print(f"  Errors: {self.stats.errors}")
        print(f"  Skipped: {self.stats.skipped}")

        print("\nPerformance:")
        print(f"  Elapsed time: {self.stats.elapsed:.1f} seconds")
        print(f"  Processing speed: {self.stats.emails_per_second:.1f} emails/second")
        print(f"  Duplicate rate: {self.stats.duplicate_rate * 100:.1f}%")

        # Database statistics
        db_stats = self.db.get_statistics()
        print("\nDatabase:")
        print(f"  Total documents: {db_stats['total_documents']}")
        print(f"  Total sources: {db_stats['total_sources']}")
        print(f"  Avg sources per doc: {db_stats['avg_sources_per_doc']:.2f}")

    def save_report(self, report_path: Path):
        """
        Save processing report to file.

        Args:
            report_path: Path to save report
        """
        report = [
            "=" * 60,
            "EMAIL PROCESSING REPORT",
            "=" * 60,
            "",
            f"Date: {datetime.now().isoformat()}",
            f"Source: {self.source_name}",
            f"Collection: {self.collection}",
            "",
            "RESULTS:",
            f"  Total files: {self.stats.total_files}",
            f"  Processed (new): {self.stats.processed}",
            f"  Duplicates: {self.stats.duplicates}",
            f"  Errors: {self.stats.errors}",
            "",
            "PERFORMANCE:",
            f"  Elapsed time: {self.stats.elapsed:.1f} seconds",
            f"  Processing speed: {self.stats.emails_per_second:.1f} emails/second",
            f"  Duplicate rate: {self.stats.duplicate_rate * 100:.1f}%",
            "",
        ]

        # Add database statistics
        db_stats = self.db.get_statistics()
        report.extend([
            "DATABASE:",
            f"  Total documents: {db_stats['total_documents']}",
            f"  Total sources: {db_stats['total_sources']}",
            f"  Avg sources per doc: {db_stats['avg_sources_per_doc']:.2f}",
            "",
        ])

        # Add document type breakdown
        if db_stats["documents_by_type"]:
            report.append("DOCUMENTS BY TYPE:")
            for doc_type, count in db_stats["documents_by_type"].items():
                report.append(f"  {doc_type}: {count}")

        report_path.write_text("\n".join(report))
        print(f"\nReport saved to: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bulk email processing pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Input directory containing emails"
    )

    parser.add_argument(
        "--source-name",
        default="bulk_import",
        help="Source collection name (default: bulk_import)"
    )

    parser.add_argument(
        "--collection",
        default="house_oversight",
        help="Collection identifier (default: house_oversight)"
    )

    parser.add_argument(
        "--format",
        choices=["pdf", "markdown"],
        default="markdown",
        help="Input file format (default: markdown)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for commits (default: 100)"
    )

    parser.add_argument(
        "--skip-duplicates",
        action="store_true",
        help="Skip duplicate detection (faster)"
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Save processing report to file"
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}")
        sys.exit(1)

    # Initialize database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "metadata" / "deduplication.db"

    if not db_path.exists():
        print("Error: Database not initialized. Run initialize_deduplication.py first.")
        sys.exit(1)

    db = CanonicalDatabase(db_path)

    # Create processor
    processor = EmailProcessor(
        db=db,
        source_name=args.source_name,
        collection=args.collection,
        batch_size=args.batch_size,
        skip_duplicates=args.skip_duplicates
    )

    # Process directory
    processor.process_directory(args.input_dir, args.format)

    # Save report if requested
    if args.report:
        processor.save_report(args.report)


if __name__ == "__main__":
    main()
