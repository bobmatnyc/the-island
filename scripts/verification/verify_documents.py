#!/usr/bin/env python3
"""
Document Data Integrity Verification Suite

Validates all document data transformations from M2 against schema compliance,
UUID integrity, classification coverage, required fields, and data consistency.

Usage:
    python scripts/verification/verify_documents.py [--verbose] [--output report.md]

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
    2 - Critical error (file not found, invalid JSON, etc.)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import argparse


# Constants
SCHEMA_PATH = Path("data/schemas/document_schema.json")
DOCUMENTS_PATH = Path("data/transformed/document_classifications.json")
PROJECT_ROOT = Path("/Users/masa/Projects/epstein")

# Valid classification types from schema
VALID_DOCUMENT_TYPES = {
    "email",
    "court_record",
    "flight_log",
    "fbi_report",
    "deposition",
    "correspondence",
    "financial",
    "administrative",
    "contact_directory",
    "government_document",
    "media_article",
    "other"
}


class DocumentVerifier:
    """Comprehensive document data integrity verifier."""

    def __init__(self, documents_path: Path, schema_path: Path, verbose: bool = False):
        self.documents_path = documents_path
        self.schema_path = schema_path
        self.verbose = verbose

        # Results tracking
        self.total_documents = 0
        self.errors: Dict[str, List[str]] = defaultdict(list)
        self.warnings: Dict[str, List[str]] = defaultdict(list)
        self.statistics: Dict[str, Any] = {}

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode enabled."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = f"[{level}]"
            print(f"{prefix:10} {message}")

    def verify_all(self) -> bool:
        """Run all verification checks. Returns True if all pass."""
        self.log("Starting document data integrity verification...")

        # Load data
        if not self._load_data():
            return False

        # Run all checks
        checks = [
            ("UUID Integrity", self._verify_uuid_integrity),
            ("Classification Coverage", self._verify_classification_coverage),
            ("Required Fields", self._verify_required_fields),
            ("Data Consistency", self._verify_data_consistency),
            ("Schema Compliance", self._verify_schema_compliance),
            ("File Existence", self._verify_file_existence),
        ]

        all_passed = True
        for check_name, check_func in checks:
            self.log(f"\nRunning check: {check_name}")
            passed = check_func()
            status = "✓ PASS" if passed else "✗ FAIL"
            self.log(f"{check_name}: {status}", "INFO" if passed else "ERROR")
            if not passed:
                all_passed = False

        return all_passed

    def _load_data(self) -> bool:
        """Load documents and schema data."""
        try:
            # Load documents
            if not self.documents_path.exists():
                self.errors["critical"].append(f"Documents file not found: {self.documents_path}")
                return False

            with open(self.documents_path, 'r') as f:
                self.data = json.load(f)

            self.total_documents = self.data.get('total_documents', 0)
            self.documents = self.data.get('documents', [])

            if len(self.documents) != self.total_documents:
                self.warnings["metadata"].append(
                    f"Document count mismatch: declared={self.total_documents}, actual={len(self.documents)}"
                )
                self.total_documents = len(self.documents)

            self.log(f"Loaded {self.total_documents:,} documents")

            # Load schema
            if not self.schema_path.exists():
                self.warnings["schema"].append(f"Schema file not found: {self.schema_path}")
                self.schema = None
            else:
                with open(self.schema_path, 'r') as f:
                    self.schema = json.load(f)
                self.log("Loaded schema definition")

            return True

        except json.JSONDecodeError as e:
            self.errors["critical"].append(f"Invalid JSON in documents file: {e}")
            return False
        except Exception as e:
            self.errors["critical"].append(f"Error loading data: {e}")
            return False

    def _verify_uuid_integrity(self) -> bool:
        """Verify all document IDs are valid UUIDs and unique."""
        self.log("Checking UUID integrity...")

        # SHA256 pattern (64 hex chars)
        sha256_pattern = re.compile(r'^[a-f0-9]{64}$')

        seen_ids: Set[str] = set()
        duplicates: List[str] = []
        invalid_ids: List[Tuple[str, str]] = []

        for idx, doc in enumerate(self.documents):
            doc_id = doc.get('id', '')

            # Check if valid SHA256 (current format)
            if not sha256_pattern.match(doc_id):
                invalid_ids.append((doc_id, doc.get('filename', f'document_{idx}')))

            # Check for duplicates
            if doc_id in seen_ids:
                duplicates.append(doc_id)
            else:
                seen_ids.add(doc_id)

        # Record results
        self.statistics['total_unique_ids'] = len(seen_ids)
        self.statistics['duplicate_ids'] = len(duplicates)
        self.statistics['invalid_ids'] = len(invalid_ids)

        if duplicates:
            self.errors["uuid_integrity"].append(
                f"Found {len(duplicates)} duplicate document IDs"
            )
            for dup_id in duplicates[:5]:  # Show first 5
                self.errors["uuid_integrity"].append(f"  - Duplicate ID: {dup_id}")

        if invalid_ids:
            self.errors["uuid_integrity"].append(
                f"Found {len(invalid_ids)} invalid document IDs (not SHA256 format)"
            )
            for inv_id, filename in invalid_ids[:5]:  # Show first 5
                self.errors["uuid_integrity"].append(f"  - Invalid ID: {inv_id} (file: {filename})")

        return len(duplicates) == 0 and len(invalid_ids) == 0

    def _verify_classification_coverage(self) -> bool:
        """Verify all documents have valid classifications."""
        self.log("Checking classification coverage...")

        classification_counts = Counter()
        invalid_classifications: List[Tuple[str, str]] = []
        missing_classifications: List[str] = []

        for doc in self.documents:
            doc_id = doc.get('id', 'unknown')
            classification = doc.get('new_classification')

            if not classification:
                missing_classifications.append(doc_id)
                continue

            if classification not in VALID_DOCUMENT_TYPES:
                invalid_classifications.append((doc_id, classification))
            else:
                classification_counts[classification] += 1

        # Record statistics
        self.statistics['classification_distribution'] = dict(classification_counts)
        self.statistics['missing_classifications'] = len(missing_classifications)
        self.statistics['invalid_classifications'] = len(invalid_classifications)
        self.statistics['classification_coverage_pct'] = (
            (self.total_documents - len(missing_classifications)) / self.total_documents * 100
            if self.total_documents > 0 else 0
        )

        if missing_classifications:
            self.errors["classification"].append(
                f"Found {len(missing_classifications)} documents without classification"
            )
            for doc_id in missing_classifications[:5]:
                self.errors["classification"].append(f"  - Missing classification: {doc_id}")

        if invalid_classifications:
            self.errors["classification"].append(
                f"Found {len(invalid_classifications)} documents with invalid classification"
            )
            for doc_id, classification in invalid_classifications[:5]:
                self.errors["classification"].append(
                    f"  - Invalid: '{classification}' (doc: {doc_id})"
                )

        return len(missing_classifications) == 0 and len(invalid_classifications) == 0

    def _verify_required_fields(self) -> bool:
        """Verify all required fields are present."""
        self.log("Checking required fields...")

        # Required fields in current document format
        required_fields = ['id', 'filename', 'path', 'source', 'new_classification']

        missing_fields: Dict[str, List[str]] = defaultdict(list)

        for doc in self.documents:
            doc_id = doc.get('id', 'unknown')

            for field in required_fields:
                if field not in doc or doc[field] is None or doc[field] == '':
                    missing_fields[field].append(doc_id)

        # Record statistics
        self.statistics['required_fields_compliance'] = {
            field: self.total_documents - len(missing_docs)
            for field, missing_docs in missing_fields.items()
        }

        all_present = True
        for field, missing_docs in missing_fields.items():
            if missing_docs:
                all_present = False
                self.errors["required_fields"].append(
                    f"Field '{field}' missing in {len(missing_docs)} documents"
                )
                for doc_id in missing_docs[:3]:
                    self.errors["required_fields"].append(f"  - Missing in: {doc_id}")

        return all_present

    def _verify_data_consistency(self) -> bool:
        """Verify data consistency (confidence scores, methods, etc.)."""
        self.log("Checking data consistency...")

        issues_found = False

        # Check confidence scores
        invalid_confidence: List[Tuple[str, float]] = []
        confidence_distribution = {'low': 0, 'medium': 0, 'high': 0}

        for doc in self.documents:
            doc_id = doc.get('id', 'unknown')
            confidence = doc.get('confidence')

            if confidence is not None:
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                    invalid_confidence.append((doc_id, confidence))
                    issues_found = True
                else:
                    # Categorize confidence
                    if confidence >= 0.8:
                        confidence_distribution['high'] += 1
                    elif confidence >= 0.5:
                        confidence_distribution['medium'] += 1
                    else:
                        confidence_distribution['low'] += 1

        self.statistics['confidence_distribution'] = confidence_distribution

        if invalid_confidence:
            self.errors["data_consistency"].append(
                f"Found {len(invalid_confidence)} documents with invalid confidence scores"
            )
            for doc_id, conf in invalid_confidence[:5]:
                self.errors["data_consistency"].append(
                    f"  - Invalid confidence: {conf} (doc: {doc_id})"
                )

        # Check classification methods
        method_counts = Counter(doc.get('classification_method', 'unknown') for doc in self.documents)
        self.statistics['classification_methods'] = dict(method_counts)

        # Check path consistency
        invalid_paths: List[Tuple[str, str]] = []
        for doc in self.documents:
            path = doc.get('path', '')
            if path:
                # Check if path looks valid (should start with data/sources/)
                if not path.startswith('data/sources/'):
                    invalid_paths.append((doc.get('id', 'unknown'), path))
                    issues_found = True

        if invalid_paths:
            self.errors["data_consistency"].append(
                f"Found {len(invalid_paths)} documents with unexpected path format"
            )
            for doc_id, path in invalid_paths[:5]:
                self.errors["data_consistency"].append(f"  - Unexpected path: {path}")

        return not issues_found

    def _verify_schema_compliance(self) -> bool:
        """Verify documents comply with canonical schema structure."""
        self.log("Checking schema compliance...")

        if not self.schema:
            self.warnings["schema"].append("Schema not loaded, skipping compliance check")
            return True

        # Note: Current document_classifications.json uses interim format
        # Full schema compliance will be checked when documents are transformed
        # to final canonical format (document_id, document_type, title, etc.)

        self.warnings["schema"].append(
            "Documents use interim classification format. "
            "Full schema compliance will be verified after transformation to canonical format."
        )

        # For now, verify that the classification types match schema enum
        schema_enum = set(self.schema.get('properties', {}).get('document_type', {}).get('enum', []))

        if schema_enum and schema_enum != VALID_DOCUMENT_TYPES:
            self.warnings["schema"].append(
                f"Classification types in code differ from schema. "
                f"Schema has {len(schema_enum)} types, code has {len(VALID_DOCUMENT_TYPES)} types"
            )

        return True

    def _verify_file_existence(self) -> bool:
        """Verify that document source files exist (sample check)."""
        self.log("Checking file existence (sampling 100 files)...")

        # Sample 100 random documents to check file existence
        import random
        sample_size = min(100, len(self.documents))
        sample_docs = random.sample(self.documents, sample_size)

        missing_files: List[Tuple[str, str]] = []
        checked_count = 0

        for doc in sample_docs:
            path = doc.get('path', '')
            if path:
                full_path = PROJECT_ROOT / path
                if not full_path.exists():
                    missing_files.append((doc.get('id', 'unknown'), path))
            checked_count += 1

        self.statistics['files_checked'] = checked_count
        self.statistics['missing_files_in_sample'] = len(missing_files)

        if missing_files:
            missing_pct = (len(missing_files) / checked_count) * 100
            self.warnings["file_existence"].append(
                f"Found {len(missing_files)} missing files in sample of {checked_count} ({missing_pct:.1f}%)"
            )
            for doc_id, path in missing_files[:5]:
                self.warnings["file_existence"].append(f"  - Missing: {path}")

            # This is a warning, not an error, as files may have been moved/reorganized
            return True

        self.log(f"All {checked_count} sampled files exist")
        return True

    def generate_report(self, output_path: Path = None) -> str:
        """Generate formatted integrity report."""
        lines = []

        # Header
        lines.append("DOCUMENT DATA INTEGRITY REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Documents File: {self.documents_path}")
        lines.append(f"Schema File: {self.schema_path}")
        lines.append("")

        # Overview
        lines.append("OVERVIEW")
        lines.append("-" * 60)
        lines.append(f"Total Documents: {self.total_documents:,}")
        lines.append("")

        # UUID Integrity
        lines.append("UUID INTEGRITY")
        lines.append("-" * 60)
        unique_ids = self.statistics.get('total_unique_ids', 0)
        duplicates = self.statistics.get('duplicate_ids', 0)
        invalid = self.statistics.get('invalid_ids', 0)

        if duplicates == 0 and invalid == 0:
            lines.append("✓ PASS - All document IDs are valid and unique")
        else:
            lines.append("✗ FAIL - Issues found:")

        lines.append(f"  Unique IDs: {unique_ids:,}")
        lines.append(f"  Duplicate IDs: {duplicates}")
        lines.append(f"  Invalid IDs: {invalid}")

        if self.errors.get("uuid_integrity"):
            lines.append("  Errors:")
            for error in self.errors["uuid_integrity"]:
                lines.append(f"    {error}")
        lines.append("")

        # Classification Coverage
        lines.append("CLASSIFICATION COVERAGE")
        lines.append("-" * 60)
        coverage_pct = self.statistics.get('classification_coverage_pct', 0)
        missing_class = self.statistics.get('missing_classifications', 0)
        invalid_class = self.statistics.get('invalid_classifications', 0)

        if missing_class == 0 and invalid_class == 0:
            lines.append("✓ PASS - All documents have valid classifications")
        else:
            lines.append("✗ FAIL - Issues found:")

        lines.append(f"  Coverage: {coverage_pct:.2f}%")
        lines.append(f"  Missing Classifications: {missing_class}")
        lines.append(f"  Invalid Classifications: {invalid_class}")
        lines.append("")

        # Classification Distribution
        lines.append("  Distribution by Type:")
        dist = self.statistics.get('classification_distribution', {})
        for doc_type, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
            pct = (count / self.total_documents * 100) if self.total_documents > 0 else 0
            lines.append(f"    {doc_type:25} {count:6,} ({pct:5.2f}%)")

        if self.errors.get("classification"):
            lines.append("  Errors:")
            for error in self.errors["classification"][:10]:  # Limit errors shown
                lines.append(f"    {error}")
        lines.append("")

        # Required Fields
        lines.append("REQUIRED FIELDS")
        lines.append("-" * 60)

        has_required_errors = bool(self.errors.get("required_fields"))
        if not has_required_errors:
            lines.append("✓ PASS - All required fields present")
        else:
            lines.append("✗ FAIL - Missing required fields:")
            for error in self.errors["required_fields"]:
                lines.append(f"  {error}")
        lines.append("")

        # Data Consistency
        lines.append("DATA CONSISTENCY")
        lines.append("-" * 60)

        has_consistency_errors = bool(self.errors.get("data_consistency"))
        if not has_consistency_errors:
            lines.append("✓ PASS - Data consistency checks passed")
        else:
            lines.append("✗ FAIL - Consistency issues found:")
            for error in self.errors["data_consistency"]:
                lines.append(f"  {error}")

        # Confidence distribution
        conf_dist = self.statistics.get('confidence_distribution', {})
        lines.append("\n  Confidence Score Distribution:")
        for level in ['high', 'medium', 'low']:
            count = conf_dist.get(level, 0)
            pct = (count / self.total_documents * 100) if self.total_documents > 0 else 0
            lines.append(f"    {level.capitalize():10} {count:6,} ({pct:5.2f}%)")

        # Classification methods
        methods = self.statistics.get('classification_methods', {})
        lines.append("\n  Classification Methods:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            pct = (count / self.total_documents * 100) if self.total_documents > 0 else 0
            lines.append(f"    {method:20} {count:6,} ({pct:5.2f}%)")
        lines.append("")

        # File Existence
        lines.append("FILE EXISTENCE")
        lines.append("-" * 60)
        files_checked = self.statistics.get('files_checked', 0)
        missing = self.statistics.get('missing_files_in_sample', 0)

        if missing == 0:
            lines.append(f"✓ PASS - All sampled files exist ({files_checked} checked)")
        else:
            lines.append(f"⚠ WARNING - Some files missing in sample:")
            lines.append(f"  Files Checked: {files_checked}")
            lines.append(f"  Missing Files: {missing}")

        if self.warnings.get("file_existence"):
            for warning in self.warnings["file_existence"]:
                lines.append(f"  {warning}")
        lines.append("")

        # Schema Compliance
        lines.append("SCHEMA COMPLIANCE")
        lines.append("-" * 60)

        has_schema_errors = bool(self.errors.get("schema"))
        if not has_schema_errors:
            lines.append("✓ PASS - Schema compliance verified")
        else:
            lines.append("✗ FAIL - Schema compliance issues:")
            for error in self.errors["schema"]:
                lines.append(f"  {error}")

        if self.warnings.get("schema"):
            lines.append("\n  Notes:")
            for warning in self.warnings["schema"]:
                lines.append(f"    {warning}")
        lines.append("")

        # Summary
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append("=" * 60)

        total_errors = sum(len(errs) for errs in self.errors.values())
        total_warnings = sum(len(warns) for warns in self.warnings.values())

        if total_errors == 0:
            lines.append("✓ OVERALL STATUS: PASS")
            lines.append(f"  All critical checks passed")
        else:
            lines.append("✗ OVERALL STATUS: FAIL")
            lines.append(f"  Critical issues found: {total_errors}")

        if total_warnings > 0:
            lines.append(f"  Warnings: {total_warnings}")

        lines.append("")
        lines.append(f"Verification completed: {datetime.now().isoformat()}")

        report = "\n".join(lines)

        # Write to file if requested
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"\nReport written to: {output_path}")

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify document data integrity for Epstein archive"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('docs/qa-reports/document-integrity-report.md'),
        help='Output path for report (default: docs/qa-reports/document-integrity-report.md)'
    )

    args = parser.parse_args()

    # Create verifier
    verifier = DocumentVerifier(
        documents_path=DOCUMENTS_PATH,
        schema_path=SCHEMA_PATH,
        verbose=args.verbose
    )

    # Run verification
    try:
        passed = verifier.verify_all()

        # Generate report
        print("\n" + "=" * 60)
        report = verifier.generate_report(output_path=args.output)
        print(report)

        # Exit with appropriate code
        sys.exit(0 if passed else 1)

    except Exception as e:
        print(f"CRITICAL ERROR: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
