#!/usr/bin/env python3
"""
Document Categorization Script

Categorizes documents based on filename patterns and source directories.
Reduces "unknown" classifications by analyzing document metadata.
"""

import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CategorizationStats:
    """Statistics for categorization results."""

    total_documents: int
    recategorized: int
    by_classification: dict[str, int]
    by_source: dict[str, int]
    by_doc_type: dict[str, int]


class DocumentCategorizer:
    """Categorize documents based on filename patterns and sources."""

    def __init__(self):
        """Initialize categorizer with pattern definitions."""

        # Patterns for different document classifications
        self.patterns = {
            "court_filing": [
                r"1320[-\.]",  # Court docket numbers
                r"exhibit",
                r"deposition",
                r"declaration",
                r"affidavit",
                r"complaint",
                r"motion",
                r"filing",
                r"unsealed",
                r"gov\.uscourts",
                r"courtlistener",
                r"giuffre.*maxwell",
                r"maxwell.*giuffre",
            ],
            "email": [
                r"\.eml$",
                r"email",
                r"message",
                r"correspondence",
            ],
            "financial": [
                r"invoice",
                r"receipt",
                r"bank.*statement",
                r"financial.*record",
                r"transaction",
                r"payment",
                r"wire.*transfer",
                r"account",
            ],
            "flight_log": [
                r"flight.*log",
                r"manifest",
                r"passenger.*list",
                r"aviation.*record",
                r"trip.*log",
            ],
            "contact_directory": [
                r"black.*book",
                r"birthday.*book",
                r"contact.*info",
                r"address.*book",
                r"phone.*book",
            ],
            "government_document": [
                r"doj[-_]",
                r"fbi[-_]",
                r"house.*oversight",
                r"congressional",
                r"gov\.",
                r"DOJ-OGR-",
                r"government",
            ],
            "media_article": [
                r"404media",
                r"article",
                r"news",
                r"report",
            ],
        }

        # Source-based classification overrides
        # Note: Court docket patterns (1320-*, etc.) take precedence in categorize()
        self.source_classifications = {
            "giuffre_maxwell": "court_filing",
            "courtlistener_giuffre_maxwell": "court_filing",
            "courtlistener": "court_filing",
            "house_oversight_nov2025": "government_document",
            "house_oversight_sept2024": "government_document",
            "house_oversight_sept2025": "government_document",
            "fbi_vault": "government_document",
            "doj_official": "government_document",
            "raw_entities": "contact_directory",  # Birthday book
            # 404media removed - let court docket patterns classify these
        }

    def categorize(
        self, path: str, source: Optional[str] = None, existing_classification: Optional[str] = None
    ) -> tuple[str, str, float]:
        """
        Categorize document based on path and source.

        Args:
            path: Document file path
            source: Source directory name
            existing_classification: Current classification (if any)

        Returns:
            Tuple of (doc_type, classification, confidence)
        """
        if not path:
            return ("unknown", existing_classification or "unknown", 0.0)

        lower_path = path.lower()
        filename = Path(path).name.lower()

        # Determine doc_type from extension
        if path.endswith(".eml"):
            doc_type = "email"
        elif path.endswith(".pdf"):
            doc_type = "pdf"
        elif path.endswith((".txt", ".text")):
            doc_type = "text"
        else:
            doc_type = "unknown"

        # Determine classification
        classification = "unknown"
        confidence = 0.0

        # 1. Check for high-priority patterns (court dockets, etc.) - HIGHEST PRIORITY
        high_priority_patterns = {
            "court_filing": [r"1320[-\.]", r"exhibit", r"unsealed", r"gov\.uscourts"],
        }

        for category, patterns in high_priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, lower_path, re.IGNORECASE):
                    classification = category
                    confidence = 0.95
                    break
            if classification != "unknown":
                break

        # 2. Check source-based classification (medium priority)
        if classification == "unknown" and source and source in self.source_classifications:
            classification = self.source_classifications[source]
            confidence = 0.9

        # 3. Check pattern-based classification
        if classification == "unknown":
            for category, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, lower_path, re.IGNORECASE):
                        classification = category
                        confidence = 0.7
                        break
                if classification != "unknown":
                    break

        # 3. Special filename-based rules
        if classification == "unknown":
            # Birthday/Black book
            if "birthday" in filename or "black" in filename:
                classification = "contact_directory"
                confidence = 0.8
            # Flight logs
            elif "flight" in filename or "manifest" in filename:
                classification = "flight_log"
                confidence = 0.8
            # DOJ documents
            elif filename.startswith("doj-"):
                classification = "government_document"
                confidence = 0.8

        # 4. Keep existing classification if we have no better match
        if classification == "unknown" and existing_classification:
            if existing_classification not in {"unknown", "administrative"}:
                classification = existing_classification
                confidence = 0.5

        # 5. Default to administrative if still unknown
        if classification == "unknown":
            classification = "administrative"
            confidence = 0.3

        return (doc_type, classification, confidence)

    def extract_source_from_path(self, path: str) -> str:
        """Extract source directory from path."""
        if not path:
            return "unknown"

        parts = Path(path).parts
        if len(parts) >= 3 and parts[0] == "data" and parts[1] == "sources":
            return parts[2]

        return "unknown"


def categorize_master_index(
    input_file: str, output_file: str, backup: bool = True
) -> CategorizationStats:
    """
    Categorize all documents in master index.

    Args:
        input_file: Path to master_document_index.json
        output_file: Path to save categorized index
        backup: Whether to create backup of input file

    Returns:
        CategorizationStats with results
    """
    logger.info(f"Loading documents from {input_file}")

    # Load master document index
    with open(input_file) as f:
        data = json.load(f)

    documents = data.get("documents", [])
    logger.info(f"Found {len(documents)} documents to categorize")

    # Create backup if requested
    if backup:
        backup_path = f"{input_file}.backup"
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Created backup at {backup_path}")

    # Initialize categorizer and stats
    categorizer = DocumentCategorizer()
    recategorized = 0
    by_classification = Counter()
    by_source = Counter()
    by_doc_type = Counter()
    confidence_scores = []

    # Categorize each document
    for i, doc in enumerate(documents):
        if i % 5000 == 0 and i > 0:
            logger.info(f"Processed {i}/{len(documents)} documents...")

        path = doc.get("canonical_path", "")
        source = categorizer.extract_source_from_path(path)
        existing_classification = doc.get("classification", "unknown")

        # Get new categorization
        doc_type, classification, confidence = categorizer.categorize(
            path, source, existing_classification
        )

        # Update document
        old_classification = doc.get("classification", "unknown")
        if classification != old_classification:
            recategorized += 1

        doc["classification"] = classification
        doc["classification_confidence"] = confidence
        doc["source"] = source
        doc["doc_type"] = doc_type

        # Update stats
        by_classification[classification] += 1
        by_source[source] += 1
        by_doc_type[doc_type] += 1
        confidence_scores.append(confidence)

    # Update metadata
    data["classification_stats"] = {
        "total_documents": len(documents),
        "recategorized": recategorized,
        "average_confidence": sum(confidence_scores) / len(confidence_scores),
        "by_classification": dict(by_classification),
        "by_source": dict(by_source),
        "by_doc_type": dict(by_doc_type),
    }

    # Save categorized index
    logger.info(f"Saving categorized index to {output_file}")
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    # Create stats object
    stats = CategorizationStats(
        total_documents=len(documents),
        recategorized=recategorized,
        by_classification=dict(by_classification),
        by_source=dict(by_source),
        by_doc_type=dict(by_doc_type),
    )

    return stats


def print_statistics(stats: CategorizationStats):
    """Print categorization statistics in formatted output."""

    print("\n" + "=" * 70)
    print("DOCUMENT CATEGORIZATION COMPLETE")
    print("=" * 70)

    print(f"\nTotal documents: {stats.total_documents:,}")
    print(f"Documents recategorized: {stats.recategorized:,}")
    print(f"Recategorization rate: {(stats.recategorized/stats.total_documents)*100:.1f}%")

    print("\n" + "-" * 70)
    print("CLASSIFICATION BREAKDOWN")
    print("-" * 70)

    sorted_classifications = sorted(stats.by_classification.items(), key=lambda x: -x[1])

    for classification, count in sorted_classifications:
        percentage = (count / stats.total_documents) * 100
        bar_length = int(percentage / 2)  # Scale to fit display
        bar = "█" * bar_length
        print(f"{classification:25} {count:>6,} ({percentage:>5.1f}%) {bar}")

    print("\n" + "-" * 70)
    print("SOURCE BREAKDOWN (Top 10)")
    print("-" * 70)

    sorted_sources = sorted(stats.by_source.items(), key=lambda x: -x[1])[:10]

    for source, count in sorted_sources:
        percentage = (count / stats.total_documents) * 100
        print(f"{source:35} {count:>6,} ({percentage:>5.1f}%)")

    print("\n" + "-" * 70)
    print("DOCUMENT TYPE BREAKDOWN")
    print("-" * 70)

    for doc_type, count in sorted(stats.by_doc_type.items(), key=lambda x: -x[1]):
        percentage = (count / stats.total_documents) * 100
        print(f"{doc_type:15} {count:>6,} ({percentage:>5.1f}%)")

    print("\n" + "=" * 70)


def main():
    """Main execution function."""

    # File paths
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "metadata" / "master_document_index.json"
    output_file = project_root / "data" / "metadata" / "master_document_index_categorized.json"

    # Run categorization
    stats = categorize_master_index(str(input_file), str(output_file), backup=True)

    # Print results
    print_statistics(stats)

    print("\n✅ Categorized document index saved to:")
    print(f"   {output_file}")
    print("\n✅ Backup saved to:")
    print(f"   {input_file}.backup")


if __name__ == "__main__":
    main()
