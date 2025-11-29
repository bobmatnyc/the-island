#!/usr/bin/env python3
"""
Document Categorization Validation Script

Validates document categorization results and identifies potential issues.
"""

import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue."""

    doc_id: str
    issue_type: str
    description: str
    path: str
    classification: str
    confidence: float


class CategoryValidator:
    """Validate document categorization results."""

    def __init__(self):
        """Initialize validator with validation rules."""

        # Expected patterns for each classification
        self.expected_patterns = {
            "email": [r"\.eml$", r"email"],
            "court_filing": [
                r"exhibit",
                r"unsealed",
                r"1320",
                r"giuffre.*maxwell",
                r"courtlistener",
            ],
            "government_document": [r"doj-", r"fbi-", r"house.*oversight", r"DOJ-OGR-"],
            "contact_directory": [r"birthday", r"black.*book"],
            "flight_log": [r"flight", r"manifest"],
        }

        # Mutually exclusive classifications (can't be both)
        self.mutually_exclusive = [
            {"email", "pdf"},  # doc_type, not classification
        ]

    def validate_document(self, doc: dict, doc_index: int) -> list[ValidationIssue]:
        """
        Validate a single document's categorization.

        Args:
            doc: Document dictionary
            doc_index: Document index for identification

        Returns:
            List of ValidationIssue objects
        """
        issues = []
        path = doc.get("canonical_path", "")
        classification = doc.get("classification", "unknown")
        confidence = doc.get("classification_confidence", 0.0)
        doc.get("doc_type", "unknown")
        source = doc.get("source", "unknown")

        doc_id = f"doc_{doc_index}"

        # Issue 1: Email files not classified as email
        if path.endswith(".eml") and classification != "email":
            issues.append(
                ValidationIssue(
                    doc_id=doc_id,
                    issue_type="email_misclassification",
                    description="Email file (.eml) not classified as email",
                    path=path,
                    classification=classification,
                    confidence=confidence,
                )
            )

        # Issue 2: Court docket numbers not classified as court_filing
        if re.search(r"1320[-\.]", path) and classification not in ["court_filing", "unknown"]:
            issues.append(
                ValidationIssue(
                    doc_id=doc_id,
                    issue_type="court_filing_misclassification",
                    description="Court docket number found but not classified as court_filing",
                    path=path,
                    classification=classification,
                    confidence=confidence,
                )
            )

        # Issue 3: Giuffre/Maxwell documents not court_filing
        if re.search(r"giuffre.*maxwell|maxwell.*giuffre", path.lower()):
            if classification not in ["court_filing", "unknown"]:
                issues.append(
                    ValidationIssue(
                        doc_id=doc_id,
                        issue_type="giuffre_maxwell_misclassification",
                        description="Giuffre/Maxwell document not classified as court_filing",
                        path=path,
                        classification=classification,
                        confidence=confidence,
                    )
                )

        # Issue 4: House Oversight documents not government_document
        if "house_oversight" in source.lower():
            if classification not in ["government_document", "unknown"]:
                issues.append(
                    ValidationIssue(
                        doc_id=doc_id,
                        issue_type="house_oversight_misclassification",
                        description="House Oversight document not classified as government_document",
                        path=path,
                        classification=classification,
                        confidence=confidence,
                    )
                )

        # Issue 5: Low confidence on non-unknown classification
        if classification != "unknown" and confidence < 0.5:
            issues.append(
                ValidationIssue(
                    doc_id=doc_id,
                    issue_type="low_confidence",
                    description=f"Low confidence ({confidence:.2f}) on classification",
                    path=path,
                    classification=classification,
                    confidence=confidence,
                )
            )

        # Issue 6: Still classified as unknown
        if classification == "unknown":
            issues.append(
                ValidationIssue(
                    doc_id=doc_id,
                    issue_type="still_unknown",
                    description="Document still classified as unknown",
                    path=path,
                    classification=classification,
                    confidence=confidence,
                )
            )

        # Issue 7: Birthday/Black book not contact_directory
        if re.search(r"birthday.*book|black.*book", path.lower()):
            if classification not in ["contact_directory", "unknown"]:
                issues.append(
                    ValidationIssue(
                        doc_id=doc_id,
                        issue_type="contact_directory_misclassification",
                        description="Birthday/Black book not classified as contact_directory",
                        path=path,
                        classification=classification,
                        confidence=confidence,
                    )
                )

        return issues


def validate_categorization(input_file: str, output_report: Optional[str] = None) -> dict:
    """
    Validate categorized document index.

    Args:
        input_file: Path to categorized document index
        output_report: Optional path to save validation report

    Returns:
        Dict with validation results
    """
    logger.info(f"Loading categorized documents from {input_file}")

    with open(input_file) as f:
        data = json.load(f)

    documents = data.get("documents", [])
    logger.info(f"Validating {len(documents)} documents...")

    validator = CategoryValidator()
    all_issues = []
    issues_by_type = defaultdict(list)

    # Validate each document
    for i, doc in enumerate(documents):
        if i % 5000 == 0 and i > 0:
            logger.info(f"Validated {i}/{len(documents)} documents...")

        issues = validator.validate_document(doc, i)

        for issue in issues:
            all_issues.append(issue)
            issues_by_type[issue.issue_type].append(issue)

    # Generate statistics
    total_issues = len(all_issues)
    issue_type_counts = {issue_type: len(issues) for issue_type, issues in issues_by_type.items()}

    # Calculate classification distribution
    classifications = Counter(doc.get("classification", "unknown") for doc in documents)
    unknown_count = classifications.get("unknown", 0)
    unknown_percentage = (unknown_count / len(documents)) * 100

    # Build validation results
    results = {
        "total_documents": len(documents),
        "total_issues": total_issues,
        "issues_by_type": issue_type_counts,
        "unknown_count": unknown_count,
        "unknown_percentage": unknown_percentage,
        "sample_issues": {},
        "classification_distribution": dict(classifications),
    }

    # Add sample issues for each type
    for issue_type, issues in issues_by_type.items():
        results["sample_issues"][issue_type] = [
            {
                "doc_id": issue.doc_id,
                "description": issue.description,
                "path": issue.path,
                "classification": issue.classification,
                "confidence": issue.confidence,
            }
            for issue in issues[:5]  # First 5 samples
        ]

    # Save report if requested
    if output_report:
        with open(output_report, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation report saved to {output_report}")

    return results


def print_validation_results(results: dict):
    """Print validation results in formatted output."""

    print("\n" + "=" * 70)
    print("DOCUMENT CATEGORIZATION VALIDATION RESULTS")
    print("=" * 70)

    print(f"\nTotal documents validated: {results['total_documents']:,}")
    print(f"Total issues found: {results['total_issues']:,}")

    # Unknown classification status
    unknown_count = results["unknown_count"]
    unknown_pct = results["unknown_percentage"]

    print("\n" + "-" * 70)
    print("UNKNOWN CLASSIFICATION STATUS")
    print("-" * 70)

    if unknown_pct < 5:
        status = "✅ EXCELLENT"
    elif unknown_pct < 10:
        status = "✓ GOOD"
    elif unknown_pct < 20:
        status = "⚠ NEEDS IMPROVEMENT"
    else:
        status = "❌ POOR"

    print(f"Unknown documents: {unknown_count:,} ({unknown_pct:.1f}%) - {status}")
    print(
        f"Classified documents: {results['total_documents'] - unknown_count:,} ({100-unknown_pct:.1f}%)"
    )

    # Issues by type
    print("\n" + "-" * 70)
    print("ISSUES BY TYPE")
    print("-" * 70)

    if results["issues_by_type"]:
        for issue_type, count in sorted(results["issues_by_type"].items(), key=lambda x: -x[1]):
            percentage = (count / results["total_documents"]) * 100
            print(f"{issue_type:40} {count:>6,} ({percentage:>5.1f}%)")
    else:
        print("✅ No issues found!")

    # Classification distribution
    print("\n" + "-" * 70)
    print("CLASSIFICATION DISTRIBUTION")
    print("-" * 70)

    for classification, count in sorted(
        results["classification_distribution"].items(), key=lambda x: -x[1]
    ):
        percentage = (count / results["total_documents"]) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{classification:25} {count:>6,} ({percentage:>5.1f}%) {bar}")

    # Sample issues
    if results["sample_issues"]:
        print("\n" + "-" * 70)
        print("SAMPLE ISSUES (First 5 per type)")
        print("-" * 70)

        for issue_type, samples in results["sample_issues"].items():
            if samples:
                print(f"\n{issue_type}:")
                for sample in samples[:3]:  # Show first 3
                    print(f"  - {sample['description']}")
                    print(f"    Path: {sample['path'][:60]}...")
                    print(
                        f"    Classification: {sample['classification']} (confidence: {sample['confidence']:.2f})"
                    )

    print("\n" + "=" * 70)


def main():
    """Main execution function."""

    # File paths
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "metadata" / "master_document_index_categorized.json"
    report_file = project_root / "data" / "metadata" / "categorization_validation_report.json"

    # Run validation
    results = validate_categorization(str(input_file), str(report_file))

    # Print results
    print_validation_results(results)

    print("\n✅ Validation report saved to:")
    print(f"   {report_file}")


if __name__ == "__main__":
    main()
